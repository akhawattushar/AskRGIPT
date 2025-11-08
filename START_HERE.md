# 🚀 Quick Start Guide - Scrape and Index Documents

## Problem: "I couldn't find fee structure information"

You need to download and index documents first! Here's how:

## Option 1: Automated Script (Easiest)

```bash
cd backend
python3 run_scrape_and_index.py
```

This will:
1. ✅ Scrape PDFs from RGIPT website
2. ✅ Index them for the AI
3. ✅ Show progress and logs

## Option 2: Manual Steps

### Step 1: Add PDF Links

Edit `scraper_config.json` and add your PDF URLs. You mentioned you have specific links - add them here:

```json
{
  "direct_pdf_links": [
    {
      "url": "https://www.rgipt.ac.in/path/to/fee-structure.pdf",
      "category": "pdfs"
    },
    {
      "url": "https://www.rgipt.ac.in/path/to/policy.pdf",
      "category": "policies"
    }
  ]
}
```

### Step 2: Run Scraper

```bash
cd backend
python3 scrapers/rgipt_scraper_enhanced.py
```

**Logs are saved to:**
- Console output (real-time)
- `backend/scraper.log` (detailed log file)

### Step 3: Index Documents

```bash
cd backend
python3 indexing_pipeline.py
```

## Checking Progress

### View logs:
```bash
tail -f backend/scraper.log
```

### Check downloaded files:
```bash
ls -la data/documents/*/
```

### Check indexed documents:
```bash
curl http://localhost:2029/documents
```

## Troubleshooting

### If scraper finds 0 PDFs:

1. **Pages need JavaScript**: Install Selenium dependencies:
   ```bash
   pip install selenium webdriver-manager
   ```
   The scraper will automatically use Selenium for pages marked `"use_selenium": true`

2. **Direct PDF links**: If you have direct PDF URLs, add them to `direct_pdf_links` in the config

3. **Check website structure**: The PDFs might be:
   - In iframes
   - Loaded via JavaScript
   - Behind login (needs authentication)

### If indexing fails:

- Check that PDFs are in `data/documents/` folders
- Ensure PDFs are not corrupted
- Check `backend/indexing_pipeline.py` output for errors

## What the Scraper Does

1. ✅ Reads `scraper_config.json`
2. ✅ Visits each URL in `target_urls`
3. ✅ Finds all PDF links on the page
4. ✅ Downloads PDFs to appropriate folders
5. ✅ Saves metadata about downloads
6. ✅ Logs everything to `scraper.log`

## After Scraping

Once documents are indexed, your AI will be able to answer questions like:
- "What is the fee structure?"
- "What are the library rules?"
- "Summarize the academic policy"

**The AI is already running on port 2029 - just add the documents!**

