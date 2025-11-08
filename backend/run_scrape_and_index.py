#!/usr/bin/env python3
"""
Convenience script to scrape documents and index them.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from scrapers.rgipt_scraper_enhanced import RGIPTScraperEnhanced
from indexing_pipeline import IndexingPipeline

def main():
    print("\n" + "="*60)
    print("🚀 Campus Compass - Scrape and Index Pipeline")
    print("="*60 + "\n")
    
    # Step 1: Scrape documents
    print("📥 Step 1: Scraping documents from RGIPT website...")
    print("-" * 60)
    
    scraper = RGIPTScraperEnhanced(
        base_url="https://www.rgipt.ac.in",
        output_dir="data/documents",
        config_file="../scraper_config.json"
    )
    
    try:
        results = scraper.scrape_all()
        print(f"\n✅ Scraping complete!")
        print(f"   - Found: {results['total_found']} PDFs")
        print(f"   - Downloaded: {results['downloaded']} files")
        print(f"   - Failed: {results['failed']} files")
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")
        return 1
    
    # Step 2: Index documents
    print("\n" + "-" * 60)
    print("📚 Step 2: Indexing documents...")
    print("-" * 60)
    
    try:
        pipeline = IndexingPipeline()
        pipeline.index_all_documents(incremental=True, clear_existing=False)
        print("\n✅ Indexing complete!")
    except Exception as e:
        print(f"\n❌ Indexing failed: {e}")
        return 1
    
    print("\n" + "="*60)
    print("🎉 All done! Your AI is ready to answer questions.")
    print("="*60)
    print("\n💡 Next steps:")
    print("   1. Make sure the API server is running on port 2029")
    print("   2. Open http://localhost:2029 in your browser")
    print("   3. Ask questions about the documents!")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

