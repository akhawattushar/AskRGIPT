import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import time
from datetime import datetime

class RGIPTScraper:
    def __init__(self, base_url="https://www.rgipt.ac.in", output_dir="data/documents"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        os.makedirs(f"{output_dir}/pdfs", exist_ok=True)
        os.makedirs(f"{output_dir}/notices", exist_ok=True)
        
    def scrape_all(self):
        print(f"🕷️ Starting RGIPT scraper at {datetime.now().strftime('%H:%M:%S')}")
        
        pages = ["/students", "/academics", "/notices", "/examination"]
        all_pdf_links = set()
        
        for page in pages:
            print(f"📄 Scraping {page}...")
            try:
                pdf_links = self.scrape_page(page)
                all_pdf_links.update(pdf_links)
                time.sleep(1)
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print(f"\n📥 Found {len(all_pdf_links)} PDFs. Downloading...")
        
        downloaded = 0
        for i, pdf_url in enumerate(all_pdf_links, 1):
            if self.download_pdf(pdf_url, i):
                downloaded += 1
            time.sleep(0.5)
        
        print(f"\n✅ Downloaded {downloaded}/{len(all_pdf_links)} files")
        return downloaded
    
    def scrape_page(self, page_path):
        url = urljoin(self.base_url, page_path)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        pdf_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '.pdf' in href.lower():
                if not href.startswith('http'):
                    href = urljoin(self.base_url, href)
                pdf_links.append(href)
        
        print(f"   Found {len(pdf_links)} PDFs")
        return pdf_links
    
    def download_pdf(self, pdf_url, index):
        try:
            response = self.session.get(pdf_url, timeout=15)
            response.raise_for_status()
            
            filename = f"document_{index}.pdf"
            folder = "notices" if "notice" in pdf_url.lower() else "pdfs"
            filepath = os.path.join(self.output_dir, folder, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"   ✅ {filename}")
            return True
            
        except:
            return False

if __name__ == "__main__":
    scraper = RGIPTScraper()
    scraper.scrape_all()
