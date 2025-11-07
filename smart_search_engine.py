import re
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import json

class SmartSearchEngine:
    """Intelligent multi-source search with keyword extraction"""
    
    def extract_keywords(self, question: str) -> dict:
        """AI extracts what user is REALLY asking"""
        keywords = {
            "type": None,
            "keywords": [],
            "timeframe": None,
            "specific_item": None
        }
        
        # Keyword extraction patterns
        patterns = {
            "timetable": r"(timetable|schedule|timing|time table|exam|midsem|quiz)",
            "admission": r"(admission|apply|registration|eligibility|criteria)",
            "library": r"(library|hours|open|close|timing|facility)",
            "faculty": r"(faculty|professor|teacher|staff|contact)",
            "fees": r"(fee|fees|cost|charges|payment)",
            "placement": r"(placement|job|campus|recruit|salary)"
        }
        
        question_lower = question.lower()
        
        for query_type, pattern in patterns.items():
            if re.search(pattern, question_lower):
                keywords["type"] = query_type
                break
        
        # Extract timeframe
        timeframe_patterns = {
            "today": r"(today|now|current)",
            "this_week": r"(this week|this semester)",
            "latest": r"(latest|updated|recent|new)"
        }
        
        for tf, pattern in timeframe_patterns.items():
            if re.search(pattern, question_lower):
                keywords["timeframe"] = tf
                break
        
        # Extract specific search terms
        keywords["keywords"] = [word for word in question_lower.split() if len(word) > 3]
        
        return keywords
    
    def search_rgipt_website(self, keywords: dict) -> str:
        """Search directly on RGIPT website"""
        print(f"🔍 Searching RGIPT website for: {keywords['type']}")
        
        try:
            url_map = {
                "timetable": "https://rgipt.ac.in",
                "admission": "https://rgipt.ac.in/article/en/admission",
                "library": "https://rgipt.ac.in/article/en/central-library",
                "faculty": "https://rgipt.ac.in/article/en/faculty",
                "placement": "https://rgipt.ac.in/article/en/placements"
            }
            
            url = url_map.get(keywords['type'], "https://rgipt.ac.in")
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style tags
            for tag in soup(['script', 'style']):
                tag.decompose()
            
            text = soup.get_text(separator='\n')
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Search for relevant content
            relevant_lines = []
            for line in lines:
                if any(kw in line.lower() for kw in keywords['keywords']):
                    relevant_lines.append(line)
            
            return '\n'.join(relevant_lines[:10]) if relevant_lines else text[:1000]
            
        except Exception as e:
            print(f"❌ Website search error: {e}")
            return None
    
    def search_duckduckgo(self, keywords: dict) -> str:
        """Search DuckDuckGo for latest info"""
        print(f"🔎 Searching DuckDuckGo for: {keywords['keywords']}")
        
        try:
            query = f"{' '.join(keywords['keywords'][:3])} RGIPT"
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
            
            if results:
                return "\n".join([f"• {r['title']}: {r['body'][:200]}" for r in results])
            return None
            
        except Exception as e:
            print(f"⚠️ DuckDuckGo search limited: {str(e)[:50]}")
            return None
    
    def format_answer(self, question: str, data: str, keywords: dict) -> str:
        """Format answer BEAUTIFULLY and CONCISELY"""
        
        # Extract key info from data
        lines = data.split('\n') if data else []
        
        format_template = f"""
┌─────────────────────────────────────────┐
│  📌 {keywords['type'].upper() if keywords['type'] else 'INFORMATION'}
└─────────────────────────────────────────┘
🎯 **DIRECT ANSWER:**
{self._extract_direct_answer(lines, keywords)}
📍 **KEY DETAILS:**
{self._extract_key_details(lines, keywords)}
🔗 **SOURCE:** RGIPT Official Website
⏰ **Updated:** Real-time {keywords.get('timeframe', 'Information')}
"""
        return format_template
    
    def _extract_direct_answer(self, lines: list, keywords: dict) -> str:
        """Get the MOST DIRECT answer"""
        
        if keywords['type'] == 'library':
            for line in lines:
                if re.search(r'(\d{1,2}:\d{2}.*midnight|\d{1,2}:\d{2}.*\d{1,2}:\d{2})', line):
                    return f"✓ {line[:150]}"
        
        for line in lines:
            if len(line) > 30 and len(line) < 300:
                return f"✓ {line}"
        
        return "Information not directly found. Showing details below..."
    
    def _extract_key_details(self, lines: list, keywords: dict) -> str:
        """Extract BULLETED key points"""
        details = []
        
        for line in lines[:15]:
            if len(line) > 20 and line[0].isupper():
                details.append(f"• {line[:120]}")
        
        return "\n".join(details[:5]) if details else "• No specific details found"

# Usage example
search_engine = SmartSearchEngine()
