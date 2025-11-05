import gradio as gr
import os
import sys

# Add backend to path
sys.path.insert(0, 'backend')

from dotenv import load_dotenv
from groq import Groq
from backend.vector_store import VectorStore
from duckduckgo_search import DDGS

# Load environment
load_dotenv('backend/.env')
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)
vector_store = VectorStore()

def web_search(query: str, max_results: int = 3):
    """Search web"""
    try:
        ddgs = DDGS()
        results = ddgs.text(f"rgipt.ac.in {query}", max_results=max_results)
        return [{"snippet": r.get("body", "")} for r in results]
    except:
        return []

def ask_rgipt(question: str):
    """Chatbot function"""
    if not question.strip():
        return "Please ask a question! 😊"
    
    try:
        # Get context
        results = vector_store.query(question, n_results=5)
        web_results = web_search(question)
        
        # Combine
        combined_context = ""
        if results.get('documents'):
            combined_context += "\n".join(results['documents'][0][:3])
        if web_results:
            combined_context += "\n" + "\n".join([r['snippet'] for r in web_results[:2]])
        
        # Generate
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are AskRGIPT, helpful AI for RGIPT students. Provide accurate, formatted answers with emojis."},
                {"role": "user", "content": f"Context: {combined_context if combined_context else 'Use general knowledge'}\n\nQuestion: {question}\n\nProvide helpful answer:"}
            ],
            model="llama-3.1-70b-versatile",
            temperature=0.3,
            max_tokens=500
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Sorry, error occurred: {str(e)}"

# Create interface
demo = gr.Interface(
    fn=ask_rgipt,
    inputs=gr.Textbox(
        label="Ask anything about RGIPT",
        placeholder="What are the library operational hours?",
        lines=3
    ),
    outputs=gr.Markdown(label="Answer"),
    title="🎓 AskRGIPT - Your AI Campus Assistant",
    description="**Ask about Library, Admissions, Hostel, Exams, and more!**",
    examples=[
        ["What are the library operational hours?"],
        ["How do I apply for admission?"],
        ["Tell me about hostel facilities"]
    ],
    theme=gr.themes.Soft()
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
