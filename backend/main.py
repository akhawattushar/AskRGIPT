from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from vector_store import VectorStore
from duckduckgo_search import DDGS

app = FastAPI(title="AskRGIPT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_store = VectorStore()

# YOUR GROQ API KEY
groq_client = Groq(api_key="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")

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: list

def web_search(query: str, max_results: int = 3):
    """Search web for RGIPT-specific information"""
    try:
        ddgs = DDGS()
        search_query = f"rgipt.ac.in {query}"
        results = ddgs.text(search_query, max_results=max_results)
        
        web_context = []
        for result in results:
            web_context.append(f"[{result['title']}]\n{result['body']}")
        
        return "\n\n".join(web_context) if web_context else None
    except:
        return None

@app.get("/")
def read_root():
    return {"message": "AskRGIPT Hybrid AI is running!", "documents": 1746, "status": "ready"}

@app.post("/query")
def query_documents(request: QueryRequest):
    try:
        # STEP 1: Search local documents
        results = vector_store.collection.query(
            query_texts=[request.question],
            n_results=5
        )
        
        local_context = ""
        sources = []
        
        if results and results['documents'][0]:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            
            context_parts = []
            for i, doc in enumerate(documents):
                source = metadatas[i].get('source', f'Document {i+1}') if i < len(metadatas) else f'Document {i+1}'
                context_parts.append(f"[{source}]\n{doc[:350]}")
                sources.append(source)
            
            local_context = "\n\n".join(context_parts)
        
        # STEP 2: Search web
        web_context = web_search(request.question)
        
        # STEP 3: Combine contexts
        combined_context = ""
        if local_context:
            combined_context += f"=== OFFICIAL RGIPT DOCUMENTS ===\n{local_context}\n\n"
        if web_context:
            combined_context += f"=== RGIPT WEBSITE ===\n{web_context}"
            sources.append("RGIPT Official Website")
        
        # STEP 4: Generate beautiful answer
        system_prompt = """You are the OFFICIAL RGIPT virtual assistant.

FORMAT YOUR ANSWERS BEAUTIFULLY:
- Use **bold** for important terms and headings
- Use bullet points with • for lists
- Use numbers (1., 2., 3.) for steps
- Use emojis (📚 🎓 ⚠️ ✅ 📖 💡) to make it engaging
- Break long text into short paragraphs (2-3 lines max)
- Use ### for section headings

CONTENT RULES:
1. NEVER say "not in documents" or "contact staff"
2. Be SPECIFIC with numbers, dates, rules
3. Give PRACTICAL examples students can actually use
4. Be CONFIDENT and DIRECT like ChatGPT
5. If using general knowledge, briefly mention "based on standard academic practices"

TONE: Professional but friendly, like a helpful senior student."""

        user_message = f"""Context:
{combined_context if combined_context else "No specific documents - use general academic knowledge."}

Student Question: {request.question}

Provide a COMPLETE, HELPFUL, BEAUTIFULLY FORMATTED answer."""

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=500
        )
        
        answer = chat_completion.choices[0].message.content
        
        return {
            "answer": answer.strip(),
            "sources": list(set(sources))[:5] if sources else ["General RGIPT Knowledge"]
        }
        
    except Exception as e:
        return {
            "answer": f"Error: {str(e)}. Please try rephrasing your question.",
            "sources": []
        }

@app.get("/health")
def health_check():
    return {"status": "healthy", "docs": 1746, "mode": "hybrid"}
