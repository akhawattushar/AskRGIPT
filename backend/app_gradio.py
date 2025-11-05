import gradio as gr
import os
from dotenv import load_dotenv
from groq import Groq
from vector_store import VectorStore
from duckduckgo_search import DDGS

# Load environment
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)
vector_store = VectorStore()

def web_search(query: str, max_results: int = 3):
    """Search web for RGIPT-specific information"""
    try:
        ddgs = DDGS()
        search_query = f"rgipt.ac.in {query}"
        results = ddgs.text(search_query, max_results=max_results)
        return [{"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("body", "")} for r in results]
    except:
        return []

def query_documents(question: str):
    """Query vector store and generate answer"""
    # Get context from vector store
    results = vector_store.query(question, n_results=5)
    
    # Get web search results
    web_results = web_search(question)
    
    # Combine contexts
    combined_context = ""
    if results['documents']:
        combined_context += "From RGIPT Documents:\n" + "\n".join(results['documents'][0])
    
    if web_results:
        combined_context += "\n\nFrom Web Search:\n" + "\n".join([f"{r['snippet']}" for r in web_results])
    
    # Generate answer with Groq
    system_prompt = """You are AskRGIPT, a helpful AI assistant for RGIPT students. 
    Provide accurate, detailed answers based on the context provided. 
    Use emojis to make responses engaging. Format answers beautifully with bullet points and sections."""
    
    user_message = f"""Context:
{combined_context if combined_context else "No specific documents - use general academic knowledge based on standard academic practices"}

Student Question: {question}

Provide a COMPLETE, HELPFUL, BEAUTIFULLY FORMATTED answer."""
    
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        model="llama-3.1-70b-versatile",
        temperature=0.3,
        max_tokens=500
    )
    
    answer = chat_completion.choices[0].message.content
    
    # Format sources
    sources = []
    if results.get('metadatas') and results['metadatas'][0]:
        sources = [m.get('source', 'Unknown') for m in results['metadatas'][0]]
    
    return answer, "\n".join([f"📚 {s}" for s in sources[:3]])

# Create Gradio interface
with gr.Blocks(theme=gr.themes.Soft(), title="AskRGIPT") as demo:
    gr.Markdown("""
    # 🎓 AskRGIPT - Your AI Campus Assistant
    
    **Ask anything about RGIPT - Library hours, Admissions, Hostel, Exams, Fees, and more!**
    """)
    
    with gr.Row():
        with gr.Column(scale=4):
            question_input = gr.Textbox(
                label="Your Question",
                placeholder="What are the library operational hours?",
                lines=2
            )
        
    with gr.Row():
        submit_btn = gr.Button("Ask AskRGIPT 🚀", variant="primary", size="lg")
        clear_btn = gr.ClearButton([question_input], value="Clear 🔄")
    
    with gr.Row():
        answer_output = gr.Markdown(label="Answer")
    
    with gr.Row():
        sources_output = gr.Textbox(label="Sources", lines=3)
    
    # Examples
    gr.Examples(
        examples=[
            ["What are the library operational hours?"],
            ["How do I apply for admission?"],
            ["Tell me about hostel facilities"],
            ["What is the fee structure?"],
            ["When are the examinations held?"]
        ],
        inputs=question_input
    )
    
    submit_btn.click(
        fn=query_documents,
        inputs=question_input,
        outputs=[answer_output, sources_output]
    )
    
    gr.Markdown("""
    ---
    **Made with ❤️ for RGIPT Students | Powered by Groq LLM + ChromaDB**
    """)

if __name__ == "__main__":
    demo.launch()
