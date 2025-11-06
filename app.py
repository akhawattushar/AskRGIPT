import subprocess
import sys

# Install packages
packages = ["openai==1.35.13", "sentence-transformers==2.7.0", "chromadb==0.5.15", 
            "duckduckgo-search==6.3.5", "httpx", "beautifulsoup4", "requests"]
for pkg in packages:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

import gradio as gr
import os
from openai import OpenAI
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup

# Get API key from HF Secrets
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

def ask_rgipt(question: str):
    """Main function"""
    try:
        msg = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": question}],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=500
        )
        return msg.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

demo = gr.Interface(
    fn=ask_rgipt,
    inputs="text",
    outputs="text",
    title="AskRGIPT"
)

if __name__ == "__main__":
    demo.launch()
