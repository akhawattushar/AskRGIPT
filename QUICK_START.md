# Quick Start - Using Campus Compass AI

## 🎯 The AI is Ready, But You Need Documents!

Your API is running on **port 2029**, but you need to add documents first. Here's how:

## Step 1: Add PDF Links

Edit `scraper_config.json` and add your PDF links:

```json
{
  "target_urls": [
    {
      "url": "https://www.rgipt.ac.in/en/page/institute-policies",
      "category": "policies",
      "use_selenium": true
    }
  ],
  "direct_pdf_links": [
    {
      "url": "https://example.com/your-policy.pdf",
      "category": "policies"
    }
  ]
}
```

## Step 2: Download PDFs

```bash
cd backend
python3 scrapers/rgipt_scraper_enhanced.py
```

## Step 3: Index Documents

```bash
cd backend
python3 indexing_pipeline.py
```

## Step 4: Use the AI!

### Option A: Web Interface (Easiest)
1. Open `frontend/index.html` in your browser
2. Or serve it: `cd frontend && python3 -m http.server 8080`
3. Open `http://localhost:8080`

### Option B: API Directly
```bash
curl -X POST http://localhost:2029/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the library rules?"}'
```

### Option C: API Documentation
Visit: http://localhost:2029/docs

## Current Status
- ✅ API Server: Running on port 2029
- ✅ OpenAI API Key: Set
- ⚠️ Documents: 0 indexed (need to download and index)

