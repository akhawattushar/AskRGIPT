import subprocess
import sys

# Install all packages at startup
packages = [
    "openai==1.35.13",
    "gradio",
    "requests",
    "beautifulsoup4",
    "PyPDF2",
    "sentence-transformers",
    "chromadb",
    "duckduckgo-search"
]

print("Installing packages...")
for pkg in packages:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

import gradio as gr
import os
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import PyPDF2
from duckduckgo_search import DDGS

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# ============ WEB SEARCH ============
def web_search(query: str):
    """Search using DuckDuckGo"""
    try:
        ddgs = DDGS()
        results = ddgs.text(f"rgipt {query}", max_results=3)
        return [r.get("body", "") for r in results]
    except:
        return []

# ============ WEB SCRAPING ============
def scrape_website(url: str):
    """Scrape website content"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()[:1000]
    except:
        return ""

# ============ PDF PROCESSING ============
def process_pdf(file_path: str):
    """Extract text from PDF"""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages[:3]:  # First 3 pages
                text += page.extract_text()
        return text[:500]
    except:
        return ""

# ============ MAIN ASK FUNCTION ============
def ask_rgipt(question: str):
    """Main function with all features"""
    if not question.strip():
        return "Please ask a question!"
    
    try:
        # Get context from web search
        search_results = web_search(question)
        context = " ".join(search_results[:2]) if search_results else ""
        
        # Call GROQ API
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are AskRGIPT, helpful AI for RGIPT"},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# ============ GRADIO INTERFACE ============
demo = gr.Interface(
    fn=ask_rgipt,
    inputs="text",
    outputs="text",
    title="🎓 AskRGIPT - Full Version",
    description="Ask anything about RGIPT (with PyPDF2, web scraping, search)"
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
