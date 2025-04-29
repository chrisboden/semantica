# Semantic Search Boilerplate

A semantic search implementation using FAISS for vector storage, SQLite for metadata, and OpenAI embeddings.

## Features

- Ingest data from JSON files into SQLite database
- Generate embeddings using OpenAI's text-embedding-3-small model
- Store and search vectors using FAISS with direct mapping to SQLite records via vector_index
- Semantic search with k-nearest neighbors
- LLM-powered answer generation using OpenRouter

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

## Usage

The system provides several CLI commands:

1. Ingest data:
```bash
python3 search.py ingest-data data.json
```

2. Generate embeddings:
```bash
python3 search.py embed-items knowledge.db
```

3. Run a search:
```bash
python3 search.py search "your search query here"
```

### Individual Commands

You can also use the individual components:

- Generate query embedding:
```bash
python3 search.py embed-query "your query text"
```

- Look up metadata by IDs:
```bash
python3 search.py lookup-metadata "id1,id2,id3"
```

- Look up vectors:
```bash
python3 search.py lookup-vectors "[vector_array]" --k 5
```

- Run prompt:
```bash
python3 search.py run-prompt "your question" "id1,id2,id3"
```

## Data Format

The input JSON file should follow this schema:
```json
[
    {
        "id": "unique_id",
        "content": "text content to search",
        "author": "content author",
        "action_type": "how item was acquired",
        "created_at": "original creation timestamp",
        "acquired_at": "when item was added to database"
    }
]
```

## Files

- `search.py`: Main implementation
- `query_prompt.md`: Prompt template for LLM
- `knowledge.db`: SQLite database with items and their vector indices
- `vectors.faiss`: FAISS vector index with 1:1 mapping to database records

## Implementation Details

The system maintains a direct 1:1 mapping between FAISS vector indices and SQLite records using a `vector_index` column in the database. This ensures that item N in the FAISS index corresponds exactly to the database record with `vector_index=N`, eliminating the need for any intermediate mapping files.

Here's how it works:

1. During data ingestion:
   - Each item is assigned a sequential `vector_index` (0, 1, 2, etc.)
   - This index is stored in the SQLite database alongside the item's metadata

2. During embedding generation:
   - Items are retrieved from SQLite in `vector_index` order
   - Embeddings are added to FAISS in the same order
   - This maintains the 1:1 correspondence between FAISS and SQLite indices

3. During search:
   - FAISS returns indices of similar vectors
   - These indices directly correspond to the `vector_index` values in SQLite
   - Metadata can be retrieved without any additional mapping step 