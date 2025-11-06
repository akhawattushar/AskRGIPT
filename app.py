import subprocess
import sys

# Install all packages at startup
packages = [
    "openai==0.28.1",   # <--- FIXED VERSION
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
import openai   # <--- using classic client
import requests
from bs4 import BeautifulSoup
import PyPDF2
from duckduckgo_search import DDGS

# Load Groq key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Configure Groq API endpoint (OpenAI Compatible)
openai.api_key = GROQ_API_KEY
openai.api_base = "https://api.groq.com/openai/v1"

# ============ WEB SEARCH ============
def web_search(query: str):
    try:
        ddgs = DDGS()
        results = ddgs.text(f"rgipt {query}", max_results=3)
        return [r.get("body", "") for r in results]
    except:
        return []

# ============ WEB SCRAPING ============
def scrape_website(url: str):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()[:1000]
    except:
        return ""

# ============ PDF PROCESSING ============
def process_pdf(file_path: str):
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages[:3]:
                text += page.extract_text()
        return text[:500]
    except:
        return ""

# ============ MAIN ASK FUNCTION ============
def ask_rgipt(question: str):
    if not question.strip():
        return "Please ask a question!"
    
    try:
        search_results = web_search(question)
        context = " ".join(search_results[:2]) if search_results else ""

        response = openai.ChatCompletion.create(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=500,
            messages=[
                {"role": "system", "content": "You are AskRGIPT, helpful AI for RGIPT."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {str(e)}"

# ============ GRADIO INTERFACE ============
demo = gr.Interface(
    fn=ask_rgipt,
    inputs="text",
    outputs="text",
    title="🎓 AskRGIPT - Full Version",
    description="Ask anything about RGIPT (with PDF, web scraping, search)"
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
