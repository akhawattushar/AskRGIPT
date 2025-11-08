"""
Enhanced Vector Store with hybrid search, re-ranking, and metadata filtering.
Supports multiple embedding models and advanced retrieval strategies.
"""
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional, Tuple
import numpy as np
from config import config

# Try to import re-ranking models
try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    print("⚠️ CrossEncoder not available. Re-ranking will be disabled.")


class VectorStore:
    def __init__(self):
        """Initialize enhanced vector store."""
        print("🧠 Initializing Enhanced Vector Store...")
        
        # Load embedding model
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        print(f"   ✅ Loaded embedding model: {config.EMBEDDING_MODEL}")
        
        # Initialize re-ranker if available
        self.reranker = None
        if RERANKER_AVAILABLE:
            try:
                # Use a cross-encoder for re-ranking (better quality than bi-encoder)
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                print("   ✅ Re-ranker initialized")
            except Exception as e:
                print(f"   ⚠️ Re-ranker initialization failed: {e}")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=config.VECTOR_DB_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="rgipt_documents",
            metadata={"description": "RGIPT official documents"},
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=config.EMBEDDING_MODEL
            )
        )
        
        print(f"   ✅ ChromaDB ready ({self.collection.count()} docs)")
    
    def add_documents(self, chunks: List[str], metadata: List[Dict], 
                     batch_size: int = 100, clear_existing: bool = False):
        """
        Add documents to vector store.
        
        Args:
            chunks: List of text chunks
            metadata: List of metadata dictionaries
            batch_size: Batch size for processing
            clear_existing: Whether to clear existing documents first
        """
        if not chunks or not metadata:
            print("⚠️ No chunks or metadata provided")
            return
        
        if len(chunks) != len(metadata):
            raise ValueError("Chunks and metadata must have the same length")
        
        print(f"\n📥 Adding {len(chunks)} chunks to vector store...")
        
        # Clear existing if requested
        if clear_existing:
            print("   🗑️  Clearing existing documents...")
            try:
                self.client.delete_collection("rgipt_documents")
                self.collection = self.client.create_collection(
                    name="rgipt_documents",
                    metadata={"description": "RGIPT official documents"},
                    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=config.EMBEDDING_MODEL
                    )
                )
            except:
                pass
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            batch_metadata = metadata[i:i+batch_size]
            
            # Generate IDs
            ids = [f"doc_{i+j}" for j in range(len(batch_chunks))]
            
            # Add to collection
            self.collection.add(
                documents=batch_chunks,
                metadatas=batch_metadata,
                ids=ids
            )
            
            print(f"   Batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} added")
        
        print(f"✅ Vector store updated! Total: {self.collection.count()} docs")
    
    def search(self, query: str, top_k: int = None, 
              category_filter: Optional[str] = None,
              similarity_threshold: Optional[float] = None,
              use_reranking: bool = True) -> Dict:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            category_filter: Filter by category (optional)
            similarity_threshold: Minimum similarity score (0-1)
            use_reranking: Whether to use re-ranking
            
        Returns:
            Dictionary with search results
        """
        if top_k is None:
            top_k = config.TOP_K_RESULTS
        
        # Build where clause for filtering
        where = None
        if category_filter:
            where = {"category": category_filter}
        
        # Initial retrieval (get more results if re-ranking)
        n_results = top_k * 2 if use_reranking and self.reranker else top_k
        
        # Perform search
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        if not results['documents'] or not results['documents'][0]:
            return {
                'documents': [],
                'metadatas': [],
                'distances': [],
                'ids': []
            }
        
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        ids = results['ids'][0]
        
        # Re-rank if enabled
        if use_reranking and self.reranker and len(documents) > top_k:
            # Create query-document pairs for re-ranking
            pairs = [[query, doc] for doc in documents]
            
            # Get re-ranking scores
            rerank_scores = self.reranker.predict(pairs)
            
            # Sort by re-ranking scores
            sorted_indices = np.argsort(rerank_scores)[::-1]  # Descending order
            
            # Apply re-ranking
            documents = [documents[i] for i in sorted_indices[:top_k]]
            metadatas = [metadatas[i] for i in sorted_indices[:top_k]]
            distances = [distances[i] for i in sorted_indices[:top_k]]
            ids = [ids[i] for i in sorted_indices[:top_k]]
        else:
            # Take top_k results
            documents = documents[:top_k]
            metadatas = metadatas[:top_k]
            distances = distances[:top_k]
            ids = ids[:top_k]
        
        # Apply similarity threshold if specified
        if similarity_threshold is not None:
            # Convert distances to similarities (ChromaDB uses cosine distance)
            similarities = [1 - dist for dist in distances]
            filtered_results = [
                (doc, meta, dist, doc_id, sim)
                for doc, meta, dist, doc_id, sim in zip(documents, metadatas, distances, ids, similarities)
                if sim >= similarity_threshold
            ]
            
            if filtered_results:
                documents, metadatas, distances, ids, _ = zip(*filtered_results)
                documents, metadatas, distances, ids = list(documents), list(metadatas), list(distances), list(ids)
            else:
                documents, metadatas, distances, ids = [], [], [], []
        
        return {
            'documents': documents,
            'metadatas': metadatas,
            'distances': distances,
            'ids': ids
        }
    
    def hybrid_search(self, query: str, top_k: int = None,
                     category_filter: Optional[str] = None,
                     keyword_weight: float = 0.3) -> Dict:
        """
        Hybrid search combining semantic and keyword matching.
        
        Args:
            query: Search query
            top_k: Number of results to return
            category_filter: Filter by category (optional)
            keyword_weight: Weight for keyword matching (0-1)
            
        Returns:
            Dictionary with search results
        """
        if top_k is None:
            top_k = config.TOP_K_RESULTS
        
        # Semantic search
        semantic_results = self.search(
            query, 
            top_k=top_k * 2, 
            category_filter=category_filter,
            use_reranking=False
        )
        
        # Simple keyword matching (ChromaDB's where clause can help)
        # For better keyword search, would need BM25 integration
        # For now, we'll use semantic search with keyword boosting via re-ranking
        
        # If we have a re-ranker, it naturally combines semantic and keyword signals
        if self.reranker:
            # Re-rank with keyword awareness
            final_results = self.search(
                query,
                top_k=top_k,
                category_filter=category_filter,
                use_reranking=True
            )
            return final_results
        
        return semantic_results
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        count = self.collection.count()
        
        # Get sample metadata to understand structure
        sample = self.collection.peek(limit=min(10, count))
        
        categories = set()
        if sample['metadatas']:
            for meta in sample['metadatas']:
                if 'category' in meta:
                    categories.add(meta['category'])
        
        return {
            'total_documents': count,
            'categories': list(categories),
            'embedding_model': config.EMBEDDING_MODEL,
            'reranker_available': self.reranker is not None
        }
    
    def delete_documents(self, ids: List[str]):
        """Delete documents by IDs."""
        if ids:
            self.collection.delete(ids=ids)
            print(f"✅ Deleted {len(ids)} documents")
    
    def update_document(self, doc_id: str, chunk: str, metadata: Dict):
        """Update a single document."""
        self.collection.update(
            ids=[doc_id],
            documents=[chunk],
            metadatas=[metadata]
        )
        print(f"✅ Updated document {doc_id}")


if __name__ == "__main__":
    from document_processor import DocumentProcessor
    
    # Test vector store
    processor = DocumentProcessor()
    chunks, metadata = processor.process_all_documents()
    
    if chunks:
        vector_store = VectorStore()
        vector_store.add_documents(chunks, metadata, clear_existing=True)
        
        print("\n🔍 Testing search:")
        query = "library rules"
        results = vector_store.search(query, top_k=3)
        
        print(f"\nQuery: {query}")
        if results['documents']:
            print(f"\nTop result:\n{results['documents'][0][:200]}...")
            print(f"\nMetadata: {results['metadatas'][0]}")
        
        # Get stats
        stats = vector_store.get_collection_stats()
        print(f"\n📊 Collection stats: {stats}")
