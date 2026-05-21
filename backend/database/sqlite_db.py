import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from utils.config import config
from utils.logger import logger

class SQLiteDatabase:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Chat sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            
            # Chat messages history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT NOT NULL, -- 'user' or 'assistant'
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
                )
            """)
            
            # City weather memory cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS city_weather_memory (
                    city TEXT PRIMARY KEY,
                    user_query TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            
            conn.commit()
            logger.info("SQLite database tables initialized successfully.")

    # SESSIONS
    def get_sessions(self) -> List[Dict[str, Any]]:
        """Retrieves all chat sessions sorted by latest timestamp."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT session_id, title, timestamp FROM chat_sessions ORDER BY timestamp DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching sessions: {e}")
            return []

    def create_or_update_session(self, session_id: str, title: str) -> bool:
        """Creates a session or updates its title and timestamp."""
        try:
            timestamp = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Check if it exists first to not overwrite custom titles if we just want to update timestamp
                cursor.execute("SELECT 1 FROM chat_sessions WHERE session_id = ?", (session_id,))
                exists = cursor.fetchone()
                
                if exists:
                    cursor.execute("""
                        UPDATE chat_sessions 
                        SET timestamp = ? 
                        WHERE session_id = ?
                    """, (timestamp, session_id))
                else:
                    cursor.execute("""
                        INSERT INTO chat_sessions (session_id, title, timestamp)
                        VALUES (?, ?, ?)
                    """, (session_id, title, timestamp))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False

    def update_session_title(self, session_id: str, title: str) -> bool:
        """Specifically updates session title."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE chat_sessions 
                    SET title = ? 
                    WHERE session_id = ?
                """, (title, session_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating session title: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """Deletes a session and its associated chat history."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Cascade delete manually since foreign key cascade might not be enabled by default
                cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def delete_all_sessions(self) -> bool:
        """Deletes all sessions and chat histories."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_history")
                cursor.execute("DELETE FROM chat_sessions")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting all sessions: {e}")
            return False

    # CHAT HISTORY
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, str]]:
        """Retrieves history for a session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role, content, timestamp 
                    FROM chat_history 
                    WHERE session_id = ? 
                    ORDER BY id ASC 
                    LIMIT ?
                """, (session_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching history for session {session_id}: {e}")
            return []

    def save_chat_message(self, session_id: str, role: str, content: str) -> bool:
        """Saves a message to chat history and updates the session timestamp."""
        try:
            timestamp = datetime.now().isoformat()
            # Ensure session exists. If not, auto-generate title from message preview.
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM chat_sessions WHERE session_id = ?", (session_id,))
                if not cursor.fetchone():
                    # Create session
                    title = content[:30] + "..." if len(content) > 30 else content
                    cursor.execute("""
                        INSERT INTO chat_sessions (session_id, title, timestamp)
                        VALUES (?, ?, ?)
                    """, (session_id, title, timestamp))
                
                # Save message
                cursor.execute("""
                    INSERT INTO chat_history (session_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (session_id, role, content, timestamp))
                
                # Update session timestamp
                cursor.execute("""
                    UPDATE chat_sessions 
                    SET timestamp = ? 
                    WHERE session_id = ?
                """, (timestamp, session_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return False

    # WEATHER MEMORY CACHE
    def get_weather_memory(self, city: str) -> Optional[Dict[str, Any]]:
        """Finds weather cache for a city (case-insensitive)."""
        try:
            normalized_city = city.strip().title()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT city, user_query, ai_response, timestamp 
                    FROM city_weather_memory 
                    WHERE city = ?
                """, (normalized_city,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching weather memory for {city}: {e}")
            return None

    def save_weather_memory(self, city: str, user_query: str, ai_response: str) -> bool:
        """Caches weather query and AI response for a city."""
        try:
            normalized_city = city.strip().title()
            timestamp = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO city_weather_memory (city, user_query, ai_response, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (normalized_city, user_query, ai_response, timestamp))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving weather memory for {city}: {e}")
            return False

    def clear_weather_memories(self) -> bool:
        """Clears all weather memory cache."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM city_weather_memory")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error clearing weather memories: {e}")
            return False

sqlite_db = SQLiteDatabase()
