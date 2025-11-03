from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
import os
from urllib.parse import urljoin, urlparse
from datetime import datetime
import json

class RGIPTScraperAdvanced:
    def __init__(self, base_url="https://www.rgipt.ac.in", output_dir="data/documents"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.downloaded_files = []
        
        # Create directories
        os.makedirs(f"{output_dir}/pdfs", exist_ok=True)
        os.makedirs(f"{output_dir}/notices", exist_ok=True)
        os.makedirs(f"{output_dir}/metadata", exist_ok=True)
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run without opening browser
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize driver
        print("🔧 Setting up Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        print("✅ WebDriver ready!")
    
    def scrape_all(self):
        """Main scraping function"""
        print(f"\n🕷️ Starting RGIPT Advanced Scraper at {datetime.now().strftime('%H:%M:%S')}")
        print(f"🎯 Target: {self.base_url}\n")
        
        # Pages to scrape (based on RGIPT website structure)
        pages = [
            {"url": "/en", "name": "Home"},
            {"url": "/en/page/course-structure", "name": "Course Structure"},
            {"url": "/en/page/semester-fee-structure", "name": "Fee Structure"},
            {"url": "/en/page/academic-format", "name": "Academic Formats"},
            {"url": "/en/page/rules-regulations", "name": "Rules & Regulations"},
            {"url": "/en/page/student-academic-handbook", "name": "Student Handbook"},
            {"url": "/en/article/examination", "name": "Examination"},
            {"url": "/en/article/central-library", "name": "Library"},
            {"url": "/en/article/hostel-facilities", "name": "Hostel"},
            {"url": "/en/article/notifications", "name": "Notifications"},
        ]
        
        all_pdf_links = set()
        all_page_content = {}
        
        # Scrape each page
        for page_info in pages:
            page_url = urljoin(self.base_url, page_info["url"])
            print(f"📄 Scraping: {page_info['name']}")
            print(f"   URL: {page_url}")
            
            try:
                pdf_links, text_content = self.scrape_page(page_url)
                all_pdf_links.update(pdf_links)
                
                if text_content:
                    all_page_content[page_info['name']] = text_content
                
                time.sleep(2)  # Be respectful to server
                
            except Exception as e:
                print(f"   ⚠️ Error: {str(e)[:100]}")
                continue
        
        print(f"\n📊 Summary:")
        print(f"   Pages scraped: {len(all_page_content)}")
        print(f"   PDFs found: {len(all_pdf_links)}")
        
        # Download PDFs
        if all_pdf_links:
            print(f"\n📥 Downloading {len(all_pdf_links)} PDFs...")
            downloaded = 0
            for i, pdf_url in enumerate(all_pdf_links, 1):
                if self.download_pdf(pdf_url, i):
                    downloaded += 1
                time.sleep(1)
            
            print(f"\n✅ Successfully downloaded: {downloaded}/{len(all_pdf_links)} PDFs")
        
        # Save page content as text files
        if all_page_content:
            print(f"\n📝 Saving page content...")
            for page_name, content in all_page_content.items():
                self.save_text_content(page_name, content)
        
        # Save metadata
        self.save_metadata()
        
        # Cleanup
        self.driver.quit()
        
        print(f"\n🎉 Scraping complete!")
        print(f"📂 Files saved in: {self.output_dir}")
        
        return downloaded if all_pdf_links else len(all_page_content)
    
    def scrape_page(self, page_url):
        """Scrape a single page for PDFs and content"""
        self.driver.get(page_url)
        time.sleep(3)  # Wait for JavaScript to load
        
        pdf_links = set()
        
        # Method 1: Find all anchor tags with PDF links
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and '.pdf' in href.lower():
                        pdf_links.add(href)
                except:
                    continue
        except Exception as e:
            print(f"   ⚠️ Method 1 failed: {str(e)[:50]}")
        
        # Method 2: Find all elements with data attributes containing PDFs
        try:
            all_elements = self.driver.find_elements(By.XPATH, "//*[contains(@href, '.pdf') or contains(@data-src, '.pdf') or contains(@src, '.pdf')]")
            for element in all_elements:
                for attr in ['href', 'data-src', 'src']:
                    try:
                        url = element.get_attribute(attr)
                        if url and '.pdf' in url.lower():
                            pdf_links.add(url)
                    except:
                        continue
        except Exception as e:
            print(f"   ⚠️ Method 2 failed: {str(e)[:50]}")
        
        # Get page text content
        try:
            # Remove scripts and styles
            self.driver.execute_script("""
                var scripts = document.getElementsByTagName('script');
                for(var i = scripts.length - 1; i >= 0; i--) {
                    scripts[i].parentNode.removeChild(scripts[i]);
                }
                var styles = document.getElementsByTagName('style');
                for(var i = styles.length - 1; i >= 0; i--) {
                    styles[i].parentNode.removeChild(styles[i]);
                }
            """)
            
            text_content = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Clean up whitespace
            text_content = '\n'.join(line.strip() for line in text_content.split('\n') if line.strip())
            
        except:
            text_content = ""
        
        print(f"   ✓ Found {len(pdf_links)} PDFs")
        
        return pdf_links, text_content
    
    def download_pdf(self, pdf_url, index):
        """Download a single PDF"""
        try:
            # Make absolute URL
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(self.base_url, pdf_url)
            
            # Download with timeout
            response = requests.get(pdf_url, timeout=20, stream=True)
            response.raise_for_status()
            
            # Generate filename
            parsed = urlparse(pdf_url)
            original_name = os.path.basename(parsed.path)
            
            # Clean filename
            if original_name and original_name.endswith('.pdf'):
                filename = original_name
            else:
                filename = f"document_{index}.pdf"
            
            # Remove invalid characters from filename
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
            
            # Determine folder
            folder = "notices" if "notice" in pdf_url.lower() or "notification" in pdf_url.lower() else "pdfs"
            filepath = os.path.join(self.output_dir, folder, filename)
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(filepath) / 1024  # KB
            
            # Track downloaded file
            self.downloaded_files.append({
                "filename": filename,
                "url": pdf_url,
                "size_kb": round(file_size, 2),
                "category": folder,
                "downloaded_at": datetime.now().isoformat()
            })
            
            print(f"   ✅ {filename} ({file_size:.1f} KB)")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:80]}")
            return False
    
    def save_text_content(self, page_name, content):
        """Save scraped text content"""
        # Clean page name for filename
        filename = page_name.lower().replace(' ', '_').replace('&', 'and')
        filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-'))
        filename = f"{filename}_content.txt"
        
        filepath = os.path.join(self.output_dir, "pdfs", filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {page_name}\n\n")
                f.write(content)
            
            print(f"   ✅ Saved: {filename}")
            
            # Track saved content
            self.downloaded_files.append({
                "filename": filename,
                "url": "webpage_content",
                "size_kb": len(content) / 1024,
                "category": "text",
                "downloaded_at": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"   ❌ Failed to save {filename}: {e}")
    
    def save_metadata(self):
        """Save metadata about downloaded files"""
        metadata = {
            "scrape_date": datetime.now().isoformat(),
            "total_files": len(self.downloaded_files),
            "files": self.downloaded_files
        }
        
        filepath = os.path.join(self.output_dir, "metadata", "scrape_metadata.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n📋 Metadata saved: {filepath}")


def main():
    """Main execution function"""
    print("=" * 60)
    print("    RGIPT ADVANCED WEB SCRAPER")
    print("    Powered by Selenium + ChromeDriver")
    print("=" * 60)
    
    scraper = RGIPTScraperAdvanced()
    
    try:
        files_downloaded = scraper.scrape_all()
        
        print("\n" + "=" * 60)
        print(f"✅ SUCCESS! Downloaded {files_downloaded} files")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("Check your internet connection and try again.")
    
    finally:
        # Ensure browser is closed
        try:
            scraper.driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()
