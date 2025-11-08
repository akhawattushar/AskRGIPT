"""
Citation Manager
Extracts and formats citations from retrieved documents.
"""
from typing import List, Dict, Optional
import re


class CitationManager:
    """Manages citation extraction and formatting."""
    
    @staticmethod
    def extract_citation(metadata: Dict, chunk_text: str, page_num: Optional[int] = None) -> Dict:
        """
        Extract citation information from metadata and chunk.
        
        Args:
            metadata: Document metadata
            chunk_text: Text chunk content
            page_num: Page number (if available)
            
        Returns:
            Dictionary with citation information
        """
        citation = {
            "source": metadata.get("source", "Unknown"),
            "category": metadata.get("category", "unknown"),
            "chunk_id": metadata.get("chunk_id", 0),
            "file_path": metadata.get("file_path", ""),
            "page": page_num or metadata.get("page", None),
            "extraction_method": metadata.get("extraction_method", "unknown"),
            "ocr_confidence": metadata.get("ocr_confidence"),
            "text_preview": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
        }
        
        return citation
    
    @staticmethod
    def format_citation(citation: Dict, style: str = "standard") -> str:
        """
        Format citation as a string.
        
        Args:
            citation: Citation dictionary
            style: Citation style ("standard", "mla", "apa")
            
        Returns:
            Formatted citation string
        """
        source = citation.get("source", "Unknown Document")
        page = citation.get("page")
        category = citation.get("category", "").title()
        
        if style == "standard":
            if page:
                return f"According to {source} (page {page})"
            else:
                return f"According to {source}"
        elif style == "mla":
            if page:
                return f'({source} {page})'
            else:
                return f'({source})'
        elif style == "apa":
            if page:
                return f"({source}, p. {page})"
            else:
                return f"({source})"
        else:
            return source
    
    @staticmethod
    def format_citations(citations: List[Dict], style: str = "standard") -> str:
        """
        Format multiple citations.
        
        Args:
            citations: List of citation dictionaries
            style: Citation style
            
        Returns:
            Formatted citations string
        """
        if not citations:
            return ""
        
        if len(citations) == 1:
            return CitationManager.format_citation(citations[0], style)
        
        # Multiple citations
        sources = set()
        for citation in citations:
            source = citation.get("source", "Unknown")
            page = citation.get("page")
            if page:
                sources.add(f"{source} (page {page})")
            else:
                sources.add(source)
        
        if style == "standard":
            if len(sources) == 1:
                return f"According to {list(sources)[0]}"
            else:
                return f"According to multiple sources: {', '.join(sorted(sources))}"
        else:
            return f"({', '.join(sorted(sources))})"
    
    @staticmethod
    def extract_page_number(chunk_text: str, metadata: Dict) -> Optional[int]:
        """
        Extract page number from chunk text or metadata.
        
        Args:
            chunk_text: Text chunk content
            metadata: Document metadata
            
        Returns:
            Page number if found
        """
        # Check metadata first
        if "page" in metadata:
            return metadata["page"]
        
        # Try to extract from chunk text (format: [Page X])
        page_match = re.search(r'\[Page\s+(\d+)\]', chunk_text)
        if page_match:
            return int(page_match.group(1))
        
        return None
    
    @staticmethod
    def create_citation_dict(results: Dict) -> List[Dict]:
        """
        Create citation dictionaries from search results.
        
        Args:
            results: Search results from vector store
            
        Returns:
            List of citation dictionaries
        """
        citations = []
        
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            page_num = CitationManager.extract_page_number(doc, meta)
            citation = CitationManager.extract_citation(meta, doc, page_num)
            citation["rank"] = i + 1
            citation["similarity"] = 1 - results.get("distances", [0])[i] if results.get("distances") else None
            citations.append(citation)
        
        return citations
    
    @staticmethod
    def verify_citation(chunk_text: str, answer: str) -> bool:
        """
        Verify that answer is grounded in the chunk text.
        Simple check for now - can be enhanced with semantic similarity.
        
        Args:
            chunk_text: Source chunk text
            answer: Generated answer
            
        Returns:
            True if answer appears to be grounded in chunk
        """
        # Simple keyword overlap check
        chunk_words = set(chunk_text.lower().split())
        answer_words = set(answer.lower().split())
        
        # Remove common words
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        chunk_words -= common_words
        answer_words -= common_words
        
        if not chunk_words:
            return False
        
        overlap = len(chunk_words & answer_words) / len(answer_words) if answer_words else 0
        
        # If more than 20% overlap, consider it grounded
        return overlap > 0.2

