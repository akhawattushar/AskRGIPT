"""
Enhanced RGIPT Scraper
Accepts provided links and downloads PDFs with comprehensive metadata tracking.
Supports both direct PDF links and pages containing PDF links.
"""
import requests
from bs4 import BeautifulSoup
import os
import json
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
from typing import List, Dict, Set, Optional
import re
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not available. Will use requests-only mode for dynamic content.")


class RGIPTScraperEnhanced:
    def __init__(self, base_url="https://www.rgipt.ac.in", output_dir="data/documents", config_file=None):
        """
        Initialize enhanced scraper.
        
        Args:
            base_url: Base URL for RGIPT website
            output_dir: Directory to save downloaded PDFs
            config_file: Path to JSON config file with target URLs (optional)
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.config_file = config_file or "scraper_config.json"
        
        # Create output directories
        os.makedirs(f"{output_dir}/pdfs", exist_ok=True)
        os.makedirs(f"{output_dir}/notices", exist_ok=True)
        os.makedirs(f"{output_dir}/policies", exist_ok=True)
        os.makedirs(f"{output_dir}/handbooks", exist_ok=True)
        os.makedirs(f"{output_dir}/metadata", exist_ok=True)
        
        # Setup requests session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Track downloaded files
        self.downloaded_files = []
        self.failed_downloads = []
        
        # Selenium driver (lazy initialization)
        self.driver = None
        self.use_selenium = SELENIUM_AVAILABLE
        
        # Rate limiting
        self.min_delay = 1.0  # Minimum delay between requests (seconds)
        self.max_retries = 3
        
    def _init_selenium(self):
        """Initialize Selenium WebDriver if available."""
        if not self.use_selenium or self.driver:
            return
        
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Selenium WebDriver initialized")
        except Exception as e:
            print(f"⚠️ Failed to initialize Selenium: {e}")
            self.use_selenium = False
    
    def _cleanup_selenium(self):
        """Close Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def load_config(self) -> Dict:
        """Load scraper configuration from JSON file."""
        if not os.path.exists(self.config_file):
            # Create default config file
            default_config = {
                "target_urls": [
                    {
                        "url": "https://www.rgipt.ac.in/en/page/institute-policies",
                        "category": "policies",
                        "description": "Institute Policies"
                    }
                ],
                "direct_pdf_links": [],
                "categories": {
                    "policies": "policies",
                    "notices": "notices",
                    "handbooks": "handbooks",
                    "fees": "pdfs",
                    "academic": "pdfs"
                }
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            print(f"📝 Created default config file: {self.config_file}")
            return default_config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ Loaded config from {self.config_file}")
            return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return {"target_urls": [], "direct_pdf_links": []}
    
    def _determine_category(self, url: str, filename: str, default: str = "pdfs") -> str:
        """Determine document category based on URL and filename."""
        url_lower = url.lower()
        filename_lower = filename.lower()
        
        # Check for category keywords
        if any(keyword in url_lower or keyword in filename_lower for keyword in ["policy", "policies", "regulation", "rule"]):
            return "policies"
        elif any(keyword in url_lower or keyword in filename_lower for keyword in ["notice", "notification", "announcement"]):
            return "notices"
        elif any(keyword in url_lower or keyword in filename_lower for keyword in ["handbook", "manual", "guide"]):
            return "handbooks"
        elif any(keyword in url_lower or keyword in filename_lower for keyword in ["fee", "fees", "payment"]):
            return "pdfs"
        
        return default
    
    def _find_pdf_links_requests(self, url: str) -> Set[str]:
        """Find PDF links using requests and BeautifulSoup."""
        pdf_links = set()
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '.pdf' in href.lower():
                    if not href.startswith('http'):
                        href = urljoin(url, href)
                    pdf_links.add(href)
            
            # Check for embedded PDFs in iframes
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src', '')
                if '.pdf' in src.lower():
                    if not src.startswith('http'):
                        src = urljoin(url, src)
                    pdf_links.add(src)
            
            # Check for PDFs in data attributes
            for element in soup.find_all(attrs={'data-src': True}):
                data_src = element.get('data-src', '')
                if '.pdf' in data_src.lower():
                    if not data_src.startswith('http'):
                        data_src = urljoin(url, data_src)
                    pdf_links.add(data_src)
                    
        except Exception as e:
            print(f"   ⚠️ Error scraping {url}: {e}")
        
        return pdf_links
    
    def _find_pdf_links_selenium(self, url: str) -> Set[str]:
        """Find PDF links using Selenium (for dynamic content)."""
        pdf_links = set()
        
        if not self.use_selenium:
            return pdf_links
        
        try:
            self._init_selenium()
            self.driver.get(url)
            time.sleep(3)  # Wait for JavaScript to load
            
            # Method 1: Find all anchor tags
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and '.pdf' in href.lower():
                        pdf_links.add(href)
                except:
                    continue
            
            # Method 2: XPath search for PDFs
            try:
                elements = self.driver.find_elements(By.XPATH, 
                    "//*[contains(@href, '.pdf') or contains(@data-src, '.pdf') or contains(@src, '.pdf')]")
                for element in elements:
                    for attr in ['href', 'data-src', 'src']:
                        try:
                            url_attr = element.get_attribute(attr)
                            if url_attr and '.pdf' in url_attr.lower():
                                pdf_links.add(url_attr)
                        except:
                            continue
            except:
                pass
            
            # Method 3: Check iframes
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    src = iframe.get_attribute("src")
                    if src and '.pdf' in src.lower():
                        pdf_links.add(src)
            except:
                pass
                
        except Exception as e:
            print(f"   ⚠️ Selenium error on {url}: {e}")
        
        return pdf_links
    
    def scrape_url(self, url: str, category: Optional[str] = None, use_selenium: bool = False) -> Set[str]:
        """
        Scrape a single URL for PDF links.
        
        Args:
            url: URL to scrape
            category: Document category (optional)
            use_selenium: Force use of Selenium even if requests works
            
        Returns:
            Set of PDF URLs found
        """
        print(f"📄 Scraping: {url}")
        
        pdf_links = set()
        
        # Try requests first (faster)
        if not use_selenium:
            pdf_links = self._find_pdf_links_requests(url)
            if pdf_links:
                print(f"   ✓ Found {len(pdf_links)} PDFs (requests)")
        
        # Use Selenium if requested or if requests found nothing
        if use_selenium or (not pdf_links and self.use_selenium):
            selenium_links = self._find_pdf_links_selenium(url)
            pdf_links.update(selenium_links)
            if selenium_links:
                print(f"   ✓ Found {len(selenium_links)} additional PDFs (Selenium)")
        
        time.sleep(self.min_delay)  # Rate limiting
        
        return pdf_links
    
    def download_pdf(self, pdf_url: str, category: Optional[str] = None, retry_count: int = 0) -> bool:
        """
        Download a single PDF file.
        
        Args:
            pdf_url: URL of the PDF to download
            category: Document category (auto-detected if not provided)
            retry_count: Current retry attempt
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            # Make absolute URL
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(self.base_url, pdf_url)
            
            # Download with timeout
            response = self.session.get(pdf_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check if it's actually a PDF
            content_type = response.headers.get('Content-Type', '').lower()
            if 'pdf' not in content_type and not pdf_url.lower().endswith('.pdf'):
                print(f"   ⚠️ Skipping non-PDF: {pdf_url} (Content-Type: {content_type})")
                return False
            
            # Generate filename
            parsed = urlparse(pdf_url)
            original_name = os.path.basename(parsed.path)
            
            if original_name and original_name.endswith('.pdf'):
                filename = original_name
            else:
                # Generate filename from URL
                filename = re.sub(r'[^\w\-_\.]', '_', parsed.path.split('/')[-1])
                if not filename.endswith('.pdf'):
                    filename = f"{filename}.pdf"
            
            # Clean filename
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
            filename = filename.strip()
            
            # Determine category
            if not category:
                category = self._determine_category(pdf_url, filename)
            
            folder_path = os.path.join(self.output_dir, category)
            os.makedirs(folder_path, exist_ok=True)
            
            filepath = os.path.join(folder_path, filename)
            
            # Skip if file already exists
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath) / 1024
                print(f"   ⏭️  Skipping (exists): {filename} ({file_size:.1f} KB)")
                return True
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(filepath) / 1024  # KB
            
            # Track downloaded file
            file_info = {
                "filename": filename,
                "url": pdf_url,
                "size_kb": round(file_size, 2),
                "category": category,
                "downloaded_at": datetime.now().isoformat(),
                "filepath": filepath
            }
            self.downloaded_files.append(file_info)
            
            print(f"   ✅ {filename} ({file_size:.1f} KB)")
            return True
            
        except requests.exceptions.RequestException as e:
            if retry_count < self.max_retries:
                print(f"   🔄 Retrying ({retry_count + 1}/{self.max_retries}): {pdf_url}")
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self.download_pdf(pdf_url, category, retry_count + 1)
            else:
                print(f"   ❌ Failed after {self.max_retries} retries: {pdf_url}")
                self.failed_downloads.append({"url": pdf_url, "error": str(e)})
                return False
        except Exception as e:
            print(f"   ❌ Error downloading {pdf_url}: {str(e)[:80]}")
            self.failed_downloads.append({"url": pdf_url, "error": str(e)})
            return False
    
    def scrape_all(self, config: Optional[Dict] = None) -> Dict:
        """
        Main scraping function.
        
        Args:
            config: Configuration dictionary (if None, loads from file)
            
        Returns:
            Dictionary with scraping results
        """
        logger.info("="*60)
        logger.info("🕷️  RGIPT Enhanced Scraper")
        logger.info(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        print(f"\n{'='*60}")
        print(f"🕷️  RGIPT Enhanced Scraper")
        print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        if config is None:
            config = self.load_config()
        
        all_pdf_links = set()
        
        # Process target URLs (pages containing PDFs)
        target_urls = config.get("target_urls", [])
        logger.info(f"Found {len(target_urls)} target URLs to scrape")
        for target in target_urls:
            url = target.get("url", "")
            category = target.get("category")
            use_selenium = target.get("use_selenium", False)
            
            if url:
                logger.info(f"Scraping URL: {url} (category: {category})")
                pdf_links = self.scrape_url(url, category, use_selenium)
                logger.info(f"Found {len(pdf_links)} PDF links from {url}")
                all_pdf_links.update(pdf_links)
        
        # Add direct PDF links from config
        direct_links = config.get("direct_pdf_links", [])
        for link_info in direct_links:
            if isinstance(link_info, str):
                all_pdf_links.add(link_info)
            elif isinstance(link_info, dict):
                all_pdf_links.add(link_info.get("url", ""))
        
        print(f"\n📊 Summary:")
        print(f"   Total PDFs found: {len(all_pdf_links)}")
        
        # Download PDFs
        if all_pdf_links:
            print(f"\n📥 Downloading {len(all_pdf_links)} PDFs...")
            downloaded = 0
            skipped = 0
            
            for i, pdf_url in enumerate(all_pdf_links, 1):
                print(f"\n[{i}/{len(all_pdf_links)}] ", end="")
                if self.download_pdf(pdf_url):
                    downloaded += 1
                else:
                    skipped += 1
                time.sleep(self.min_delay)
            
            print(f"\n✅ Successfully downloaded: {downloaded}/{len(all_pdf_links)}")
            if skipped > 0:
                print(f"⚠️  Skipped/Failed: {skipped}")
        
        # Save metadata
        self.save_metadata()
        
        # Cleanup
        self._cleanup_selenium()
        
        print(f"\n{'='*60}")
        print(f"🎉 Scraping complete!")
        print(f"📂 Files saved in: {self.output_dir}")
        print(f"{'='*60}\n")
        
        return {
            "total_found": len(all_pdf_links),
            "downloaded": len(self.downloaded_files),
            "failed": len(self.failed_downloads),
            "files": self.downloaded_files
        }
    
    def save_metadata(self):
        """Save metadata about downloaded files."""
        metadata = {
            "scrape_date": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_files": len(self.downloaded_files),
            "failed_downloads": len(self.failed_downloads),
            "files": self.downloaded_files,
            "failed": self.failed_downloads
        }
        
        filepath = os.path.join(self.output_dir, "metadata", "scrape_metadata.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Metadata saved: {filepath}")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RGIPT Enhanced PDF Scraper")
    parser.add_argument("--config", type=str, default="scraper_config.json",
                       help="Path to configuration JSON file")
    parser.add_argument("--output", type=str, default="data/documents",
                       help="Output directory for downloaded PDFs")
    parser.add_argument("--base-url", type=str, default="https://www.rgipt.ac.in",
                       help="Base URL for RGIPT website")
    
    args = parser.parse_args()
    
    scraper = RGIPTScraperEnhanced(
        base_url=args.base_url,
        output_dir=args.output,
        config_file=args.config
    )
    
    try:
        results = scraper.scrape_all()
        print(f"\n✅ Success! Downloaded {results['downloaded']} files")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper._cleanup_selenium()


if __name__ == "__main__":
    main()

