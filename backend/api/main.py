"""
FastAPI main application.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import json
from typing import List
import os

from api.models import (
    ChatRequest, ChatResponse, SearchRequest, SearchResponse,
    FunctionsResponse, DocumentsResponse, HealthResponse,
    Citation, SearchResult, FunctionInfo, DocumentInfo
)
from query_router import QueryRouter
from vector_store import VectorStore
from indexing_pipeline import IndexingPipeline
from config import config

app = FastAPI(
    title="Campus Compass",
    description="RAG chatbot for RGIPT college queries",
    version="1.0.0"
)

# Frontend path
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend")
frontend_path = os.path.abspath(frontend_path)

# Mount static files (CSS, JS)
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
router = QueryRouter()
vector_store = VectorStore()
indexing_pipeline = IndexingPipeline()


@app.get("/", tags=["Root"])
async def root():
    """Serve frontend homepage."""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "Campus Compass API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/index.html", tags=["Frontend"])
async def index():
    """Serve frontend index."""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    stats = vector_store.get_collection_stats()
    return HealthResponse(
        status="healthy",
        vector_store_count=stats["total_documents"],
        embedding_model=stats["embedding_model"],
        reranker_available=stats["reranker_available"]
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Chat endpoint for question answering.
    """
    try:
        result = router.route(request.message)
        
        # Convert citations to response format
        citations = []
        for cit in result.get("citations", []):
            citations.append(Citation(
                source=cit.get("source", "Unknown"),
                category=cit.get("category"),
                page=cit.get("page"),
                chunk_id=cit.get("chunk_id"),
                text_preview=cit.get("text_preview"),
                similarity=cit.get("similarity")
            ))
        
        return ChatResponse(
            answer=result.get("answer") or result.get("result", "No answer generated"),
            citations=citations,
            intent=result.get("intent"),
            used_function=result.get("used_function", False),
            is_grounded=result.get("is_grounded", True),
            retrieved_docs=result.get("retrieved_docs", 0),
            query=request.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint for real-time responses.
    """
    def generate():
        try:
            # Use RAG engine streaming
            from rag_engine import RAGEngine
            engine = RAGEngine()
            
            for chunk in engine.stream_query(
                request.message,
                top_k=request.top_k,
                category_filter=request.category_filter
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            query = message_data.get("message", "")
            
            if not query:
                await websocket.send_json({
                    "type": "error",
                    "content": "Empty message"
                })
                continue
            
            # Process query
            result = router.route(query)
            
            # Send response
            await websocket.send_json({
                "type": "response",
                "answer": result.get("answer") or result.get("result", "No answer generated"),
                "citations": result.get("citations", []),
                "intent": result.get("intent"),
                "used_function": result.get("used_function", False),
                "is_grounded": result.get("is_grounded", True)
            })
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": str(e)
        })


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(request: SearchRequest):
    """
    Direct search endpoint for document retrieval.
    """
    try:
        results = vector_store.search(
            query=request.query,
            top_k=request.top_k or config.TOP_K_RESULTS,
            category_filter=request.category_filter
        )
        
        search_results = []
        for i, (doc, meta, dist) in enumerate(zip(
            results.get("documents", []),
            results.get("metadatas", []),
            results.get("distances", [])
        )):
            similarity = 1 - dist if dist else 0.0
            search_results.append(SearchResult(
                document=doc,
                metadata=meta,
                similarity=similarity,
                rank=i + 1
            ))
        
        return SearchResponse(
            results=search_results,
            total=len(search_results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")


@app.get("/functions", response_model=FunctionsResponse, tags=["Functions"])
async def get_functions():
    """
    Get list of available function calling functions.
    """
    from function_calling import FunctionCallingSystem
    function_system = FunctionCallingSystem()
    functions = function_system.get_available_functions()
    
    function_infos = []
    for func in functions:
        function_infos.append(FunctionInfo(
            name=func["name"],
            description=func["description"],
            parameters=func["parameters"]
        ))
    
    return FunctionsResponse(functions=function_infos)


@app.get("/documents", response_model=DocumentsResponse, tags=["Documents"])
async def get_documents():
    """
    Get list of indexed documents.
    """
    documents = []
    
    # Scan data directory
    folders = ["pdfs", "notices", "policies", "handbooks"]
    
    for folder in folders:
        folder_path = os.path.join(config.DATA_DIR, folder)
        if not os.path.exists(folder_path):
            continue
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                # Check if indexed
                indexed_info = indexing_pipeline.index_metadata.get("indexed_files", {}).get(file_path)
                
                documents.append(DocumentInfo(
                    filename=filename,
                    category=folder,
                    file_path=file_path,
                    indexed_at=indexed_info.get("indexed_at") if indexed_info else None,
                    chunk_count=indexed_info.get("chunk_count") if indexed_info else None
                ))
    
    return DocumentsResponse(
        documents=documents,
        total=len(documents)
    )


@app.post("/index", tags=["Indexing"])
async def trigger_indexing(incremental: bool = True, clear_existing: bool = False):
    """
    Trigger document indexing.
    """
    try:
        indexing_pipeline.index_all_documents(
            incremental=incremental,
            clear_existing=clear_existing
        )
        return {
            "status": "success",
            "message": "Indexing completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexing: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

