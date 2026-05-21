import os
import re
import hashlib
import numpy as np
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import chromadb
from database.sqlite_db import sqlite_db
from utils.config import config
from utils.logger import logger

class LocalHashEmbeddingFunction:
    """
    Lightweight, 100% offline local word-hashing embedding function for ChromaDB.
    Avoids external model downloads and runs instantly.
    """
    def __init__(self, dimensionality: int = 128):
        self.dimensionality = dimensionality
        self.name = "LocalHashEmbeddingFunction"

    def __call__(self, input: Any) -> Any:
        embeddings = []
        for text in input:
            vector = np.zeros(self.dimensionality)
            words = re.findall(r'\w+', text.lower())
            if not words:
                embeddings.append(vector.tolist())
                continue
            for word in words:
                h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
                idx = h % self.dimensionality
                vector[idx] += 1.0
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            embeddings.append(vector.tolist())
        return embeddings

class MemoryService:
    def __init__(self, chroma_path: str = config.CHROMA_PATH):
        self.sqlite = sqlite_db
        self.chroma_path = chroma_path
        self.collection_name = "weather_agent_memories"
        self.client = None
        self.collection = None
        self.fallback_mode = False
        self.fallback_db = []  # In-memory fallback if ChromaDB fails to load
        
        self._init_chroma()

    def _init_chroma(self):
        """Initializes ChromaDB with offline local word-hashing embeddings."""
        try:
            os.makedirs(self.chroma_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.chroma_path)
            self.embedding_function = LocalHashEmbeddingFunction()
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info("ChromaDB vector store initialized successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize ChromaDB: {e}. Switching to offline in-memory fallback.")
            self.fallback_mode = True

    # SQLITE CACHE & SESSION/HISTORY ACCESSORS
    def get_weather_memory(self, city: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached weather query and AI response for a city."""
        return self.sqlite.get_weather_memory(city)

    def save_weather_memory(self, city: str, user_query: str, ai_response: str) -> bool:
        """Saves a weather query and generated response to SQLite and indexes it in ChromaDB."""
        # Save to SQLite
        sql_success = self.sqlite.save_weather_memory(city, user_query, ai_response)
        
        # Also index in Vector DB for semantic lookups
        memory_text = f"Weather lookup for {city.strip().title()}: Query: {user_query}. Response: {ai_response}"
        memory_id = f"mem_{uuid.uuid4().hex[:10]}"
        self.add_semantic_memory(
            text=memory_text,
            metadata={"city": city.strip().title(), "timestamp": datetime.now().isoformat()},
            doc_id=memory_id
        )
        return sql_success

    def get_sessions(self) -> List[Dict[str, Any]]:
        """Gets all previous chat sessions."""
        return self.sqlite.get_sessions()

    def create_or_update_session(self, session_id: str, title: str) -> bool:
        """Registers/updates a chat session."""
        return self.sqlite.create_or_update_session(session_id, title)

    def update_session_title(self, session_id: str, title: str) -> bool:
        """Renames a chat session."""
        return self.sqlite.update_session_title(session_id, title)

    def delete_session(self, session_id: str) -> bool:
        """Deletes a chat session."""
        return self.sqlite.delete_session(session_id)

    def delete_all_sessions(self) -> bool:
        """Deletes all chat sessions."""
        return self.sqlite.delete_all_sessions()

    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, str]]:
        """Gets history for a session."""
        return self.sqlite.get_chat_history(session_id, limit)

    def save_chat_message(self, session_id: str, role: str, content: str) -> bool:
        """Saves a chat message."""
        return self.sqlite.save_chat_message(session_id, role, content)

    # CHROMADB SEMANTIC VECTOR SEARCH
    def add_semantic_memory(self, text: str, metadata: Dict[str, Any], doc_id: str):
        """Saves a document chunk to the vector store."""
        if not text or not text.strip():
            return
            
        if self.fallback_mode:
            # Fallback memory insertion
            self.fallback_db = [item for item in self.fallback_db if item['id'] != doc_id]
            self.fallback_db.append({
                'id': doc_id,
                'text': text,
                'metadata': metadata
            })
            return

        try:
            self.collection.upsert(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
        except Exception as e:
            logger.error(f"Error adding memory to ChromaDB: {e}. Indexing in memory fallback.")
            self.fallback_db = [item for item in self.fallback_db if item['id'] != doc_id]
            self.fallback_db.append({
                'id': doc_id,
                'text': text,
                'metadata': metadata
            })

    def search_semantic_memories(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Searches vector store for semantically similar memories."""
        if not query or not query.strip():
            return []

        if self.fallback_mode or not self.collection:
            return self._fallback_search(query, limit)

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            formatted_results = []
            if results and 'documents' in results and results['documents']:
                docs = results['documents'][0]
                metas = results['metadatas'][0] if 'metadatas' in results and results['metadatas'] else [{}] * len(docs)
                ids = results['ids'][0] if 'ids' in results and results['ids'] else [""] * len(docs)
                
                for doc, meta, doc_id in zip(docs, metas, ids):
                    formatted_results.append({
                        "id": doc_id,
                        "text": doc,
                        "metadata": meta
                    })
            return formatted_results
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}. Falling back to token matching.")
            return self._fallback_search(query, limit)

    def _fallback_search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Simple fallback Jaccard similarity search using word overlaps."""
        query_words = set(query.lower().split())
        if not query_words:
            return []
            
        scored_results = []
        for item in self.fallback_db:
            text_words = item['text'].lower().split()
            overlap = len(query_words.intersection(text_words))
            union_len = len(query_words.union(text_words))
            score = overlap / union_len if union_len > 0 else 0.0
            
            if score > 0:
                scored_results.append((score, item))
                
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": item['id'],
                "text": item['text'],
                "metadata": item['metadata']
            }
            for _, item in scored_results[:limit]
        ]

    def clear_all_memories(self) -> bool:
        """Wipes SQLite cache and resets ChromaDB collections."""
        sqlite_success = self.sqlite.clear_weather_memories()
        
        if self.fallback_mode:
            self.fallback_db = []
            vector_success = True
        else:
            try:
                if self.client:
                    self.client.delete_collection(self.collection_name)
                    self.collection = self.client.get_or_create_collection(
                        name=self.collection_name,
                        embedding_function=self.embedding_function
                    )
                vector_success = True
                logger.info("ChromaDB vector collection reset successfully.")
            except Exception as e:
                logger.error(f"Error resetting ChromaDB: {e}")
                self.fallback_db = []
                vector_success = False

        return sqlite_success and vector_success

memory_service = MemoryService()
