import subprocess
import sys

# Install packages
print("Installing required packages...")
packages = [
    "openai==1.35.13",
    "sentence-transformers==2.7.0",
    "chromadb==0.5.15",
    "duckduckgo-search==6.3.5",
    "python-dotenv==1.0.1",
    "httpx",
    "beautifulsoup4",
    "requests"
]

for package in packages:
    print(f"Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", package])

print("All packages installed!")

import gradio as gr
import os
import httpx
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from duckduckgo_search import DDGS

# Get API key from HF Secrets
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in HF Secrets!")

groq_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    http_client=httpx.Client()
)

# ============ WEB SCRAPING FUNCTION ============
def web_search(query: str, max_results: int = 3):
    """Smart search: Try web scrape FIRST, then fallback to hardcoded"""
    scraped_data = scrape_website_smart(query)
    if scraped_data:
        return [{"snippet": scraped_data}]
    
    hardcoded_answer = search_hardcoded_database(query)
    if hardcoded_answer:
        return [{"snippet": hardcoded_answer}]
    
    try:
        ddgs = DDGS()
        results = ddgs.text(f"rgipt.ac.in {query}", max_results=max_results)
        return [{"snippet": r.get("body", "")} for r in results]
    except:
        return [{"snippet": "Information not found."}]

def scrape_website_smart(query: str):
    """Try to scrape with timeout & error handling"""
    urls = [
        "https://www.rgipt.ac.in",
        "https://www.rgipt.ac.in/article/en/central-library",
    ]
    
    for url in urls:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=3)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text()
                
                if query.lower() in text.lower():
                    idx = text.lower().find(query.lower())
                    return text[max(0, idx-200):min(len(text), idx+500)]
        except:
            continue
    
    return None

def search_hardcoded_database(query: str):
    """Fallback: Hardcoded RGIPT knowledge base"""
    knowledge_base = {
        "library hours": "📚 RGIPT Central Library: 10:00 AM to 12:00 midnight",
        "library timing": "📚 RGIPT Central Library: 10:00 AM to 12:00 midnight",
        "admission": "🎓 Apply at www.rgipt.ac.in | B.Tech & MBA programs | Check eligibility criteria",
        "hostel": "🏠 RGIPT provides hostel for students | Apply through admission portal",
        "exam": "📝 As per academic calendar | Contact your department for dates",
        "fee": "💰 B.Tech ~8 LPA avg | MBA varies | Check admission portal",
        "campus": "📍 Jais, Amethi, UP, India",
        "contact": "📞 +91-522-2279000 | 🌐 www.rgipt.ac.in",
    }
    
    query_lower = query.lower()
    
    if query_lower in knowledge_base:
        return knowledge_base[query_lower]
    
    for key, value in knowledge_base.items():
        if key in query_lower or query_lower in key:
            return value
    
    return None

# ============ MAIN ASK FUNCTION ============
def ask_rgipt(question: str):
    """Main function to answer questions"""
    if not question.strip():
        return "Please ask a question! 😊"
    
    try:
        web_results = web_search(question)
        combined_context = "\n".join([r['snippet'] for r in web_results[:2]]) if web_results else ""
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are AskRGIPT, helpful AI for RGIPT. Provide accurate, well-formatted answers with emojis and headers."
                },
                {
                    "role": "user",
                    "content": f"""Context: {combined_context if combined_context else 'Use general knowledge'}

Question: {question}

Provide a helpful, well-formatted answer with:
- Bold headers (**Header**)
- Bullet points
- Emojis where appropriate"""
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=500
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {str(e)}"

# ============ GRADIO INTERFACE ============
demo = gr.Interface(
    fn=ask_rgipt,
    inputs=gr.Textbox(
        label="Ask anything about RGIPT",
        placeholder="What are library hours?",
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
