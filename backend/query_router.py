"""
Query Router
Classifies user intent and routes queries to appropriate handlers (function calling or general RAG).
"""
import re
from typing import Dict, Optional, Tuple
from function_calling import FunctionCallingSystem
from rag_engine import RAGEngine


class QueryRouter:
    """Routes queries to appropriate handlers based on intent classification."""
    
    def __init__(self):
        """Initialize query router."""
        self.function_system = FunctionCallingSystem()
        self.rag_engine = RAGEngine()
        
        # Intent patterns
        self.intent_patterns = {
            "policy_search": [
                r"policy|policies|regulation|regulations|rule|rules",
                r"what.*policy|search.*policy|find.*policy"
            ],
            "fee_query": [
                r"fee|fees|payment|tuition|cost|price",
                r"how much|what.*fee|fee structure"
            ],
            "calendar_query": [
                r"calendar|schedule|date|dates|deadline|when",
                r"academic calendar|exam.*date|registration.*date"
            ],
            "policy_summary": [
                r"summarize|summary|overview|brief|tl;dr|tldr",
                r"what.*policy.*about|explain.*policy"
            ],
            "policy_comparison": [
                r"compare|comparison|difference|differences|vs|versus",
                r"which.*better|what.*difference.*between"
            ]
        }
    
    def classify_intent(self, query: str) -> Tuple[str, Dict]:
        """
        Classify user intent from query.
        
        Args:
            query: User query
            
        Returns:
            Tuple of (intent_type, extracted_parameters)
        """
        query_lower = query.lower()
        
        # Check for policy comparison
        if any(re.search(pattern, query_lower) for pattern in self.intent_patterns["policy_comparison"]):
            # Try to extract two policy names
            policies = re.findall(r'(\w+(?:\s+\w+)*)\s+(?:policy|policies)', query_lower)
            if len(policies) >= 2:
                return "policy_comparison", {
                    "policy1": policies[0],
                    "policy2": policies[1]
                }
        
        # Check for policy summary
        if any(re.search(pattern, query_lower) for pattern in self.intent_patterns["policy_summary"]):
            # Extract policy name
            policy_match = re.search(r'(?:summarize|summary|overview).*?(?:of|for)?\s*([\w\s]+?)(?:\s+policy)?', query_lower)
            if policy_match:
                return "policy_summary", {
                    "policy_name": policy_match.group(1).strip()
                }
        
        # Check for fee query
        if any(re.search(pattern, query_lower) for pattern in self.intent_patterns["fee_query"]):
            # Extract program and semester
            program_match = re.search(r'(b\.?tech|m\.?tech|phd|mba|program)', query_lower)
            semester_match = re.search(r'semester\s+(\d+|one|two|three|four|first|second|third|fourth)', query_lower)
            
            return "fee_query", {
                "program": program_match.group(1) if program_match else None,
                "semester": semester_match.group(1) if semester_match else None
            }
        
        # Check for calendar query
        if any(re.search(pattern, query_lower) for pattern in self.intent_patterns["calendar_query"]):
            # Extract event type and date range
            event_types = ["registration", "examination", "exam", "holiday", "vacation", "deadline"]
            event_type = None
            for et in event_types:
                if et in query_lower:
                    event_type = et
                    break
            
            date_match = re.search(r'(\d{4}[-/]\d{4}|\d{4})', query_lower)
            
            return "calendar_query", {
                "event_type": event_type,
                "date_range": date_match.group(1) if date_match else None
            }
        
        # Check for policy search
        if any(re.search(pattern, query_lower) for pattern in self.intent_patterns["policy_search"]):
            # Extract policy type
            policy_types = ["academic", "hostel", "library", "examination", "admission"]
            policy_type = None
            for pt in policy_types:
                if pt in query_lower:
                    policy_type = pt
                    break
            
            return "policy_search", {
                "query": query,
                "policy_type": policy_type
            }
        
        # Default to general query
        return "general", {}
    
    def route(self, query: str) -> Dict:
        """
        Route query to appropriate handler.
        
        Args:
            query: User query
            
        Returns:
            Dictionary with response and metadata
        """
        intent, parameters = self.classify_intent(query)
        
        response = {
            "intent": intent,
            "parameters": parameters,
            "used_function": False
        }
        
        # Route to appropriate handler
        if intent == "policy_search":
            result = self.function_system.search_policies(
                parameters.get("query", query),
                parameters.get("policy_type")
            )
            response.update(result)
            response["used_function"] = True
        
        elif intent == "fee_query":
            result = self.function_system.get_fee_structure(
                parameters.get("program"),
                parameters.get("semester")
            )
            response.update(result)
            response["used_function"] = True
        
        elif intent == "calendar_query":
            result = self.function_system.get_academic_calendar(
                parameters.get("event_type"),
                parameters.get("date_range")
            )
            response.update(result)
            response["used_function"] = True
        
        elif intent == "policy_summary":
            result = self.function_system.summarize_policy(
                parameters.get("policy_name", query)
            )
            response.update(result)
            response["used_function"] = True
        
        elif intent == "policy_comparison":
            result = self.function_system.compare_policies(
                parameters.get("policy1"),
                parameters.get("policy2")
            )
            response.update(result)
            response["used_function"] = True
        
        else:
            # General RAG query
            result = self.rag_engine.query(query)
            response.update({
                "answer": result.get("answer"),
                "citations": result.get("citations", []),
                "is_grounded": result.get("is_grounded", False)
            })
        
        return response


if __name__ == "__main__":
    # Test query router
    router = QueryRouter()
    
    test_queries = [
        "What is the fee structure for B.Tech semester 1?",
        "Summarize the academic policy",
        "Compare library policy and hostel policy",
        "When is the examination date?",
        "What are the library rules?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        result = router.route(query)
        
        print(f"Intent: {result['intent']}")
        print(f"Used Function: {result['used_function']}")
        print(f"Answer: {result.get('answer', result.get('result', 'No answer'))}")
        print(f"Citations: {len(result.get('citations', []))}")

