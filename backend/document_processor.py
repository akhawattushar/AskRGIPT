import os
from sentence_transformers import SentenceTransformer
from vector_store import VectorStore

class DocumentProcessor:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_store = VectorStore()
    
    def process_pdf(self, file_path):
        """Extract text from PDF"""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"⚠️ PDF error {file_path}: {e}")
            return ""
    
    def process_docx(self, file_path):
        """Extract text from DOCX"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            print(f"⚠️ DOCX error: {e}")
            return ""
    
    def process_txt(self, file_path):
        """Extract text from TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ TXT error: {e}")
            return ""
    
    def chunk_text(self, text, chunk_size=500):
        """Split text into chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            
            if current_length >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def process_documents(self, folder_path='scraped_pdfs'):
        """Process ALL file types: PDF, DOCX, TXT"""
        
        if not os.path.exists(folder_path):
            print(f"⚠️ Folder {folder_path} not found!")
            return 0
        
        all_documents = []
        all_metadatas = []
        all_ids = []
        doc_id = 0
        total_files = 0
        
        # Process all files
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                
                text = ""
                file_type = ""
                
                # Determine file type
                if filename.endswith('.pdf'):
                    text = self.process_pdf(file_path)
                    file_type = 'PDF'
                elif filename.endswith('.docx'):
                    text = self.process_docx(file_path)
                    file_type = 'DOCX'
                elif filename.endswith('.txt'):
                    text = self.process_txt(file_path)
                    file_type = 'TXT'
                else:
                    continue  # Skip other files
                
                if not text.strip():
                    print(f"⚠️ {filename}: No content extracted")
                    continue
                
                total_files += 1
                
                # Chunk and store
                chunks = self.chunk_text(text)
                print(f"✅ {filename} ({file_type}): {len(chunks)} chunks")
                
                for i, chunk in enumerate(chunks):
                    all_documents.append(chunk)
                    all_metadatas.append({
                        'source': filename,
                        'file_type': file_type,
                        'chunk_id': i
                    })
                    all_ids.append(f"doc_{doc_id}")
                    doc_id += 1
        
        # Add to vector store
        if all_documents:
            print(f"\n📊 Adding {len(all_documents)} chunks to vector store...")
            self.vector_store.collection.add(
                documents=all_documents,
                metadatas=all_metadatas,
                ids=all_ids
            )
            print(f"✅ Successfully processed {total_files} files!")
        else:
            print("⚠️ No files processed!")
        
        return total_files

if __name__ == "__main__":
    processor = DocumentProcessor()
    
    print("="*50)
    print("DOCUMENT PROCESSING STARTED")
    print("="*50)
    
    # Process local files
    print("\n1️⃣ Processing Local Documents (PDF, DOCX, TXT)...")
    local_count = processor.process_documents('scrapers/scraped_pdfs')
    
    # Process web
    print("\n2️⃣ Scraping RGIPT Official Website...")
    try:
        from rgipt_web_scraper import RGIPTWebScraper
        scraper = RGIPTWebScraper()
        scraper.scrape_pages()
    except Exception as e:
        print(f"⚠️ Web scraping error: {e}")
    
    print("\n" + "="*50)
    print("✅ PROCESSING COMPLETE!")
    print("="*50)
