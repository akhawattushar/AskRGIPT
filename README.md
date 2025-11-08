# Campus Compass — The AI Oracle for Your College
Problem Statement 3

A Retrieval-Augmented Generation (RAG) chatbot that serves as a single source of truth for college-related queries. Campus Compass finds precise answers from official documents and presents them clearly, with citations.

---

## Table of Contents
- [Vision](#vision)
- [Challenge](#challenge)
- [Core Modules](#core-modules)
  - [1. Taming the Knowledge Beast](#1-taming-the-knowledge-beast)
  - [2. Building the "Brain": The Vector Knowledge Core](#2-building-the-brain-the-vector-knowledge-core)
  - [3. The Oracle Interface: Ask Anything, Get Answers](#3-the-oracle-interface-ask-anything-get-answers)
- [Trust & Citations](#trust--citations)
- [Bonus Ideas (The "Wow" Factor)](#bonus-ideas-the-wow-factor)
- [Suggested Implementation Steps](#suggested-implementation-steps)
- [Example Interaction](#example-interaction)
- [Next Steps / Contribution](#next-steps--contribution)

---

## Vision
Every student knows the pain: a simple question about college policy (e.g., "What's the fine for a late library book?") sends you down a rabbit hole of broken links, 100-page PDFs, and outdated websites. The official information exists, but it's trapped in a digital labyrinth.

Campus Compass aims to be the single, trustworthy AI assistant for all college-related queries — fast, accurate, and source-citing.

## Challenge
Slay the bureaucracy dragon! Build Campus Compass using a RAG architecture so the bot retrieves relevant official content and only answers based on those documents.

---

## Core Modules

### 1. Taming the Knowledge Beast:
- The Source Material
  - Collect a corpus of official documents: student handbook, academic calendar, library rules, fee structure, hostel regulations, syllabi, policy PDFs, memos, etc.
- The Processing Pipeline
  - Ingest file types: PDF, DOCX, TXT, HTML, etc.
  - Clean and normalize text (remove headers/footers, de-duplicate).
  - Split documents into logical chunks (paragraphs or semantic segments).
  - Optionally track metadata (source filename, section, page number).

### 2. Building the "Brain": The Vector Knowledge Core
- Embedding Generation
  - Use a high-quality sentence-transformer or embedding model to convert each chunk into a vector.
- Vector Database
  - Store embeddings in a vector store like ChromaDB, FAISS, or Pinecone for fast semantic retrieval.
  - Keep source metadata alongside embeddings to enable precise citations.

### 3. The Oracle Interface: Ask Anything, Get Answers
- RAG Pipeline (high-level)
  1. Convert the user's question into an embedding.
  2. Retrieve the most relevant document chunks from the vector DB.
  3. Provide those chunks as context to an LLM together with the original question.
- Trustworthy Responses
  - The LLM should be constrained to answer only from provided context.
  - Require the model to include citations (e.g., "According to the Student Handbook 2025, page 42...").

---

## Trust & Citations
- Always prefer direct quotes from the retrieved chunks when possible.
- Include source metadata (document title, section, page or paragraph ID).
- If the model cannot find an authoritative answer, reply with a safe fallback such as:
  - "I couldn't find an authoritative answer in the available documents. Would you like me to search more sources or connect you to an admin?"

---

## Bonus Ideas (The "Wow" Factor)
- Multi-Document Synthesis
  - Answer complex questions that require merging information across multiple documents (e.g., drop date + financial penalty combines Academic Calendar + Fee Structure).
- Policy Summarizer (TL;DR)
  - Generate concise, bulleted summaries for long policies (e.g., plagiarism policy).
- Personalized Alerts
  - Opt-in alerts tied to the academic calendar: registration deadlines, fee due dates, exam schedules.
- Role-based Responses
  - Provide different levels of detail for students, faculty, or admin users.

---

## Suggested Implementation Steps
1. Collect and catalog official documents and metadata.
2. Build ingestion pipeline (parsing, cleaning, chunking).
3. Generate embeddings for chunks and populate a vector store.
4. Implement a retrieval layer with configurable similarity thresholds.
5. Integrate with an LLM and design prompts that force context-limited answers + citation format.
6. Create a simple front-end/chat interface (web, mobile, or campus LMS integration).
7. Add testing and evaluation: QA with sample queries and ground-truth citations.
8. Add monitoring to detect hallucinations and stale documents.

---

## Example Interaction
User: "What's the last day to drop a course, and what's the financial penalty for doing so?"
System flow:
1. Convert the question to an embedding.
2. Retrieve relevant chunks from Academic Calendar and Fee Structure.
3. LLM generates a synthesized answer with citations:
   - "According to the Academic Calendar 2025, the last day to drop a course without academic penalty is July 15. According to the Fee Structure document, dropping after July 1 incurs a 50% refund penalty."

---

## Implementation Status

### ✅ Completed Features

1. **Enhanced Document Scraper** (`backend/scrapers/rgipt_scraper_enhanced.py`)
   - Configuration-based scraping with JSON config
   - Support for direct PDF links and pages containing PDFs
   - Selenium integration for dynamic content
   - Metadata tracking and category classification

2. **OCR Support** (`backend/ocr/`)
   - PaddleOCR and Tesseract OCR integration
   - Image preprocessing (deskew, denoise, enhance contrast)
   - Automatic detection of scanned vs text-based PDFs

3. **Enhanced Document Processor** (`backend/document_processor.py`)
   - Support for PDF, DOCX, HTML, TXT files
   - Semantic chunking with langchain
   - OCR integration for scanned documents
   - Metadata preservation (source, page, category, OCR confidence)

4. **Enhanced Vector Store** (`backend/vector_store.py`)
   - ChromaDB with sentence-transformers
   - Hybrid search (semantic + keyword)
   - Re-ranking with cross-encoder models
   - Metadata filtering

5. **RAG Engine** (`backend/rag_engine.py`)
   - LLM integration (OpenAI GPT-3.5/4)
   - Citation extraction and formatting
   - Hallucination prevention
   - Context-limited responses

6. **Function Calling System** (`backend/function_calling.py`)
   - Structured query handlers (policies, fees, calendar)
   - Policy summarization
   - Policy comparison

7. **Query Router** (`backend/query_router.py`)
   - Intent classification
   - Automatic routing to functions or general RAG
   - Parameter extraction from natural language

8. **FastAPI Backend** (`backend/api/`)
   - RESTful API endpoints
   - WebSocket support for real-time chat
   - Streaming responses
   - Request/response validation

9. **Web Frontend** (`frontend/`)
   - Modern chat interface
   - Citation display
   - Function call indicators
   - Responsive design

### 🚧 Optional Features (Not Yet Implemented)

- Fine-tuning pipeline for RGIPT-specific model training
- Comprehensive test suite and evaluation framework
- Advanced monitoring and logging
- Docker Compose deployment configuration

## Quick Start

See [SETUP.md](SETUP.md) for detailed setup instructions.

### Basic Setup

1. Install dependencies: `pip install -r backend/requirements.txt`
2. Configure `.env` with your OpenAI API key
3. Add PDF links to `scraper_config.json`
4. Run scraper: `python backend/scrapers/rgipt_scraper_enhanced.py`
5. Index documents: `python backend/indexing_pipeline.py`
6. Start API: `python backend/api/main.py`
7. Open `frontend/index.html` in browser

## API Documentation

Once the API is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Contribution

To contribute:
1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

---