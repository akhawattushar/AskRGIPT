import subprocess
import sys
import os

packages = [
    "openai==1.35.13", "gradio>=4.0.0", "requests", "beautifulsoup4",
    "PyPDF2", "langchain==0.1.16", "langchain-huggingface",
    "sentence-transformers", "chromadb", "httpx"
]
for pkg in packages:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

import gradio as gr
from openai import OpenAI
import httpx
import re

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    http_client=httpx.Client()
)

# 🎯 RGIPT SPECIFIC FACTS (Training Data)
RGIPT_KNOWLEDGE = {
    "hostel_capacity": "2-3 students per room (depends on batch/category)",
    "campus_location": "Jais, Uttar Pradesh",
    "fee_annual": "₹1.5-1.9 lakh per year (including hostel + mess)",
    "library_hours": "10:00 AM to 12:00 midnight",
    "admission_type": "JEE Main based (IIIT level)",
    "branches": ["Petroleum", "Mechanical", "Civil", "Electrical", "CS", "ECE", "AI"],
    "placement_rate": "95%+ in recent years",
    "placement_avg_package": "₹8-12 lakh average",
    "hostel_mandatory": "Yes, 100% residential campus",
    "scholarship_available": "Yes, merit + merit-cum-means",
    "gender_distribution": "Mixed hostels by floor",
    "food_options": "Multi-cuisine mess facility"
}

def contextualize_to_rgipt(question: str, ai_response: str) -> str:
    """Ensure answer stays focused on RGIPT, not generic"""
    
    response_lower = ai_response.lower()
    
    # ❌ Red flags for generic answers
    generic_phrases = [
        "varies from college to college",
        "most colleges have",
        "generally", "typically in colleges",
        "in most institutions",
        "some universities have",
        "many colleges offer"
    ]
    
    for phrase in generic_phrases:
        if phrase in response_lower:
            print(f"⚠️ Detected generic phrase: {phrase}")
            # Replace with RGIPT-specific context
            if "hostel" in question.lower():
                return f"""🏠 **RGIPT Hostel**
→ **2-3 students per room** (standard)
→ Separate hostels for boys & girls
→ Single room for selected students
→ Mix of single-seaters & shared rooms
💡 Pro Tip: Single rooms assigned based on merit & availability."""
            
            elif "fee" in question.lower():
                return f"""💰 **RGIPT Fee Structure**
→ **₹1.5-1.9 lakh per year**
→ Includes tuition + hostel + mess
→ Semester-based payment
→ Scholarships available for merit students
💡 Pro Tip: Check official website for latest fee structure."""
    
    return ai_response

def format_rgipt_answer(raw_answer: str, question: str) -> str:
    """Format with RGIPT context injected"""
    
    answer = raw_answer.strip()
    
    # Check if question matches RGIPT knowledge base
    question_lower = question.lower()
    
    for topic, info in RGIPT_KNOWLEDGE.items():
        if topic.replace("_", " ") in question_lower or topic.replace("_", "") in question_lower.replace(" ", ""):
            if isinstance(info, str):
                answer = f"🎓 **{topic.replace('_', ' ').title()}:** {info}\n\n{answer}"
            break
    
    # Highlight important keywords
    important_words = ["MUST", "Important", "Required", "RGIPT", "Only"]
    for word in important_words:
        answer = answer.replace(word, f"**{word}**")
    
    # Topic emojis
    emojis = {
        "hostel": "🏠", "library": "📚", "fee": "💰", "placement": "💼",
        "admission": "🎓", "jee": "📝", "cutoff": "📊", "course": "📖"
    }
    
    for topic, emoji in emojis.items():
        pattern = f"(?i)\\b({topic})"
        answer = re.sub(pattern, f"{emoji} \\1", answer)
    
    # Convert to bullets
    lines = answer.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith(('•', '→', '-', '*')):
            formatted_lines.append(line)
            continue
        
        if line.endswith(':'):
            formatted_lines.append(f"\n**{line}**")
            continue
        
        if any(c in line for c in [' is ', ' are ', 'has ', 'have ']):
            if len(line) > 20:
                formatted_lines.append(f"→ {line}")
                continue
        
        formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

def ask_rgipt(question: str) -> str:
    """Search outside but ANSWER = RGIPT ONLY"""
    
    if not question.strip():
        return "❓ Ask me about RGIPT! 🎓\n\n💡 Example: 'Hostel capacity?' or 'JEE cutoff?'"
    
    try:
        print(f"🔍 Processing: {question}")
        
        # STEP 1: Search for RGIPT knowledge first
        question_lower = question.lower()
        for topic in RGIPT_KNOWLEDGE.keys():
            if topic.replace("_", " ") in question_lower:
                print(f"✅ Found RGIPT knowledge: {topic}")
        
        # STEP 2: Send to AI with STRICT RGIPT CONTEXT
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=900,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are RGIPT AI assistant. ANSWER ONLY ABOUT RGIPT.
🎯 RGIPT KNOWLEDGE BASE:
{chr(10).join(f"• {k.replace('_', ' ').title()}: {v}" for k, v in list(RGIPT_KNOWLEDGE.items())[:5])}
CRITICAL RULES:
✅ Answer SPECIFICALLY about RGIPT
✅ Use facts from knowledge base when available
✅ Use → bullet points
✅ NEVER give generic college answers
✅ If asked "how many in hostel room" → answer "RGIPT has 2-3"
✅ Do NOT say "varies" or "generally" or "typically"
✅ Be SPECIFIC to RGIPT only
❌ DON'T:
- Say "varies from college to college"
- Give general advice
- Answer about other colleges
- Use generic comparisons
FORMAT:
🎓 [Topic]
→ RGIPT-specific fact 1
→ RGIPT-specific fact 2
💡 Pro Tip: [something useful about RGIPT]"""
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nAnswer ONLY about RGIPT. Be specific. NO generic answers."
                }
            ]
        )
        
        raw_answer = response.choices[0].message.content.strip()
        print(f"📝 Raw answer received")
        
        # STEP 3: Contextualize to RGIPT
        contextualized = contextualize_to_rgipt(question, raw_answer)
        print(f"✅ Contextualized to RGIPT")
        
        # STEP 4: Format beautifully
        formatted_answer = format_rgipt_answer(contextualized, question)
        
        final_output = f"""🎓 **RGIPT Answer**
━━━━━━━━━━━━━━━━━━
{formatted_answer}
━━━━━━━━━━━━━━━━━━
✨ RGIPT-specific, accurate answer 🚀"""
        
        return final_output
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

# UI
demo = gr.Interface(
    fn=ask_rgipt,
    inputs=gr.Textbox(
        label="🎯 Ask About RGIPT",
        placeholder="e.g., 'Hostel capacity?' or 'How many per room?' (RGIPT-specific)",
        lines=2
    ),
    outputs=gr.Textbox(
        label="✨ RGIPT Answer (No Generic Replies)",
        lines=13,
        interactive=False
    ),
    title="🎓 AskRGIPT - RGIPT Only",
    description="Search anywhere, but ANSWER is RGIPT-SPECIFIC only! 🛡️",
    theme=gr.themes.Soft(),
    examples=[
        ["How many students per hostel room?"],
        ["What's RGIPT fee structure?"],
        ["Library hours at RGIPT?"],
        ["RGIPT placement statistics?"],
        ["Tell me about RGIPT branches"]
    ]
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)