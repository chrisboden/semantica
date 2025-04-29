import numpy as np
import faiss
from typing import List, Optional
from openai import OpenAI
from src.config import OPENAI_API_KEY, EMBEDDING_MODEL, VECTOR_DIMENSION, VECTORS_PATH

# Create OpenAI client
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=60,
    max_retries=3
)

def get_embedding(text: str) -> List[float]:
    """Get embedding for a text using OpenAI API."""
    response = openai_client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def create_index(embeddings: List[List[float]]) -> None:
    """Create and save FAISS index from embeddings."""
    index = faiss.IndexFlatL2(VECTOR_DIMENSION)
    embeddings_array = np.array(embeddings, dtype=np.float32)
    index.add(embeddings_array)
    faiss.write_index(index, VECTORS_PATH)

def search_index(query_embedding: List[float], k: int) -> tuple[np.ndarray, np.ndarray]:
    """Search FAISS index for similar vectors."""
    index = faiss.read_index(VECTORS_PATH)
    query_array = np.array([query_embedding], dtype=np.float32)
    return index.search(query_array, k) 