import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import time

class RGIPTScraper:
    def __init__(self):
        self.base_url = "https://www.rgipt.ac.in"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def scrape_all_sections(self):
        """Scrape PDFs from ALL important sections"""
        
        sections = {
            'library': 'https://www.rgipt.ac.in/en/library',
            'academics': 'https://www.rgipt.ac.in/en/academics',
            'admissions': 'https://www.rgipt.ac.in/en/admissions',
            'rules': 'https://www.rgipt.ac.in/en/institute/rules-regulations',
            'notices': 'https://www.rgipt.ac.in/en/notices',
            'students': 'https://www.rgipt.ac.in/en/students',
            'examinations': 'https://www.rgipt.ac.in/en/examination'
        }
        
        all_pdfs = {}
        
        for section_name, url in sections.items():
            print(f"\n🔍 Scraping {section_name}...")
            pdfs = self.get_pdfs_from_page(url)
            all_pdfs[section_name] = pdfs
            print(f"   ✅ Found {len(pdfs)} PDFs in {section_name}")
            time.sleep(2)
        
        return all_pdfs
    
    def get_pdfs_from_page(self, url):
        """Get all PDF links from a page"""
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            pdf_links = []
            
            # Find all PDF links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.pdf') or 'pdf' in href.lower():
                    full_url = urljoin(self.base_url, href)
                    pdf_links.append({
                        'url': full_url,
                        'text': link.get_text(strip=True)
                    })
            
            return pdf_links
            
        except Exception as e:
            print(f"   ❌ Error scraping {url}: {e}")
            return []
    
    def download_all_pdfs(self, output_dir='scraped_pdfs'):
        """Download ALL PDFs from all sections"""
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        all_pdfs = self.scrape_all_sections()
        
        total_downloaded = 0
        
        for section, pdfs in all_pdfs.items():
            section_dir = os.path.join(output_dir, section)
            if not os.path.exists(section_dir):
                os.makedirs(section_dir)
            
            for i, pdf in enumerate(pdfs):
                try:
                    filename = f"{section}_{i+1}.pdf"
                    filepath = os.path.join(section_dir, filename)
                    
                    print(f"📥 Downloading: {pdf['text'][:50]}...")
                    
                    response = self.session.get(pdf['url'], timeout=30)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    total_downloaded += 1
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ Failed: {e}")
        
        print(f"\n🎉 Downloaded {total_downloaded} PDFs total!")
        return total_downloaded

if __name__ == "__main__":
    scraper = RGIPTScraper()
    scraper.download_all_pdfs()
