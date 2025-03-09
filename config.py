import os
from dotenv import load_dotenv
# API settings
API_HOST = "0.0.0.0"
API_PORT = 3002
API_RELOAD = True

# Index settings
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
INDEX_DATA_DIR = "index_data"

# LLM settings
LLM_MODEL_NAME = "gemini-2.0-flash"
LLM_TEMPERATURE = 0
LLM_MAX_TOKENS = 5000
LLM_TIMEOUT = 30
LLM_MAX_RETRIES = 3

# Text processing settings
DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 100

# Supported file types
SUPPORTED_EXTENSIONS = ['.txt', '.pdf', '.docx']

# Google API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
POSTGRES_URI = os.getenv("POSTGRES_URI")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY