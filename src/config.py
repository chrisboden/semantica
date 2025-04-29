import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Model parameters
MODEL_NAME = "openai/gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_DIMENSION = 1536  # Dimension for text-embedding-3-small
K_NEIGHBORS = 5

# Database
DB_PATH = 'knowledge.db'
VECTORS_PATH = 'vectors.faiss' 