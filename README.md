Problem Statement 3: Campus Compass - The AI Oracle for Your College
The Vision
Every student knows the pain: a simple question about college policy ("What's the fine for a late
library book?") sends you down a rabbit hole of broken links, 100-page PDFs, and outdated
websites. The official information exists, but it's trapped in a digital labyrinth.
The Challenge: Slay the bureaucracy dragon! Build Campus Compass, an AI-powered
chatbot that serves as the single source of truth for all college-related queries. Using a
Retrieval-Augmented Generation (RAG) model, your bot won't make things up; it will find the
precise answer from official documents and present it clearly, saving students time and
frustration.
Core Modules
1. Taming the Knowledge Beast:
● The Source Material: Gather a corpus of official documents: the student handbook,
academic calendar, library rules, fee structures, hostel regulations, etc.
● The Processing Pipeline: Build a robust pipeline to ingest these documents (PDFs,
DOCX, TXT), clean the text, and split them into logical, indexed chunks.
2. Building the 'Brain': The Vector Knowledge Core:
● Embedding Generation: Use a high-quality sentence-transformer model to convert
every document chunk into a meaningful vector embedding.
● The Vector Database: Store these embeddings in an efficient vector database (like
ChromaDB, FAISS, or Pinecone) that allows for lightning-fast semantic searches.
3. The Oracle Interface: Ask Anything, Get Answers:
● The RAG Pipeline: When a student asks a question, your system will:
1. Convert the question into a vector.
2. Search the vector database to retrieve the most relevant document chunks.
3. Feed these chunks and the original question as context to an LLM.
● Trustworthy Responses: The LLM's primary instruction is to generate an answer
based only on the provided context and to cite its sources (e.g., "According to the
Student Handbook 2025, page 42...").
The 'Wow' Factor (Bonus Ideas):
● Multi-Document Synthesis: Train the bot to answer complex questions that require
information from multiple sources. Example: "What's the last day to drop a course, and what's the financial penalty for doing so?" (This might involve the Academic Calendar
and the Fee Structure document).
● The Policy Summarizer (TL;DR): Add a feature where a user can ask, "Summarize the
college's policy on plagiarism," and the bot provides a concise, bulleted summary.
● Personalized Alerts: Allow users to opt-in for alerts based on the academic calendar,
such as reminders for registration deadlines or upcoming fee payments.