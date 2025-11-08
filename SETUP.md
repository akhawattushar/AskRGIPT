# Campus Compass Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note:** For OCR support, you may need to install additional system dependencies:
- **PaddleOCR**: Requires PaddlePaddle (automatically installed via pip)
- **Tesseract OCR**: Requires system installation
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your OpenAI API key:

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Scrape Documents

Add your PDF links to `scraper_config.json`:

```json
{
  "target_urls": [
    {
      "url": "https://www.rgipt.ac.in/en/page/institute-policies",
      "category": "policies",
      "description": "Institute Policies",
      "use_selenium": true
    }
  ],
  "direct_pdf_links": [
    {
      "url": "https://example.com/policy.pdf",
      "category": "policies"
    }
  ]
}
```

Run the scraper:

```bash
cd backend
python scrapers/rgipt_scraper_enhanced.py
```

### 4. Process and Index Documents

```bash
cd backend
python indexing_pipeline.py
```

Or for a full re-index:

```bash
python indexing_pipeline.py --full
```

### 5. Start the API Server

```bash
cd backend
python api/main.py
```

Or using uvicorn directly:

```bash
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 6. Open the Frontend

Open `frontend/index.html` in your browser, or serve it using a simple HTTP server:

```bash
cd frontend
python -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

**Note:** Update `API_BASE_URL` in `frontend/app.js` if your API is running on a different port.

## Usage

### Scraping Documents

The enhanced scraper supports:
- Configuration file with target URLs
- Direct PDF links
- Automatic category detection
- Metadata tracking
- Retry logic

### Processing Documents

The document processor:
- Supports PDF, DOCX, HTML, TXT files
- Automatically detects scanned PDFs and uses OCR
- Uses semantic chunking for better context preservation
- Tracks metadata (source, page, category, OCR confidence)

### Querying

You can query the system via:
1. **Web Interface**: Open `frontend/index.html`
2. **API**: POST to `/chat` endpoint
3. **WebSocket**: Connect to `/ws` endpoint

### Function Calling

The system automatically routes queries to appropriate functions:
- Policy searches → `search_policies()`
- Fee queries → `get_fee_structure()`
- Calendar queries → `get_academic_calendar()`
- Policy summaries → `summarize_policy()`
- Policy comparisons → `compare_policies()`

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /chat` - Chat endpoint
- `POST /chat/stream` - Streaming chat
- `WebSocket /ws` - WebSocket chat
- `POST /search` - Direct search
- `GET /functions` - List available functions
- `GET /documents` - List indexed documents
- `POST /index` - Trigger indexing

## Troubleshooting

### OCR Not Working

1. Ensure PaddleOCR or Tesseract is installed
2. Check OCR_ENGINE in `.env` (paddleocr or tesseract)
3. For PaddleOCR, first run may download models (wait a few minutes)

### Selenium Issues

If Selenium fails:
1. Install Chrome/Chromium browser
2. ChromeDriver is auto-installed via webdriver-manager
3. For headless mode, ensure display is available (or use --headless)

### API Connection Errors

1. Ensure backend is running on correct port
2. Check CORS settings in `api/main.py`
3. Update `API_BASE_URL` in `frontend/app.js`

## Next Steps

- Fine-tuning pipeline (optional)
- Evaluation framework
- Monitoring and logging
- Docker deployment

