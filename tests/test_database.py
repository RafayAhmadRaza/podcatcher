"""Tests for database functionality."""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the database module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcatcher.database import (
    get_connection,
    create_db,
    add_podcast,
    remove_podcast,
    update_podcast,
    set_download,
    get_podcasts,
    remove_episode,
    DB_PATH,
)
from podcatcher.models import Episode, Podcast


class TestDatabase:
    """Test database operations with real SQLite."""

    def setup_method(self):
        """Create a temporary database for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_podcatcher.db"
        
        # Monkey-patch the DB_PATH
        import podcatcher.database as db_module
        self.original_db_path = db_module.DB_PATH
        db_module.DB_PATH = self.db_path

        self.connection = get_connection()
        create_db(self.connection)
        self.connection.close()

    def teardown_method(self):
        """Clean up temporary database."""
        import podcatcher.database as db_module
        db_module.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def create_test_podcast(self, id=1):
        """Create a test podcast with episodes."""
        return Podcast(
            id=id,
            title="Test Podcast",
            description="A test podcast",
            website="http://test.com",
            rss_url="http://test.com/rss",
            episodes=[
                Episode(
                    title="Episode 1",
                    published="2024-01-01",
                    audio_url="http://test.com/ep1.mp3",
                    guid="ep1-guid",
                ),
                Episode(
                    title="Episode 2",
                    published="2024-01-02",
                    audio_url="http://test.com/ep2.mp3",
                    guid="ep2-guid",
                ),
            ],
        )

    def test_create_db_creates_tables(self):
        """Test that create_db creates the required tables."""
        conn = get_connection()
        cursor = conn.cursor()

        # Check podcasts table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='podcasts'")
        assert cursor.fetchone() is not None

        # Check episodes table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='episodes'")
        assert cursor.fetchone() is not None

        conn.close()

    def test_add_podcast(self):
        """Test adding a podcast with episodes."""
        podcast = self.create_test_podcast()
        add_podcast(podcast)

        # Verify podcast was added
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM podcasts WHERE title = 'Test Podcast'")
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "Test Podcast"
        podcast_id = row[0]

        # Verify episodes were added - check by column name
        cursor.execute("SELECT title FROM episodes WHERE podcast_id = ? ORDER BY id", (podcast_id,))
        episodes = cursor.fetchall()
        assert len(episodes) == 2
        assert episodes[0][0] == "Episode 1"
        assert episodes[1][0] == "Episode 2"

        conn.close()

    def test_get_podcasts(self):
        """Test retrieving podcasts with episodes."""
        podcast = self.create_test_podcast()
        add_podcast(podcast)

        podcasts = get_podcasts()
        assert len(podcasts) == 1
        assert podcasts[0].title == "Test Podcast"
        assert len(podcasts[0].episodes) == 2
        assert podcasts[0].episodes[0].title == "Episode 1"
        assert podcasts[0].episodes[1].title == "Episode 2"
        assert podcasts[0].episodes[0].guid == "ep1-guid"
        assert podcasts[0].episodes[1].guid == "ep2-guid"

    def test_remove_podcast(self):
        """Test removing a podcast cascades to episodes."""
        podcast = self.create_test_podcast()
        add_podcast(podcast)

        # Re-fetch to get the ID
        podcasts = get_podcasts()
        podcast_id = podcasts[0].id

        remove_podcast(podcasts[0])

        # Verify podcast and episodes are gone
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM podcasts WHERE id = ?", (podcast_id,))
        assert cursor.fetchone() is None

        cursor.execute("SELECT * FROM episodes WHERE podcast_id = ?", (podcast_id,))
        assert len(cursor.fetchall()) == 0

        conn.close()

    def test_update_podcast_adds_new_episodes(self):
        """Test updating a podcast adds new episodes without duplicates."""
        podcast = self.create_test_podcast()
        add_podcast(podcast)

        # Create updated podcast with new episode (this is what get_feed would return)
        updated_feed = Podcast(
            id=1,
            title="Test Podcast",
            description="A test podcast",
            website="http://test.com",
            rss_url="http://test.com/rss",
            episodes=[
                Episode(
                    title="Episode 1",
                    published="2024-01-01",
                    audio_url="http://test.com/ep1.mp3",
                    guid="ep1-guid",
                ),
                Episode(
                    title="Episode 2",
                    published="2024-01-02",
                    audio_url="http://test.com/ep2.mp3",
                    guid="ep2-guid",
                ),
                Episode(
                    title="Episode 3",
                    published="2024-01-03",
                    audio_url="http://test.com/ep3.mp3",
                    guid="ep3-guid",
                ),
            ],
        )

        # Get the podcast from database (has only 2 episodes)
        podcasts = get_podcasts()
        db_podcast = podcasts[0]
        assert len(db_podcast.episodes) == 2

        # Mock get_feed to return the updated feed with 3 episodes
        with patch("podcatcher.database.get_feed") as mock_get_feed:
            mock_get_feed.return_value = updated_feed
            update_podcast(db_podcast)

        # Verify new episode was added
        podcasts = get_podcasts()
        assert len(podcasts[0].episodes) == 3
        guids = {ep.guid for ep in podcasts[0].episodes}
        assert "ep1-guid" in guids
        assert "ep2-guid" in guids
        assert "ep3-guid" in guids

    def test_update_podcast_no_duplicates(self):
        """Test updating a podcast doesn't create duplicate episodes."""
        podcast = self.create_test_podcast()
        add_podcast(podcast)

        # Get the podcast from database
        podcasts = get_podcasts()
        db_podcast = podcasts[0]
        assert len(db_podcast.episodes) == 2

        # Mock get_feed to return same episodes (no new ones)
        updated_feed = Podcast(
            id=1,
            title="Test Podcast",
            description="A test podcast",
            website="http://test.com",
            rss_url="http://test.com/rss",
            episodes=[
                Episode(
                    title="Episode 1",
                    published="2024-01-01",
                    audio_url="http://test.com/ep1.mp3",
                    guid="ep1-guid",
                ),
                Episode(
                    title="Episode 2",
                    published="2024-01-02",
                    audio_url="http://test.com/ep2.mp3",
                    guid="ep2-guid",
                ),
            ],
        )

        with patch("podcatcher.database.get_feed") as mock_get_feed:
            mock_get_feed.return_value = updated_feed
            update_podcast(db_podcast)
            update_podcast(db_podcast)  # Run twice

        podcasts = get_podcasts()
        assert len(podcasts[0].episodes) == 2  # Still only 2 episodes

    def test_set_download(self):
        """Test marking an episode as downloaded."""
        podcast = self.create_test_podcast()
        add_podcast(podcast)

        podcasts = get_podcasts()
        episode = podcasts[0].episodes[0]

        set_download(podcasts[0].id, episode, True, "/path/to/episode.mp3")

        # Verify download status
        podcasts = get_podcasts()
        updated_episode = podcasts[0].episodes[0]
        assert updated_episode.is_downloaded is True
        assert updated_episode.local_path == "/path/to/episode.mp3"

    def test_remove_episode(self):
        """Test removing an episode (marking as watched, not downloaded)."""
        podcast = self.create_test_podcast()
        add_podcast(podcast)

        podcasts = get_podcasts()
        episode = podcasts[0].episodes[0]

        # First mark as downloaded
        set_download(podcasts[0].id, episode, True, "/path/to/episode.mp3")

        # Then remove (mark watched, not downloaded)
        remove_episode(podcasts[0].id, episode)

        podcasts = get_podcasts()
        updated_episode = podcasts[0].episodes[0]
        assert updated_episode.is_downloaded is False
        assert updated_episode.local_path is None
        assert updated_episode.watched is True

    def test_unique_constraint_podcast_rss_url(self):
        """Test that duplicate RSS URLs are rejected."""
        podcast1 = self.create_test_podcast()
        podcast1.rss_url = "http://test.com/rss"
        add_podcast(podcast1)

        podcast2 = self.create_test_podcast()
        podcast2.rss_url = "http://test.com/rss"  # Same URL
        podcast2.title = "Different Title"

        with pytest.raises(sqlite3.IntegrityError):
            add_podcast(podcast2)

    def test_unique_constraint_episode_guid_per_podcast(self):
        """Test that duplicate episode GUIDs per podcast are rejected."""
        podcast = self.create_test_podcast()
        add_podcast(podcast)

        podcasts = get_podcasts()
        podcast_id = podcasts[0].id

        # Try to insert episode with same GUID
        conn = get_connection()
        cursor = conn.cursor()
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO episodes (podcast_id, title, published, audio_url, guid) VALUES (?, ?, ?, ?, ?)",
                (podcast_id, "Duplicate", "2024-01-03", "http://test.com/ep3.mp3", "ep1-guid")
            )

        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])