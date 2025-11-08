# How to Scrape and Index Documents

## Step 1: Configure Scraper

Edit `scraper_config.json` and add your PDF links:

```json
{
  "target_urls": [
    {
      "url": "https://www.rgipt.ac.in/en/page/institute-policies",
      "category": "policies",
      "description": "Institute Policies",
      "use_selenium": true
    },
    {
      "url": "https://www.rgipt.ac.in/en/page/semester-fee-structure",
      "category": "pdfs",
      "description": "Fee Structure",
      "use_selenium": true
    }
  ],
  "direct_pdf_links": [
    {
      "url": "https://www.rgipt.ac.in/path/to/fee-structure.pdf",
      "category": "pdfs"
    }
  ]
}
```

## Step 2: Run the Scraper

```bash
cd backend
python3 scrapers/rgipt_scraper_enhanced.py
```

This will:
- Download PDFs from the configured URLs
- Save them to `data/documents/` (organized by category)
- Create metadata in `data/documents/metadata/scrape_metadata.json`
- Log progress to `scraper.log` and console

## Step 3: Index the Documents

After scraping, index the documents:

```bash
cd backend
python3 indexing_pipeline.py
```

Or for a full re-index:

```bash
python3 indexing_pipeline.py --full
```

## Step 4: Verify

Check how many documents are indexed:

```bash
curl http://localhost:2029/documents
```

Or check the health endpoint:

```bash
curl http://localhost:2029/health
```

## Logs

- Scraper logs: `backend/scraper.log`
- Console output: Shows real-time progress

## Troubleshooting

If scraping fails:
1. Check `scraper.log` for errors
2. Ensure you have internet connection
3. For Selenium pages, ensure Chrome/Chromium is installed
4. Check if URLs are accessible

