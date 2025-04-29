import sqlite3
from typing import List, Dict, Any
from src.config import DB_PATH

def setup_database() -> None:
    """Set up SQLite database with required schema."""
    conn = sqlite3.connect(DB_PATH)
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

def insert_items(data: List[Dict[str, Any]]) -> None:
    """Insert items into database with vector indices."""
    conn = sqlite3.connect(DB_PATH)
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

def get_all_items() -> List[tuple]:
    """Get all items from database in vector_index order."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT content FROM items ORDER BY vector_index')
    items = c.fetchall()
    conn.close()
    return items

def lookup_metadata(vector_indices: List[int]) -> List[Dict[str, str]]:
    """Look up metadata for given vector indices."""
    conn = sqlite3.connect(DB_PATH)
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