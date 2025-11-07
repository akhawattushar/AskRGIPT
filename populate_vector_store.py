import os
import PyPDF2
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

print("🔄 Starting vector store population...")

# PDFs are already at this location
pdf_folder = "./backend/data/documents/pdfs"

# Check if folder exists
if not os.path.exists(pdf_folder):
    print(f"❌ ERROR: PDF folder not found at {pdf_folder}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Available paths: {os.listdir('.')}")
    exit(1)

documents = []
pdf_count = 0

print(f"📁 Looking for PDFs in: {pdf_folder}")

# Loop through all PDFs
for pdf_file in Path(pdf_folder).glob("*.pdf"):
    print(f"📄 Processing: {pdf_file.name}")
    
    try:
        with open(pdf_file, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": pdf_file.name,
                            "page": page_num + 1
                        }
                    )
                    documents.append(doc)
        
        pdf_count += 1
        print(f"   ✅ Success!")
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print(f"\n📊 Total: {len(documents)} pages from {pdf_count} PDFs")

if len(documents) == 0:
    print("❌ No documents extracted!")
    exit(1)

# Create embeddings
print("\n🧠 Creating embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Build vector store
print("💾 Building vector store...")
vector_store = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="./chroma_db",
    collection_name="rgipt_docs"
)

print("✅ DONE! Vector store ready at ./chroma_db")