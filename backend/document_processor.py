"""
Enhanced Document Processor with OCR support for scanned PDFs.
Supports PDF, DOCX, HTML, TXT files with semantic chunking and metadata tracking.
"""
import fitz  # PyMuPDF
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.text_splitter import MarkdownHeaderTextSplitter
except ImportError:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
    except ImportError:
        # Fallback to simple text splitting if langchain not available
        RecursiveCharacterTextSplitter = None
        MarkdownHeaderTextSplitter = None
import os
import re
import io
from typing import List, Dict, Tuple, Optional
try:
    from PIL import Image
    import numpy as np
except ImportError:
    Image = None
    np = None

from config import config

# Import OCR modules
try:
    from ocr.ocr_engine import OCREngine, detect_text_in_pdf
    from ocr.image_preprocessing import ImagePreprocessor
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR modules not available. Scanned PDFs will not be processed.")

# Import document parsing libraries
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("⚠️ python-docx not available. DOCX files will not be processed.")

try:
    from bs4 import BeautifulSoup
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    print("⚠️ BeautifulSoup not available. HTML files will not be processed.")


class DocumentProcessor:
    def __init__(self):
        """Initialize document processor with enhanced features."""
        # Standard text splitter
        if RecursiveCharacterTextSplitter is not None:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=config.CHUNK_SIZE,
                chunk_overlap=config.CHUNK_OVERLAP,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
        else:
            # Fallback: simple splitter
            self.text_splitter = None
            print("⚠️ Langchain not available, using simple text splitting")
        
        # Semantic chunker (for better context preservation)
        if config.USE_SEMANTIC_CHUNKING:
            try:
                from langchain.text_splitter import SemanticChunker
                from langchain.embeddings import HuggingFaceEmbeddings
                embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
                self.semantic_splitter = SemanticChunker(
                    embeddings=embeddings,
                    breakpoint_threshold_type="percentile",
                    breakpoint_threshold_amount=95
                )
                self.use_semantic = True
            except Exception as e:
                print(f"⚠️ Semantic chunking not available: {e}")
                self.use_semantic = False
        else:
            self.use_semantic = False
        
        # Initialize OCR engine if available
        self.ocr_engine = None
        if OCR_AVAILABLE:
            try:
                self.ocr_engine = OCREngine(engine=config.OCR_ENGINE)
            except Exception as e:
                print(f"⚠️ OCR engine initialization failed: {e}")
    
    def _extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Extract text from PDF (supports both text-based and scanned PDFs).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        metadata = {
            "extraction_method": "text",
            "ocr_confidence": None,
            "total_pages": 0,
            "has_text_layer": False
        }
        
        try:
            doc = fitz.open(pdf_path)
            metadata["total_pages"] = len(doc)
            
            text_parts = []
            ocr_confidences = []
            
            # First, try text extraction
            has_text = False
            for page_num, page in enumerate(doc):
                page_text = page.get_text().strip()
                if len(page_text) > 50:  # Significant text found
                    has_text = True
                    text_parts.append(f"\n[Page {page_num + 1}]\n{page_text}")
            
            metadata["has_text_layer"] = has_text
            
            # If no text found, use OCR (for scanned PDFs)
            if not has_text and self.ocr_engine:
                print(f"   🔍 No text layer found, using OCR...")
                metadata["extraction_method"] = "ocr"
                
                for page_num, page in enumerate(doc):
                    try:
                        # Convert page to image
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                        img_data = pix.tobytes("png")
                        pil_image = Image.open(io.BytesIO(img_data))
                        
                        # Perform OCR
                        page_text, confidence = self.ocr_engine.extract_text(
                            pil_image,
                            preprocess=config.OCR_PREPROCESS
                        )
                        
                        if page_text.strip():
                            text_parts.append(f"\n[Page {page_num + 1}]\n{page_text}")
                            ocr_confidences.append(confidence)
                        
                    except Exception as e:
                        print(f"   ⚠️ OCR error on page {page_num + 1}: {e}")
                        continue
                
                if ocr_confidences:
                    metadata["ocr_confidence"] = sum(ocr_confidences) / len(ocr_confidences)
            
            doc.close()
            
            full_text = "\n".join(text_parts)
            return full_text, metadata
            
        except Exception as e:
            print(f"❌ Error reading PDF {pdf_path}: {e}")
            return "", metadata
    
    def _extract_text_from_docx(self, docx_path: str) -> Tuple[str, Dict]:
        """
        Extract text from DOCX file.
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        metadata = {
            "extraction_method": "docx",
            "total_paragraphs": 0
        }
        
        if not DOCX_AVAILABLE:
            return "", metadata
        
        try:
            doc = DocxDocument(docx_path)
            text_parts = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            metadata["total_paragraphs"] = len(text_parts)
            return "\n\n".join(text_parts), metadata
            
        except Exception as e:
            print(f"❌ Error reading DOCX {docx_path}: {e}")
            return "", metadata
    
    def _extract_text_from_html(self, html_path: str) -> Tuple[str, Dict]:
        """
        Extract text from HTML file.
        
        Args:
            html_path: Path to HTML file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        metadata = {
            "extraction_method": "html"
        }
        
        if not HTML_AVAILABLE:
            return "", metadata
        
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text, metadata
            
        except Exception as e:
            print(f"❌ Error reading HTML {html_path}: {e}")
            return "", metadata
    
    def _extract_text_from_txt(self, txt_path: str) -> Tuple[str, Dict]:
        """
        Extract text from TXT file.
        
        Args:
            txt_path: Path to TXT file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        metadata = {
            "extraction_method": "txt"
        }
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(txt_path, 'r', encoding=encoding) as f:
                        text = f.read()
                    return text, metadata
                except UnicodeDecodeError:
                    continue
            
            raise ValueError("Could not decode file with any encoding")
            
        except Exception as e:
            print(f"❌ Error reading TXT {txt_path}: {e}")
            return "", metadata
    
    def extract_text(self, file_path: str) -> Tuple[str, Dict]:
        """
        Extract text from any supported file type.
        
        Args:
            file_path: Path to file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == ".pdf":
            return self._extract_text_from_pdf(file_path)
        elif file_ext == ".docx":
            return self._extract_text_from_docx(file_path)
        elif file_ext in [".html", ".htm"]:
            return self._extract_text_from_html(file_path)
        elif file_ext == ".txt":
            return self._extract_text_from_txt(file_path)
        else:
            print(f"⚠️ Unsupported file type: {file_ext}")
            return "", {"extraction_method": "unsupported"}
    
    def _determine_category(self, file_path: str) -> str:
        """Determine document category from file path."""
        file_path_lower = file_path.lower()
        
        if "policy" in file_path_lower or "policies" in file_path_lower:
            return "policies"
        elif "notice" in file_path_lower or "notification" in file_path_lower:
            return "notices"
        elif "handbook" in file_path_lower or "manual" in file_path_lower:
            return "handbooks"
        else:
            return "pdfs"
    
    def process_document(self, file_path: str) -> Tuple[List[str], List[Dict]]:
        """
        Process a single document and return chunks with metadata.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Tuple of (chunks, metadata_list)
        """
        filename = os.path.basename(file_path)
        print(f"📄 Processing: {filename}")
        
        # Extract text
        text, extraction_metadata = self.extract_text(file_path)
        
        if not text.strip():
            print(f"   ⚠️ No text extracted")
            return [], []
        
        # Determine category
        category = self._determine_category(file_path)
        
        # Chunk text
        if self.use_semantic and len(text) > config.CHUNK_SIZE:
            try:
                chunks = self.semantic_splitter.split_text(text)
                print(f"   ✅ Created {len(chunks)} semantic chunks")
            except Exception as e:
                print(f"   ⚠️ Semantic chunking failed, using standard: {e}")
                chunks = self.text_splitter.split_text(text)
                print(f"   ✅ Created {len(chunks)} chunks")
        else:
            chunks = self.text_splitter.split_text(text)
            print(f"   ✅ Created {len(chunks)} chunks")
        
        # Create metadata for each chunk
        metadata_list = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "source": filename,
                "chunk_id": i,
                "category": category,
                "file_path": file_path,
                **extraction_metadata
            }
            metadata_list.append(chunk_metadata)
        
        return chunks, metadata_list
    
    def process_all_documents(self) -> Tuple[List[str], List[Dict]]:
        """
        Process all documents in the data directory.
        
        Returns:
            Tuple of (all_chunks, all_metadata)
        """
        all_chunks = []
        all_metadata = []
        
        # Process all subdirectories
        folders = ["pdfs", "notices", "policies", "handbooks"]
        
        for folder in folders:
            folder_path = os.path.join(config.DATA_DIR, folder)
            if not os.path.exists(folder_path):
                continue
            
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                
                # Check if file is supported
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext not in config.SUPPORTED_FORMATS:
                    continue
                
                chunks, metadata = self.process_document(file_path)
                
                all_chunks.extend(chunks)
                all_metadata.extend(metadata)
        
        print(f"\n🎯 Total chunks created: {len(all_chunks)}")
        return all_chunks, all_metadata


if __name__ == "__main__":
    processor = DocumentProcessor()
    chunks, metadata = processor.process_all_documents()
    print(f"\n📝 Sample chunk:\n{chunks[0][:200]}..." if chunks else "No documents found")
