# Semantic Search Boilerplate

We're going to create a boilerplate semantic search example.

We'll use sqlite for storing the metadata (knowledge.db)
We'll use Faiss for the vector index (vectors.faiss)
We'll use openai `text-embedding-3-small` model for generating the vectors
We'll use k-nearest neighbours for vector search algo

# Implementation Details

The system maintains a direct 1:1 mapping between vectors in FAISS and records in SQLite using a `vector_index` column in the database. When items are ingested:

1. Each item is assigned a sequential `vector_index` (0, 1, 2, etc.)
2. When embeddings are generated, they are added to FAISS in the same order
3. This ensures that item N in the FAISS index corresponds exactly to the database record with `vector_index=N`

This approach eliminates the need for any intermediate mapping files between vector IDs and database records.

# Data Format

The raw data will be in a data.json file with this schema

[
    {
        "id": "id of the item",
        "content": "content of the item",
        "author": "author of the item",
        "action_type": "how the item was acquired: authored, quoted, shared, bookmarked",
        "created_at": "the timestamp for when the item was originally created, eg when a blog post was authored",
        "acquired_at": "the timestamp for when the item was logged to the database"
    }
]


-----

# code for generating embeddings - OPENAI_API_KEY is in the .env file

from openai import OpenAI
client = OpenAI()

response = client.embeddings.create(
    input="Your text string goes here",
    model="text-embedding-3-small"
)

print(response.data[0].embedding)


--------

Functions we will need:

A: `ingest_data` Runs the ingest process to:
1. set up the sqlite db and schema
2. add items from the json to the sqlite db (the metadata)
Note: `ingest` should be runnable from cli and accept a path to a local json file, as the argument

B: `lookup_metadata` Runs a query on the metadata db 
1. use the ids to look up the matching metadata in sqlite
2. returns json response with selected the `content` kv from the corresponding metadata
Note: `get_metadata` should be runnable from cli and accept `item_ids` as an argument (comma separated list of ids)

C: `embed_item` Gets vector embedding for each item in the db
1. generate embedding for the `content` kv of each item 
2. add vectors to faiss with same id as the metadata
3. confirm sucess or show errors
Note: `embed_item` should be runnable from cli and accept path to a local sqlite file, as the argument

D: `embed_query` Gets vector embedding for the user query
1. submit the query text to openai api with text-embedding-3-small model
2. return the vector embeddings for the query text
Note: `embed_query` should be runnable from cli and accept `user_query`, as the argument

E: `lookup_vectors` Runs a semantic search query
runnable from cli and accepts `query_vectors` as an argument, returns json response
1. uses query_vectors to perform k-nearest neighbours on the faiss index (eg 5 nearest)
2. returns the k number of resuts (ie the selected 5 id's) in rank order
Note: `lookup_vectors` should be runnable from cli and accept `query_vectors` and `k` (optional), as the arguments. `k` being the number of results to return

F: `run_prompt` Makes a request to LLM API to generate a natural language answer to the user's question
1. Composes a prompt payload with messages array including system message and user message:
   a. For system message: 
    - Uses the content in query_prompt.md prompt template, as the system message
    - populates the {query_results} placeholder in the prompt template with the selected metadata from the database via `lookup_metadata`
   b. For user message:
    - Uses the `user_query` text as the user message
2. Submits the prompt payload via OpenRouter API to the selected LLM 
    - See .cursor/rules/openrouter_mdc for full documentation on LLM interactions
    - Model params should be streaming: false, model: openai/gpt-4o-mini model. Place model params at top of file for easy changes
    - OPENROUTER_API_KEY in .env along with base url
3. Handles the chat completions response from the LLM and returns the assistant message.
Note: `run_prompt` should be runnable from cli, and accept `user_query` and `item_ids`


F: `search` Runs the full semantic search process, accepts `query` as an argument
1. Checks if sqlite db and faiss index exists else returns error saying database or faiss index needs to be setup
2. Runs `embed_query` passing in the `query` as `user_query
3. Runs `lookup_vectors` passing in the `query_vectors`
4. Runs `run_prompt` passing in the `user_query` and `item_ids`