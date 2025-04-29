import requests
import click
from typing import List, Dict, Optional
from src.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL_NAME
from src.database import lookup_metadata

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