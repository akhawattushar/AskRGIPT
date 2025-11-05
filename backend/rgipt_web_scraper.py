import requests
from bs4 import BeautifulSoup
from vector_store import VectorStore
import time

class RGIPTWebScraper:
    def __init__(self):
        self.base_url = "https://www.rgipt.ac.in"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.vector_store = VectorStore()
        
    def clean_text(self, text):
        """Clean and normalize text"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove common noise words
        noise_phrases = [
            'Home', 'About Us', 'Admissions', 'Academics', 
            'Research', 'Contact', 'Login', 'Register',
            'Skip to main content', 'Skip to navigation'
        ]
        for phrase in noise_phrases:
            text = text.replace(phrase, '')
        return text.strip()
    
    def scrape_pages(self):
        """Scrape RGIPT pages with focused content extraction"""
        
        pages = {
            'Library Hours and Facilities': {
                'url': '/article/en/central-library',
                'selectors': ['article', 'main', '.content-area', '.entry-content']
            },
            'Admission Requirements': {
                'url': '/article/en/admissions',
                'selectors': ['article', 'main', '.content-area']
            },
            'Hostel Information': {
                'url': '/article/en/hostel-facilities',
                'selectors': ['article', 'main', '.content-area']
            },
            'Examination Rules': {
                'url': '/article/en/examination',
                'selectors': ['article', 'main', '.content-area']
            },
            'Fee Structure': {
                'url': '/article/en/fee-structure',
                'selectors': ['article', 'main', '.content-area']
            },
        }
        
        all_documents = []
        all_metadatas = []
        all_ids = []
        doc_id = 0
        
        for page_name, page_info in pages.items():
            try:
                url = self.base_url + page_info['url']
                print(f"🔄 {page_name}...")
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                    element.decompose()
                
                # Try multiple selectors to find main content
                content = None
                for selector in page_info['selectors']:
                    content = soup.select_one(selector)
                    if content and len(content.get_text(strip=True)) > 200:
                        break
                
                if not content:
                    content = soup.find('body')
                
                if not content:
                    print(f"⚠️ {page_name}: No content")
                    continue
                
                # Extract and clean text
                text = content.get_text(separator=' ', strip=True)
                text = self.clean_text(text)
                
                if len(text) < 100:
                    print(f"⚠️ {page_name}: Too short ({len(text)} chars)")
                    continue
                
                # Create focused chunks
                chunks = self.chunk_text(text, chunk_size=300)
                print(f"✅ {page_name}: {len(chunks)} chunks ({len(text)} chars)")
                
                for i, chunk in enumerate(chunks):
                    all_documents.append(chunk)
                    all_metadatas.append({
                        'source': f'RGIPT Official - {page_name}',
                        'url': url,
                        'section': page_name,
                        'chunk_id': i
                    })
                    all_ids.append(f"web_{doc_id}")
                    doc_id += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ {page_name}: {e}")
        
        # Add to vector store
        if all_documents:
            print(f"\n📊 Adding {len(all_documents)} focused chunks...")
            self.vector_store.collection.add(
                documents=all_documents,
                metadatas=all_metadatas,
                ids=all_ids
            )
            print(f"✅ Success! Added {doc_id} chunks")
        else:
            print("❌ No content scraped!")
    
    def chunk_text(self, text, chunk_size=300):
        """Create smaller, focused chunks"""
        sentences = text.split('.')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
            
            current_chunk.append(sentence)
            current_length += len(sentence)
            
            if current_length >= chunk_size:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = []
                current_length = 0
        
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        
        return chunks

if __name__ == "__main__":
    scraper = RGIPTWebScraper()
    scraper.scrape_pages()
