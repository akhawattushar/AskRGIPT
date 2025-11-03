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

## Next Steps / Contribution
- Want this added to the repository as README.md? I can create/update the file for you.
- Suggestions welcome: desired LLM provider, preferred vector DB, or example documents to include.
- To contribute: fork the repo, implement ingestion or retrieval modules, add unit tests, and open a PR.

---