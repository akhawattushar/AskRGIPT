from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from config import config

class VectorStore:
    def __init__(self):
        print("🧠 Initializing Vector Store...")
        
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        print(f"   ✅ Loaded embedding model: {config.EMBEDDING_MODEL}")
        
        self.client = chromadb.PersistentClient(
            path=config.VECTOR_DB_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name="rgipt_documents",
            metadata={"description": "RGIPT official documents"}
        )
        print(f"   ✅ ChromaDB ready ({self.collection.count()} docs)")
    
    def add_documents(self, chunks, metadata):
        print(f"\n📥 Adding {len(chunks)} chunks to vector store...")
        
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            batch_metadata = metadata[i:i+batch_size]
            
            embeddings = self.embedding_model.encode(batch_chunks).tolist()
            ids = [f"doc_{i+j}" for j in range(len(batch_chunks))]
            
            self.collection.add(
                embeddings=embeddings,
                documents=batch_chunks,
                metadatas=batch_metadata,
                ids=ids
            )
            
            print(f"   Batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
        
        print(f"✅ Vector store updated! Total: {self.collection.count()} docs")
    
    def search(self, query, top_k=5):
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return results

if __name__ == "__main__":
    from document_processor import DocumentProcessor
    
    processor = DocumentProcessor()
    chunks, metadata = processor.process_all_documents()
    
    vector_store = VectorStore()
    vector_store.add_documents(chunks, metadata)
    
    print("\n🔍 Testing search:")
    query = "library rules"
    results = vector_store.search(query, top_k=3)
    print(f"\nQuery: {query}")
    print(f"\nTop result:\n{results['documents'][0][0][:200]}...")
