import json
import os
import click
from typing import List
from src.database import setup_database, insert_items, get_all_items
from src.embeddings import get_embedding, create_index, search_index
from src.llm import run_prompt
from src.config import DB_PATH, VECTORS_PATH, K_NEIGHBORS

@click.group()
def cli():
    """Semantic Search CLI"""
    pass

@cli.command()
@click.argument('json_path')
def ingest_data(json_path: str) -> None:
    """Ingest data from JSON file into SQLite database."""
    # Setup database
    setup_database()
    
    # Read JSON data
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Insert data into database
    insert_items(data)
    click.echo(f"Ingested {len(data)} items into database")

@cli.command()
def embed_items() -> None:
    """Generate embeddings for all items and create FAISS index."""
    # Get all items from database
    items = get_all_items()
    
    if not items:
        click.echo("No items found in database")
        return
    
    # Generate embeddings
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
    
    # Create and save index
    create_index(embeddings)
    click.echo(f"Successfully embedded {len(embeddings)} items and created FAISS index")

@cli.command()
@click.argument('query')
def search(query: str) -> None:
    """Run complete semantic search process."""
    # Check if database and index exist
    if not os.path.exists(DB_PATH):
        click.echo("Error: Database not found. Please run ingest_data first.")
        return
    if not os.path.exists(VECTORS_PATH):
        click.echo("Error: FAISS index not found. Please run embed_items first.")
        return
    
    try:
        # Get query embedding
        embedding = get_embedding(query)
        if embedding is None:
            return
        
        # Search index
        distances, indices = search_index(embedding, K_NEIGHBORS)
        
        # Run prompt with vector indices
        run_prompt(query, indices[0].tolist())
        
    except Exception as e:
        click.echo(f"Error during search: {str(e)}")
        return

def main():
    cli() 