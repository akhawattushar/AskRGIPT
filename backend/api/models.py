"""
Pydantic models for API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message/query")
    category_filter: Optional[str] = Field(None, description="Filter by document category")
    top_k: Optional[int] = Field(None, description="Number of results to retrieve")
    similarity_threshold: Optional[float] = Field(None, description="Minimum similarity score (0-1)")


class Citation(BaseModel):
    """Citation model."""
    source: str
    category: Optional[str] = None
    page: Optional[int] = None
    chunk_id: Optional[int] = None
    text_preview: Optional[str] = None
    similarity: Optional[float] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    citations: List[Citation] = []
    intent: Optional[str] = None
    used_function: bool = False
    is_grounded: bool = True
    retrieved_docs: int = 0
    query: Optional[str] = None


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query: str = Field(..., description="Search query")
    top_k: Optional[int] = Field(None, description="Number of results")
    category_filter: Optional[str] = Field(None, description="Filter by category")


class SearchResult(BaseModel):
    """Search result model."""
    document: str
    metadata: Dict[str, Any]
    similarity: float
    rank: int


class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    results: List[SearchResult]
    total: int


class FunctionInfo(BaseModel):
    """Function information model."""
    name: str
    description: str
    parameters: Dict[str, str]


class FunctionsResponse(BaseModel):
    """Response model for functions endpoint."""
    functions: List[FunctionInfo]


class DocumentInfo(BaseModel):
    """Document information model."""
    filename: str
    category: str
    file_path: str
    indexed_at: Optional[str] = None
    chunk_count: Optional[int] = None


class DocumentsResponse(BaseModel):
    """Response model for documents endpoint."""
    documents: List[DocumentInfo]
    total: int


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    vector_store_count: int
    embedding_model: str
    reranker_available: bool

