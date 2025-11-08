"""
RAG Engine
Core RAG pipeline with LLM integration, citation extraction, and hallucination prevention.
"""
from typing import List, Dict, Optional, Tuple
import openai
from config import config
from vector_store import VectorStore
from citation_manager import CitationManager


class RAGEngine:
    """RAG Engine for question answering with citations."""
    
    def __init__(self):
        """Initialize RAG engine."""
        self.vector_store = VectorStore()
        self.citation_manager = CitationManager()
        
        # Initialize OpenAI client
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        
        openai.api_key = config.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        
        # System prompt for context-limited responses
        self.system_prompt = """You are a helpful assistant for RGIPT (Rajiv Gandhi Institute of Petroleum Technology).
Your role is to answer questions based ONLY on the provided context from official RGIPT documents.
You must:
1. Answer questions using ONLY the information provided in the context
2. Include citations using the format: "According to [Document Name]..."
3. If the context doesn't contain enough information, say "I couldn't find an authoritative answer in the available documents."
4. Be precise and accurate
5. Do not make up information or use knowledge outside the provided context"""
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess query (expand abbreviations, handle RGIPT-specific terms).
        
        Args:
            query: User query
            
        Returns:
            Preprocessed query
        """
        # Expand common abbreviations
        expansions = {
            "RGIPT": "Rajiv Gandhi Institute of Petroleum Technology",
            "fee": "fee structure fees payment",
            "policy": "policy policies regulation regulations",
        }
        
        preprocessed = query
        for abbrev, expansion in expansions.items():
            if abbrev.lower() in query.lower():
                preprocessed += f" {expansion}"
        
        return preprocessed
    
    def _build_context(self, results: Dict, max_length: int = 3000) -> Tuple[str, List[Dict]]:
        """
        Build context string from search results.
        
        Args:
            results: Search results from vector store
            max_length: Maximum context length in characters
            
        Returns:
            Tuple of (context_string, citations)
        """
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        
        if not documents:
            return "", []
        
        # Create citations
        citations = self.citation_manager.create_citation_dict(results)
        
        # Build context
        context_parts = []
        current_length = 0
        
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            # Add document marker
            source = meta.get("source", "Unknown")
            page = self.citation_manager.extract_page_number(doc, meta)
            
            doc_marker = f"\n[Document: {source}"
            if page:
                doc_marker += f", Page {page}"
            doc_marker += "]\n"
            
            doc_text = doc_marker + doc
            
            if current_length + len(doc_text) > max_length:
                # Try to fit at least a portion
                remaining = max_length - current_length - len(doc_marker) - 100
                if remaining > 100:
                    doc_text = doc_marker + doc[:remaining] + "..."
                else:
                    break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
            
            if current_length >= max_length:
                break
        
        context = "\n".join(context_parts)
        return context, citations[:len(context_parts)]
    
    def _generate_answer(self, query: str, context: str, citations: List[Dict]) -> Dict:
        """
        Generate answer using LLM.
        
        Args:
            query: User query
            context: Retrieved context
            citations: List of citations
            
        Returns:
            Dictionary with answer and metadata
        """
        # Build prompt
        user_prompt = f"""Context from RGIPT documents:
{context}

Question: {query}

Please answer the question using ONLY the information from the context above. Include citations in your answer using the format "According to [Document Name]..." when referencing specific information."""

        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Verify answer is grounded
            is_grounded = True
            if citations:
                # Check if answer references the context
                chunk_texts = [c["text_preview"] for c in citations]
                is_grounded = any(
                    self.citation_manager.verify_citation(chunk, answer)
                    for chunk in chunk_texts
                )
            
            return {
                "answer": answer,
                "citations": citations,
                "is_grounded": is_grounded,
                "model": config.LLM_MODEL,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
            }
            
        except Exception as e:
            error_msg = f"Error generating answer: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "answer": "I apologize, but I encountered an error while generating a response. Please try again.",
                "citations": [],
                "is_grounded": False,
                "error": error_msg
            }
    
    def query(self, question: str, 
              top_k: Optional[int] = None,
              category_filter: Optional[str] = None,
              similarity_threshold: Optional[float] = None) -> Dict:
        """
        Process a query and return answer with citations.
        
        Args:
            question: User question
            top_k: Number of results to retrieve
            category_filter: Filter by document category
            similarity_threshold: Minimum similarity score
            
        Returns:
            Dictionary with answer, citations, and metadata
        """
        # Preprocess query
        preprocessed_query = self._preprocess_query(question)
        
        # Retrieve relevant documents
        results = self.vector_store.search(
            query=preprocessed_query,
            top_k=top_k,
            category_filter=category_filter,
            similarity_threshold=similarity_threshold,
            use_reranking=True
        )
        
        if not results.get("documents"):
            return {
                "answer": "I couldn't find relevant information in the available documents to answer your question. Please try rephrasing or contact an administrator for assistance.",
                "citations": [],
                "is_grounded": False,
                "retrieved_docs": 0
            }
        
        # Build context
        context, citations = self._build_context(results)
        
        if not context:
            return {
                "answer": "I couldn't find enough information in the available documents to answer your question.",
                "citations": [],
                "is_grounded": False,
                "retrieved_docs": len(results.get("documents", []))
            }
        
        # Generate answer
        answer_result = self._generate_answer(question, context, citations)
        
        return {
            **answer_result,
            "retrieved_docs": len(results.get("documents", [])),
            "query": question
        }
    
    def stream_query(self, question: str, 
                    top_k: Optional[int] = None,
                    category_filter: Optional[str] = None):
        """
        Stream query response (for real-time chat).
        
        Args:
            question: User question
            top_k: Number of results to retrieve
            category_filter: Filter by document category
            
        Yields:
            Response chunks
        """
        # Preprocess and retrieve (same as query)
        preprocessed_query = self._preprocess_query(question)
        results = self.vector_store.search(
            query=preprocessed_query,
            top_k=top_k,
            category_filter=category_filter,
            use_reranking=True
        )
        
        if not results.get("documents"):
            yield {
                "type": "error",
                "content": "No relevant documents found"
            }
            return
        
        # Build context
        context, citations = self._build_context(results)
        
        # Stream answer
        try:
            user_prompt = f"""Context from RGIPT documents:
{context}

Question: {question}

Please answer the question using ONLY the information from the context above. Include citations in your answer."""
            
            stream = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.LLM_TEMPERATURE,
                stream=True
            )
            
            yield {
                "type": "citations",
                "content": citations
            }
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "type": "content",
                        "content": chunk.choices[0].delta.content
                    }
            
            yield {
                "type": "done"
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "content": f"Error: {str(e)}"
            }


if __name__ == "__main__":
    # Test RAG engine
    engine = RAGEngine()
    
    test_queries = [
        "What are the library rules?",
        "What is the fee structure?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        result = engine.query(query)
        
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nCitations: {len(result.get('citations', []))}")
        print(f"Grounded: {result.get('is_grounded', False)}")

