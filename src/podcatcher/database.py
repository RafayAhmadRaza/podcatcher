import sqlite3
from pathlib import Path

DB_PATH = Path("podcatcher.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_db(connection):
    # connection = sqlite3.connect(DB_PATH)

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS podcasts(
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        website TEXT,
        rss_url TEXT NOT NULL UNIQUE)
        """
    )

    connection.execute("""
    CREATE TABLE IF NOT EXISTS episodes(
    id INTEGER PRIMARY KEY,
    podcast_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    published TEXT,
    audio_url TEXT,
    guid TEXT NOT NULL,
    FOREIGN KEY (podcast_id) REFERENCES podcasts(id),
    UNIQUE(podcast_id,guid)
    )
    
    """)
    connection.commit()
    connection.close()