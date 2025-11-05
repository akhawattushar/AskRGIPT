# 🎓 AskRGIPT - AI Assistant for RGIPT Students

Your intelligent companion for all RGIPT-related queries using advanced RAG (Retrieval-Augmented Generation) technology.

![AskRGIPT Demo](screenshots/demo.png)

**Live Demo:** [Coming Soon]

---

## ✨ Features

- 🤖 **Smart AI Responses** - Powered by Groq LLM (Llama 3.1 70B)
- 🌐 **Real-time Web Scraping** - Always current RGIPT official info
- 📚 **Multi-source Knowledge** - Official RGIPT pages + documents
- 🎨 **Beautiful UI** - Modern gradient chat interface
- 📜 **Query History** - Track and revisit your questions
- ⚡ **Fast & Accurate** - Hybrid RAG architecture
- 🔍 **Multi-format Support** - Handles PDF, DOCX, and TXT files

---

## 🎯 What Can AskRGIPT Answer?

AskRGIPT provides detailed, accurate answers about:

- 📖 **Library hours & facilities** - Operational hours (10 AM - 12 midnight!), resources, digital libraries
- 🎓 **Admission requirements** - Eligibility, application process, entrance exams
- 🏢 **Hostel information** - Facilities, allocation, rules
- 📝 **Examination rules** - Schedules, guidelines, policies
- 💰 **Fee structure** - Tuition, hostel fees, payment deadlines
- 🎯 **Academic programs** - Courses offered, curriculum details

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** `0.115.4` - Modern Python web framework
- **ChromaDB** `0.5.15` - Vector database for semantic search
- **Sentence Transformers** `3.2.1` - Document embeddings (all-MiniLM-L6-v2)
- **Groq API** `0.11.0` - Lightning-fast LLM inference (Llama 3.1 70B)
- **BeautifulSoup4** `4.12.3` - Web scraping official RGIPT pages
- **DuckDuckGo Search** `6.3.5` - Web search integration
- **PyPDF2** `3.0.1` - PDF document processing
- **python-docx** `1.2.0` - Word document processing

### Frontend
- **React** `18.3.1` - Modern UI framework
- **React Markdown** `9.0.1` - Beautiful formatted responses
- **CSS3** - Custom gradient design with animations
- **LocalStorage** - Query history persistence

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- 4GB RAM minimum
- Groq API Key ([Get it free](https://console.groq.com))

---

### Backend Setup

1. **Clone the repository**
