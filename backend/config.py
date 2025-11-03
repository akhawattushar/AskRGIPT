import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DATA_DIR = "data/documents"
    VECTOR_DB_DIR = "data/vector_db"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    TOP_K_RESULTS = 5
    LLM_MODEL = "gpt-3.5-turbo"
    LLM_TEMPERATURE = 0.3

config = Config()
