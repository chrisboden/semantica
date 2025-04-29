import json
import sqlite3
import numpy as np
import faiss
import os
import click
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
import requests

# Load environment variables
load_dotenv()

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Create OpenAI client
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=60,
    max_retries=3
)

# Model parameters
MODEL_NAME = "openai/gpt-4-turbo"
EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_DIMENSION = 1536  # Dimension for text-embedding-3-small
K_NEIGHBORS = 5

def setup_database(db_path: str) -> None:
    """Set up SQLite database with required schema."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            author TEXT,
            action_type TEXT,
            created_at TEXT,
            acquired_at TEXT,
            vector_index INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def get_embedding(text: str) -> List[float]:
    """Get embedding for a text using OpenAI API."""
    response = openai_client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def lookup_metadata(vector_indices: List[int]) -> List[Dict[str, str]]:
    """Look up metadata for given vector indices."""
    conn = sqlite3.connect('knowledge.db')
    c = conn.cursor()
    
    placeholders = ','.join('?' * len(vector_indices))
    query = f'SELECT id, content, author, action_type, created_at, acquired_at FROM items WHERE vector_index IN ({placeholders}) ORDER BY vector_index'
    c.execute(query, vector_indices)
    results = [{
        'id': row[0],
        'content': row[1],
        'author': row[2] or 'Unknown',
        'action_type': row[3] or 'Unknown',
        'created_at': row[4] or 'Unknown',
        'acquired_at': row[5] or 'Unknown'
    } for row in c.fetchall()]
    conn.close()
    
    return results

def run_prompt(user_query: str, vector_indices: List[int]) -> Optional[str]:
    """Generate LLM response using query and context."""
    # Get metadata for items
    metadata = lookup_metadata(vector_indices)
    
    # Read prompt template
    with open('query_prompt.md', 'r') as f:
        system_prompt = f.read()
    
    # Create formatted context with metadata
    context_items = []
    for item in metadata:
        context_item = f"""Content: {item['content']}

Author: {item['author']}
Type: {item['action_type']}

-----------"""
        context_items.append(context_item)
    
    # Join all context items with newlines
    context = "\n\n".join(context_items)
    
    # Replace placeholder with formatted context
    system_prompt = system_prompt.replace('{query_results}', context)
    
    # Debug prints
    click.echo("\nDEBUG - Context being used:")
    click.echo(f"Number of context items: {len(metadata)}")
    click.echo(f"Context:\n{context}\n")
    click.echo(f"DEBUG - Full prompt:\n{system_prompt}\n")
    
    # Prepare messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    # Make request to OpenRouter
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/OpenRouterAPI/openrouter",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    }
    
    response = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        answer = result['choices'][0]['message']['content']
        click.echo(answer)
        return answer
    else:
        click.echo(f"Error: {response.status_code} - {response.text}")
        return None

def run_cli():
    """Run the CLI application."""
    @click.group()
    def cli():
        """Semantic Search CLI"""
        pass

    @cli.command()
    @click.argument('json_path')
    def ingest_data(json_path: str) -> None:
        """Ingest data from JSON file into SQLite database."""
        db_path = 'knowledge.db'
        
        # Setup database
        setup_database(db_path)
        
        # Read JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Insert data into database with vector indices
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        for idx, item in enumerate(data):
            c.execute('''
                INSERT OR REPLACE INTO items 
                (id, content, author, action_type, created_at, acquired_at, vector_index)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['id'],
                item['content'],
                item.get('author'),
                item.get('action_type'),
                item.get('created_at'),
                item.get('acquired_at'),
                idx
            ))
        conn.commit()
        conn.close()
        click.echo(f"Ingested {len(data)} items into database")

    @cli.command()
    @click.argument('db_path')
    def embed_items(db_path: str) -> None:
        """Generate embeddings for all items and create FAISS index."""
        # Get all items from database in vector_index order
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT content FROM items ORDER BY vector_index')
        items = c.fetchall()
        conn.close()
        
        if not items:
            click.echo("No items found in database")
            return
        
        # Create FAISS index
        index = faiss.IndexFlatL2(VECTOR_DIMENSION)
        
        # Generate embeddings and add to index
        embeddings = []
        for content, in items:  # Unpack single item from row tuple
            try:
                embedding = get_embedding(content)
                embeddings.append(embedding)
                click.echo(f"Successfully embedded item")
            except Exception as e:
                click.echo(f"Error generating embedding: {str(e)}")
        
        if not embeddings:
            click.echo("No embeddings were successfully generated. Please check your OpenAI API key and try again.")
            return
        
        # Add embeddings to index
        embeddings_array = np.array(embeddings, dtype=np.float32)
        index.add(embeddings_array)
        
        # Save index
        faiss.write_index(index, 'vectors.faiss')
        
        click.echo(f"Successfully embedded {len(embeddings)} items and created FAISS index")

    @cli.command()
    @click.argument('query')
    def search(query: str) -> None:
        """Run complete semantic search process."""
        # Check if database and index exist
        if not os.path.exists('knowledge.db'):
            click.echo("Error: Database not found. Please run ingest_data first.")
            return
        if not os.path.exists('vectors.faiss'):
            click.echo("Error: FAISS index not found. Please run embed_items first.")
            return
        
        # Get query embedding
        try:
            embedding = get_embedding(query)
            if embedding is None:
                return
            
            # Look up similar vectors
            index = faiss.read_index('vectors.faiss')
            
            # Convert query vectors to numpy array
            query_array = np.array([embedding], dtype=np.float32)
            
            # Search
            distances, indices = index.search(query_array, K_NEIGHBORS)
            
            # Run prompt with vector indices
            run_prompt(query, indices[0].tolist())
            
        except Exception as e:
            click.echo(f"Error during search: {str(e)}")
            return

    cli()

if __name__ == '__main__':
    run_cli() 