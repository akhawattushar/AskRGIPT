import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from config import config

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def extract_text_from_pdf(self, pdf_path):
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page_num, page in enumerate(doc):
                text += f"\n[Page {page_num + 1}]\n"
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"❌ Error reading {pdf_path}: {e}")
            return ""
    
    def process_document(self, file_path):
        print(f"📄 Processing: {os.path.basename(file_path)}")
        
        text = self.extract_text_from_pdf(file_path)
        
        if not text.strip():
            print(f"   ⚠️ No text extracted")
            return []
        
        chunks = self.text_splitter.split_text(text)
        print(f"   ✅ Created {len(chunks)} chunks")
        
        return chunks
    
    def process_all_documents(self):
        all_chunks = []
        metadata = []
        
        folders = ["pdfs", "notices"]
        
        for folder in folders:
            folder_path = os.path.join(config.DATA_DIR, folder)
            if not os.path.exists(folder_path):
                continue
                
            for filename in os.listdir(folder_path):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(folder_path, filename)
                    chunks = self.process_document(file_path)
                    
                    for i, chunk in enumerate(chunks):
                        all_chunks.append(chunk)
                        metadata.append({
                            "source": filename,
                            "chunk_id": i,
                            "category": folder
                        })
        
        print(f"\n🎯 Total chunks created: {len(all_chunks)}")
        return all_chunks, metadata

if __name__ == "__main__":
    processor = DocumentProcessor()
    chunks, metadata = processor.process_all_documents()
    print(f"\n📝 Sample chunk:\n{chunks[0][:200]}..." if chunks else "No documents found")
