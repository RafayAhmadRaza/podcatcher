
from models import Episode
from models import Podcast
from feeds import get_feed
import sqlite3
from pathlib import Path

DB_PATH = Path("podcatcher.db")

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

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
    FOREIGN KEY (podcast_id) REFERENCES podcasts(id) ON DELETE CASCADE,
    UNIQUE(podcast_id,guid)
    )
    
    """)
    connection.commit()
    connection.close()

def add_podcast(podcast):
    


    connection = get_connection()

    SQL_QUERY = """
    INSERT INTO podcasts (title, description,website,rss_url)
    VALUES (?,?,?,?)
    """
    values = (podcast.title,podcast.description,podcast.website,podcast.rss_url)
    connection.execute(
        SQL_QUERY,
        values
    )

    podcast_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    episode_query = """INSERT INTO episodes(podcast_id,title,published,audio_url,guid)
    VALUES (?,?,?,?,?)"""
    for ep in podcast.episodes:
        connection.execute(
            episode_query,
            (podcast_id,ep.title,ep.published,ep.audio_url,ep.guid)
        )
    connection.commit()
    connection.close()

def remove_podcast(podcast):
    connection = get_connection()

    SQL_QUERY = """
    DELETE FROM podcasts WHERE id = ?
    """
    connection.execute(SQL_QUERY,(podcast.id,))
    connection.commit()
    connection.close()

def update_podcast(podcast):
    connection = get_connection()
    new_feed = get_feed(podcast.rss_url)
    
        
    old_episode_guids = {episode.guid for episode in podcast.episodes}

    SQL_QUERY = """
    
    INSERT INTO episodes 
        (podcast_id,title,published,audio_url,guid)
        VALUES(?,?,?,?,?)
    """

    new_episodes = False

    

    for episode in new_feed.episodes:
        if episode.guid not in old_episode_guids:
            connection.execute(
                SQL_QUERY,
                (podcast.id,
                episode.title,
                episode.published,
                episode.audio_url,
                episode.guid)
            )
            new_episodes = True



    connection.commit()
    connection.close()

    if new_episodes:
        print("New Episodes added.")
    else:
        print("No New Episodes Found.")

def get_podcasts():

    SQL_QUERY = """
        SELECT
            podcasts.id,
            podcasts.title,
            podcasts.description,
            podcasts.website,
            podcasts.rss_url,
            episodes.id,
            episodes.podcast_id,
            episodes.title,
            episodes.published,
            episodes.audio_url,
            episodes.guid
        FROM podcasts
        JOIN episodes
            ON podcasts.id = episodes.podcast_id
    """

    connection = get_connection()
    result = connection.execute(SQL_QUERY)
    podcasts = {}

    for row in result:

        if row[0] not in podcasts:
            podcasts[row[0]] = Podcast(
                id=row[0],
                title=row[1],
                description=row[2],
                website=row[3],
                rss_url=row[4],
                episodes=[]
            )

        episode = Episode(
            title=row[7],
            published=row[8],
            audio_url=row[9],
            guid=row[10]
        )

        podcasts[row[0]].episodes.append(episode)

    connection.close()
    return list(podcasts.values())