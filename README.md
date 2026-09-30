# Podcatcher

Podcatcher is a small podcast client written in Python.

I built it as a learning project around RSS feeds, SQLite, HTTP downloads, VLC playback, and Textual. It has both a command-line interface and a terminal UI.

## Features

* **RSS feed parsing** - Add podcasts by RSS URL, fetch episodes
* **SQLite database** - Persistent storage for podcasts, episodes, download status
* **HTTP downloads** - Download episodes with resume support (`.part` files, HTTP Range requests)
* **VLC playback** - Play downloaded or streaming episodes
* **Terminal UI** - Three-panel layout: podcasts, episodes, queue
* **Episode queue** - Add episodes to queue, auto-play next
* **Search** - Filter episodes by title (case-insensitive)
* **Playback speed** - Adjustable from 0.5x to 2.5x
* **Playback controls** - Play/pause, stop, seek, next

## Installation

Requires Python 3.10+ and VLC.

```bash
pip install -e .
```

Or install dependencies manually:

```bash
pip install feedparser httpx python-vlc textual
```

Make sure VLC is installed on your system:
- Linux: `apt install vlc` / `dnf install vlc` / `pacman -S vlc`
- macOS: `brew install vlc`
- Windows: Download from videolan.org

## CLI Usage

```bash
podcatcher -a "RSS_URL"           # Add podcast
podcatcher -l                      # List podcasts
podcatcher -u "PODCAST_NAME"       # Update podcast (fetch new episodes)
podcatcher -r "PODCAST_NAME"       # Remove podcast
podcatcher -d "PODCAST_NAME"       # Download episode (interactive)
podcatcher -p "PODCAST_NAME"       # Play episode (interactive)
```

## TUI Usage

Run the terminal UI:

```bash
podcatcher
```

Or directly:

```bash
python -m podcatcher.tui
```

### Keyboard Controls

| Key | Action |
|-----|--------|
| `q` | Quit |
| `←` / `→` | Switch panels (podcasts ↔ episodes ↔ queue) |
| `Tab` | Cycle panels |
| `↑` / `↓` | Navigate list |
| `Enter` | Play selected episode |
| `Space` | Pause / resume |
| `s` | Stop |
| `n` | Play next (from queue) |
| `[` | Decrease playback speed |
| `]` | Increase playback speed |
| `j` / `l` | Seek -10s / +10s |
| `a` | Add selected episode to queue |
| `x` | Remove selected queue item |
| `c` | Clear queue |
| `d` | Download selected episode |
| `/` | Search episodes |
| `Esc` | Clear search / close input |
| `A` | Add podcast (RSS URL) |
| `u` | Update selected podcast |
| `r` | Refresh from database |
| `?` | Show help |

### Panels

**Podcasts (left)** - List of subscribed podcasts. Select one to show its episodes.

**Episodes (center)** - Episodes for the selected podcast. When search is active, shows filtered results. Press `Enter` to play, `a` to queue, `d` to download.

**Queue (right)** - Queued episodes. `[>]` indicates currently playing. Press `Enter` to play a queue item, `x` to remove, `c` to clear.

### Playback Status

Bottom area shows:
- Currently playing episode title
- Progress bar with current/total time
- **Speed: 1.00x** (updates when changed)
- Status messages
- Download progress (when active)

### Playback Speed

Speed range: 0.5x, 0.75x, 1.0x, 1.25x, 1.5x, 1.75x, 2.0x, 2.25x, 2.5x

Press `[` to decrease, `]` to increase. The speed display updates immediately and applies to the current VLC player. Speed persists while the app runs but resets on restart.

### Search

Press `/` to open search. Type to filter episodes by title (case-insensitive). The episode list updates as you type. Press `Esc` to clear search and restore all episodes. Changing podcasts also clears search.

### Queue

Add episodes with `a`. The queue uses stable identity (podcast ID + episode GUID) so duplicates are prevented and items survive UI refreshes. When an episode finishes, the next queue item plays automatically.

### Playback Independence

Browsing (changing podcast/episode selection, searching) never stops playback. The `playing_*` state is separate from `selected_*` state.

## Project Structure

```
podcatcher/
├── pyproject.toml
├── README.md
├── TEST_REPORT.md
├── LICENSE
├── podcatcher.db
├── src/
│   └── podcatcher/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py          # Command-line interface
│       ├── models.py       # Episode, Podcast dataclasses
│       ├── database.py     # SQLite operations
│       ├── feeds.py        # RSS feed parsing
│       ├── downloader.py   # HTTP downloads with resume
│       ├── player.py       # VLC player wrapper
│       ├── tui.py          # Textual TUI application
│       └── tui.tcss        # TUI styles
└── tests/
    ├── test_database.py
    ├── test_filtering.py
    ├── test_markup_safety.py
    ├── test_playback_state.py
    ├── test_queue.py
    └── test_tui.py
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=podcatcher
```

Check syntax:

```bash
python -m compileall src
```

## Current Limitations

* No persistent config file (speed, window size reset on restart)
* No OPML import/export
* No episode description display in TUI
* Network streams may not show duration until playback starts
* Watched state only marked in database, files not auto-deleted
* No chapter support
* No playlist export

## License

MIT