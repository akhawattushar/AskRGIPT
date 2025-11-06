import subprocess
import sys

# Install packages
packages = ["openai==1.35.13", "httpx", "beautifulsoup4", "requests", "gradio"]
for pkg in packages:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

import gradio as gr
import os
from openai import OpenAI
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ============ DIAGNOSTIC FUNCTIONS ============
def test_api_key():
    """Check 1: Is API key present?"""
    if GROQ_API_KEY:
        return f"✅ API Key Found: {GROQ_API_KEY[:10]}..."
    return "❌ API Key NOT found!"

def test_groq_connection():
    """Check 2: Can we connect to GROQ?"""
    try:
        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        # Try a simple test
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama-3.3-70b-versatile",
            max_tokens=10
        )
        return "✅ GROQ API is WORKING!"
    except Exception as e:
        return f"❌ GROQ Connection Failed: {str(e)}"

def test_network():
    """Check 3: Is internet working?"""
    try:
        r = requests.get("https://api.groq.com", timeout=5)
        return f"✅ Network OK (Status: {r.status_code})"
    except Exception as e:
        return f"❌ Network Error: {str(e)}"

def full_diagnostic():
    """Run all tests"""
    results = []
    results.append("=" * 50)
    results.append("🔍 ASKRGIPT DIAGNOSTIC TEST")
    results.append("=" * 50)
    results.append("")
    results.append("TEST 1: API KEY")
    results.append(test_api_key())
    results.append("")
    results.append("TEST 2: NETWORK CONNECTION")
    results.append(test_network())
    results.append("")
    results.append("TEST 3: GROQ API CONNECTION")
    results.append(test_groq_connection())
    results.append("")
    results.append("=" * 50)
    
    return "\n".join(results)

# ============ GRADIO INTERFACE ============
demo = gr.Interface(
    fn=full_diagnostic,
    inputs=None,
    outputs=gr.Textbox(label="Diagnostic Results", lines=20),
    title="🔧 AskRGIPT Diagnostic Tool",
    description="Click submit to run system diagnostics",
    allow_flagging="never"
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
