import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DATA_DIR = "data/documents"
    VECTOR_DB_DIR = "data/vector_db"
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    
    # OCR settings
    OCR_ENGINE = os.getenv("OCR_ENGINE", "paddleocr")  # paddleocr, tesseract, or auto
    OCR_PREPROCESS = os.getenv("OCR_PREPROCESS", "true").lower() == "true"
    OCR_MIN_CONFIDENCE = float(os.getenv("OCR_MIN_CONFIDENCE", "0.5"))
    
    # Document processing
    USE_SEMANTIC_CHUNKING = os.getenv("USE_SEMANTIC_CHUNKING", "true").lower() == "true"
    SUPPORTED_FORMATS = [".pdf", ".docx", ".txt", ".html", ".htm"]

config = Config()
