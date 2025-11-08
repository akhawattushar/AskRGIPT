"""
Function Calling System
Structured query handlers for specific types of queries (policies, fees, calendar, etc.).
"""
from typing import Dict, List, Optional, Any
from rag_engine import RAGEngine
from vector_store import VectorStore
from citation_manager import CitationManager


class FunctionCallingSystem:
    """System for handling structured queries via function calls."""
    
    def __init__(self):
        """Initialize function calling system."""
        self.rag_engine = RAGEngine()
        self.vector_store = VectorStore()
        self.citation_manager = CitationManager()
    
    def search_policies(self, query: str, policy_type: Optional[str] = None) -> Dict:
        """
        Search for specific policies.
        
        Args:
            query: Search query
            policy_type: Type of policy (e.g., "academic", "hostel", "library")
            
        Returns:
            Dictionary with policy information and citations
        """
        category_filter = "policies" if policy_type is None else None
        
        # Enhance query with policy-specific terms
        enhanced_query = f"policy {query}" if "policy" not in query.lower() else query
        
        if policy_type:
            enhanced_query += f" {policy_type} policy"
        
        results = self.vector_store.search(
            query=enhanced_query,
            category_filter=category_filter,
            top_k=5,
            use_reranking=True
        )
        
        if not results.get("documents"):
            return {
                "function": "search_policies",
                "result": None,
                "answer": f"I couldn't find information about {query} in the policy documents.",
                "citations": []
            }
        
        # Get answer using RAG
        answer_result = self.rag_engine.query(enhanced_query, category_filter="policies")
        
        return {
            "function": "search_policies",
            "query": query,
            "policy_type": policy_type,
            "result": answer_result.get("answer"),
            "citations": answer_result.get("citations", []),
            "is_grounded": answer_result.get("is_grounded", False)
        }
    
    def get_fee_structure(self, program: Optional[str] = None, semester: Optional[str] = None) -> Dict:
        """
        Get fee structure information.
        
        Args:
            program: Program name (e.g., "B.Tech", "M.Tech")
            semester: Semester number
            
        Returns:
            Dictionary with fee structure information
        """
        query_parts = ["fee structure", "fees", "payment"]
        
        if program:
            query_parts.append(program)
        if semester:
            query_parts.append(f"semester {semester}")
        
        query = " ".join(query_parts)
        
        results = self.vector_store.search(
            query=query,
            top_k=5,
            use_reranking=True
        )
        
        if not results.get("documents"):
            return {
                "function": "get_fee_structure",
                "result": None,
                "answer": "I couldn't find fee structure information in the available documents.",
                "citations": []
            }
        
        answer_result = self.rag_engine.query(query)
        
        return {
            "function": "get_fee_structure",
            "program": program,
            "semester": semester,
            "result": answer_result.get("answer"),
            "citations": answer_result.get("citations", []),
            "is_grounded": answer_result.get("is_grounded", False)
        }
    
    def get_academic_calendar(self, event_type: Optional[str] = None, 
                              date_range: Optional[str] = None) -> Dict:
        """
        Get academic calendar information.
        
        Args:
            event_type: Type of event (e.g., "registration", "examination", "holiday")
            date_range: Date range (e.g., "2024-2025")
            
        Returns:
            Dictionary with calendar information
        """
        query_parts = ["academic calendar", "schedule", "dates"]
        
        if event_type:
            query_parts.append(event_type)
        if date_range:
            query_parts.append(date_range)
        
        query = " ".join(query_parts)
        
        results = self.vector_store.search(
            query=query,
            top_k=5,
            use_reranking=True
        )
        
        if not results.get("documents"):
            return {
                "function": "get_academic_calendar",
                "result": None,
                "answer": "I couldn't find academic calendar information in the available documents.",
                "citations": []
            }
        
        answer_result = self.rag_engine.query(query)
        
        return {
            "function": "get_academic_calendar",
            "event_type": event_type,
            "date_range": date_range,
            "result": answer_result.get("answer"),
            "citations": answer_result.get("citations", []),
            "is_grounded": answer_result.get("is_grounded", False)
        }
    
    def summarize_policy(self, policy_name: str) -> Dict:
        """
        Summarize a specific policy.
        
        Args:
            policy_name: Name of the policy to summarize
            
        Returns:
            Dictionary with policy summary
        """
        query = f"{policy_name} policy summary overview"
        
        results = self.vector_store.search(
            query=query,
            category_filter="policies",
            top_k=10,  # Get more context for summarization
            use_reranking=True
        )
        
        if not results.get("documents"):
            return {
                "function": "summarize_policy",
                "policy_name": policy_name,
                "result": None,
                "answer": f"I couldn't find information about {policy_name} policy.",
                "citations": []
            }
        
        # Build extended context for summarization
        context_parts = []
        citations = []
        
        for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            context_parts.append(doc)
            citations.append(self.citation_manager.extract_citation(meta, doc))
        
        context = "\n\n".join(context_parts)
        
        # Generate summary
        summary_prompt = f"""Please provide a concise summary of the {policy_name} policy based on the following information:

{context}

Provide a summary in bullet points covering the key aspects of this policy."""
        
        answer_result = self.rag_engine._generate_answer(
            summary_prompt,
            context,
            citations
        )
        
        return {
            "function": "summarize_policy",
            "policy_name": policy_name,
            "result": answer_result.get("answer"),
            "citations": citations,
            "is_grounded": answer_result.get("is_grounded", False)
        }
    
    def compare_policies(self, policy1: str, policy2: str) -> Dict:
        """
        Compare two policies.
        
        Args:
            policy1: Name of first policy
            policy2: Name of second policy
            
        Returns:
            Dictionary with comparison
        """
        # Search for both policies
        results1 = self.vector_store.search(
            query=f"{policy1} policy",
            category_filter="policies",
            top_k=5,
            use_reranking=True
        )
        
        results2 = self.vector_store.search(
            query=f"{policy2} policy",
            category_filter="policies",
            top_k=5,
            use_reranking=True
        )
        
        if not results1.get("documents") or not results2.get("documents"):
            return {
                "function": "compare_policies",
                "policy1": policy1,
                "policy2": policy2,
                "result": None,
                "answer": f"I couldn't find information about one or both policies to compare.",
                "citations": []
            }
        
        # Build context from both policies
        context_parts = []
        citations = []
        
        for doc, meta in zip(results1.get("documents", []), results1.get("metadatas", [])):
            context_parts.append(f"[{policy1} Policy]\n{doc}")
            citations.append(self.citation_manager.extract_citation(meta, doc))
        
        for doc, meta in zip(results2.get("documents", []), results2.get("metadatas", [])):
            context_parts.append(f"[{policy2} Policy]\n{doc}")
            citations.append(self.citation_manager.extract_citation(meta, doc))
        
        context = "\n\n".join(context_parts)
        
        # Generate comparison
        comparison_prompt = f"""Compare the {policy1} policy and the {policy2} policy. Highlight:
1. Key similarities
2. Key differences
3. Important points from each policy"""
        
        answer_result = self.rag_engine._generate_answer(
            comparison_prompt,
            context,
            citations
        )
        
        return {
            "function": "compare_policies",
            "policy1": policy1,
            "policy2": policy2,
            "result": answer_result.get("answer"),
            "citations": citations,
            "is_grounded": answer_result.get("is_grounded", False)
        }
    
    def get_available_functions(self) -> List[Dict]:
        """Get list of available functions."""
        return [
            {
                "name": "search_policies",
                "description": "Search for specific policies",
                "parameters": {
                    "query": "str - Search query",
                    "policy_type": "str (optional) - Type of policy"
                }
            },
            {
                "name": "get_fee_structure",
                "description": "Get fee structure information",
                "parameters": {
                    "program": "str (optional) - Program name",
                    "semester": "str (optional) - Semester number"
                }
            },
            {
                "name": "get_academic_calendar",
                "description": "Get academic calendar information",
                "parameters": {
                    "event_type": "str (optional) - Type of event",
                    "date_range": "str (optional) - Date range"
                }
            },
            {
                "name": "summarize_policy",
                "description": "Summarize a specific policy",
                "parameters": {
                    "policy_name": "str - Name of the policy"
                }
            },
            {
                "name": "compare_policies",
                "description": "Compare two policies",
                "parameters": {
                    "policy1": "str - Name of first policy",
                    "policy2": "str - Name of second policy"
                }
            }
        ]

