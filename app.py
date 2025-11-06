import subprocess
import sys

packages = [
    "openai==0.28.1",
    "gradio",
    "requests",
    "beautifulsoup4",
    "PyPDF2",
    "duckduckgo-search"
]

print("Installing packages...")
for pkg in packages:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

import gradio as gr
import os
import openai
import requests
from bs4 import BeautifulSoup
import PyPDF2
from duckduckgo_search import DDGS

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
openai.api_key = GROQ_API_KEY
openai.api_base = "https://api.groq.com/openai/v1"

def web_search(query: str):
    try:
        ddgs = DDGS()
        results = ddgs.text(f"rgipt {query}", max_results=3)
        return [r.get("body", "") for r in results]
    except:
        return []

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

demo = gr.Interface(
    fn=ask_rgipt,
    inputs="text",
    outputs="text",
    title="🎓 AskRGIPT",
    description="Ask anything about RGIPT"
)

if __name__ == "__main__":
    # ✅ CORRECT: NO allowed_origins parameter!
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True
    )
