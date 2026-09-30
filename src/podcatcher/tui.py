from textual.app import App, ComposeResult
from textual import events, work
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)
from textual.worker import Worker, WorkerState

import vlc

from .database import (
    add_podcast,
    get_podcasts,
    set_download,
    update_podcast,
)
from .downloader import download_ep
from .feeds import get_feed
from .player import (
    create_network_player,
    create_player,
    get_timer,
    pause_play,
    start_play,
)


podcasts = get_podcasts()
SELECTED_PDC = 0


class PodcatcherApp(App):

    CSS_PATH = "tui.tcss"

    # ---------------------------------------------------------
    # Startup
    # ---------------------------------------------------------

    def on_mount(self):

        self.selected_podcast = None
        self.selected_episode = None

        self.playing_podcast = None
        self.playing_episode = None
        self.current_player = None

        self.queue = []
        self.queue_index = 0

        self.input_action = None

        self.playback_speed = 1.0

        # Search state
        self.search_query = ""
        self.visible_episodes = []

        self.player_timer = self.set_interval(
            1,
            self.update_player_time,
        )

        self.refresh_podcast_list()

        if podcasts:

            self.selected_podcast = podcasts[
                SELECTED_PDC
            ]

        self.refresh_episode_list()
        self.refresh_queue_list()

        self.update_playback_bar(
            0,
            0,
        )

        self.update_task_progress(
            0,
        )

        self.hide_task_progress()

        self.query_one(
            "#podcast-list",
            ListView,
        ).focus()

        # Initialize key-help with safe text (no markup)
        self.update_key_help()
        self.update_speed_display()

    # ---------------------------------------------------------
    # Keyboard
    # ---------------------------------------------------------

    def on_key(
        self,
        event: events.Key,
    ):

        if self.input_action is not None:
            return

        if event.key == "q":
            self.exit()
            return

        if event.key == "left":

            self.query_one(
                "#podcast-list",
                ListView,
            ).focus()

            return

        if event.key == "right":

            self.query_one(
                "#episodes-list",
                ListView,
            ).focus()

            return

        if event.key == "tab":

            self.focus_next_panel()

            return

        # -----------------------------------------------------
        # Playback
        # -----------------------------------------------------

        if event.key == "space":

            self.toggle_playback()

            return

        if event.key == "s":

            self.stop_current()

            return

        if event.key == "j":

            self.seek(-10)

            return

        if event.key == "l":

            self.seek(10)

            return

        if event.key == "n":

            self.play_next()

            return

        if event.key == "[":

            self.change_playback_speed(-0.25)

            return

        if event.key == "]":

            self.change_playback_speed(0.25)

            return

        # -----------------------------------------------------
        # Queue
        # -----------------------------------------------------

        if event.key == "a":

            self.add_selected_to_queue()

            return

        if event.key == "x":

            self.remove_selected_queue_item()

            return

        if event.key == "c":

            self.clear_queue()

            return

        # -----------------------------------------------------
        # Podcast
        # -----------------------------------------------------

        if event.key == "u":

            self.update_selected_podcast()

            return

        # -----------------------------------------------------
        # Download
        # -----------------------------------------------------

        if event.key == "d":

            self.download_selected_episode()

            return

        # -----------------------------------------------------
        # Search
        # -----------------------------------------------------

        if event.key == "/":

            self.show_input(
                "Search episodes...",
                "search",
            )

            return

        # -----------------------------------------------------
        # Add podcast
        # -----------------------------------------------------

        if event.key == "A":

            self.show_input(
                "RSS URL...",
                "add",
            )

            return

        # -----------------------------------------------------
        # Refresh
        # -----------------------------------------------------

        if event.key == "r":

            self.refresh_from_database()

            return

        # -----------------------------------------------------
        # Help
        # -----------------------------------------------------

        if event.key == "?":

            self.show_help()

            return

    # ---------------------------------------------------------
    # Focus navigation
    # ---------------------------------------------------------

    def focus_next_panel(self):

        podcast_list = self.query_one(
            "#podcast-list",
            ListView,
        )

        episode_list = self.query_one(
            "#episodes-list",
            ListView,
        )

        queue_list = self.query_one(
            "#queue-list",
            ListView,
        )

        focused = self.focused

        if focused == podcast_list:

            episode_list.focus()

        elif focused == episode_list:

            queue_list.focus()

        else:

            podcast_list.focus()

    # ---------------------------------------------------------
    # Input
    # ---------------------------------------------------------

    def show_input(
        self,
        placeholder,
        action,
    ):

        input_box = self.query_one(
            "#command-input",
            Input,
        )

        self.input_action = action

        input_box.placeholder = placeholder
        input_box.value = ""
        input_box.display = True
        input_box.focus()

    def close_input(self):

        input_box = self.query_one(
            "#command-input",
            Input,
        )

        input_box.value = ""
        input_box.display = False

        self.input_action = None

        self.query_one(
            "#podcast-list",
            ListView,
        ).focus()

    def on_input_key(
        self,
        event: events.Key,
    ):

        if event.key == "escape":

            event.stop()

            # If search is active, clear it instead of closing input
            if self.input_action == "search":
                self.clear_search()
            else:
                self.close_input()

    def on_input_submitted(
        self,
        event: Input.Submitted,
    ):

        value = event.value.strip()

        action = self.input_action

        self.close_input()

        if not value:
            return

        if action == "add":

            self.add_podcast_from_url(
                value
            )

        elif action == "search":

            self.search_episodes(
                value
            )

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search_episodes(
        self,
        query,
    ):

        if self.selected_podcast is None:

            self.set_task_status(
                "Select a podcast first."
            )

            return

        query = query.lower()
        self.search_query = query

        episodes_list = self.query_one(
            "#episodes-list",
            ListView,
        )

        episodes_list.clear()

        matches = []

        for episode in (
            self.selected_podcast.episodes
        ):

            if query in episode.title.lower():

                matches.append(
                    episode
                )

        self.visible_episodes = matches

        for episode in matches:

            self.add_episode_list_item(
                episodes_list,
                episode,
            )

        self.set_task_status(
            f"{len(matches)} episode(s) found."
        )

    def clear_search(self):
        """Clear search and restore full episode list."""
        self.search_query = ""
        self.visible_episodes = []
        self.close_input()
        self.refresh_episode_list()
        self.set_task_status("Search cleared.")

    # ---------------------------------------------------------
    # Podcast
    # ---------------------------------------------------------

    def add_podcast_from_url(
        self,
        feed_url,
    ):

        self.set_task_status(
            "Fetching podcast..."
        )

        self.show_task_progress()

        self.add_podcast_worker(
            feed_url
        )

    @work(
        thread=True,
        exclusive=False,
    )
    def add_podcast_worker(
        self,
        feed_url,
    ):

        podcast = get_feed(
            feed_url
        )

        add_podcast(
            podcast
        )

        return podcast

    def update_selected_podcast(self):

        if self.selected_podcast is None:

            self.set_task_status(
                "Select a podcast first."
            )

            return

        podcast = self.selected_podcast

        self.set_task_status(
            f"Updating: {podcast.title}"
        )

        self.show_task_progress()

        self.update_podcast_worker(
            podcast
        )

    @work(
        thread=True,
        exclusive=False,
    )
    def update_podcast_worker(
        self,
        podcast,
    ):

        update_podcast(
            podcast
        )

        return podcast

    # ---------------------------------------------------------
    # Download
    # ---------------------------------------------------------

    def download_selected_episode(self):

        if self.selected_podcast is None:

            self.set_task_status(
                "Select a podcast first."
            )

            return

        if self.selected_episode is None:

            self.set_task_status(
                "Select an episode first."
            )

            return

        podcast = self.selected_podcast
        episode = self.selected_episode

        if episode.audio_url is None:

            self.set_task_status(
                "Episode has no audio URL."
            )

            return

        if episode.is_downloaded:

            self.set_task_status(
                "Episode is already downloaded."
            )

            return

        self.set_task_status(
            f"Downloading: {episode.title}"
        )

        self.show_task_progress()

        self.download_episode_worker(
            podcast,
            episode,
        )

    @work(
        thread=True,
        exclusive=False,
    )
    def download_episode_worker(
        self,
        podcast,
        episode,
    ):

        def progress_callback(
            current,
            total,
        ):

            if total <= 0:
                return

            percentage = (
                current / total
            ) * 100

            self.call_from_thread(
                self.update_task_progress,
                percentage,
            )

        result = download_ep(
            podcast.title,
            episode.title,
            episode.audio_url,
            progress_callback,
        )

        return (
            result,
            podcast,
            episode,
        )

    # ---------------------------------------------------------
    # Worker state
    # ---------------------------------------------------------

    def on_worker_state_changed(
        self,
        event: Worker.StateChanged,
    ):

        worker = event.worker

        if event.state == WorkerState.SUCCESS:

            if worker.name == "add_podcast_worker":

                podcast = worker.result

                self.refresh_from_database()

                self.set_task_status(
                    f"Added: {podcast.title}"
                )

                self.hide_task_progress()

                return

            if worker.name == "update_podcast_worker":

                podcast = worker.result

                self.refresh_from_database()

                self.set_task_status(
                    f"Updated: {podcast.title}"
                )

                self.hide_task_progress()

                return

            if worker.name == "download_episode_worker":

                (
                    result,
                    podcast,
                    episode,
                ) = worker.result

                is_downloaded, local_path = result

                if is_downloaded:

                    set_download(
                        podcast.id,
                        episode,
                        True,
                        local_path,
                    )

                    episode.is_downloaded = True
                    episode.local_path = local_path

                    self.refresh_episode_list()

                    self.update_task_progress(
                        100
                    )

                    self.set_task_status(
                        "Download complete."
                    )

                else:

                    self.set_task_status(
                        "Download failed."
                    )

                self.hide_task_progress()

                return

        if event.state == WorkerState.ERROR:

            self.set_task_status(
                f"Operation failed: {worker.error}"
            )

            self.hide_task_progress()

    # ---------------------------------------------------------
    # Database refresh
    # ---------------------------------------------------------

    def refresh_from_database(self):

        global podcasts
        global SELECTED_PDC

        selected_title = None

        if self.selected_podcast:

            selected_title = (
                self.selected_podcast.title
            )

        podcasts = get_podcasts()

        if not podcasts:

            SELECTED_PDC = 0

            self.selected_podcast = None
            self.selected_episode = None
            self.search_query = ""
            self.visible_episodes = []

            self.refresh_podcast_list()
            self.refresh_episode_list()

            return

        if SELECTED_PDC >= len(podcasts):

            SELECTED_PDC = 0

        new_selected = None

        if selected_title:

            for podcast in podcasts:

                if (
                    podcast.title
                    == selected_title
                ):

                    new_selected = podcast

                    break

        if new_selected is None:

            new_selected = podcasts[
                SELECTED_PDC
            ]

        self.selected_podcast = new_selected
        self.search_query = ""
        self.visible_episodes = []

        self.refresh_podcast_list()
        self.refresh_episode_list()

        self.set_task_status(
            "Refreshed."
        )

    # ---------------------------------------------------------
    # Progress bar
    # ---------------------------------------------------------

    def make_progress_bar(
        self,
        percentage,
        width=30,
    ):

        percentage = max(
            0,
            min(
                100,
                percentage,
            ),
        )

        filled = int(
            (percentage / 100)
            * width
        )

        empty = width - filled

        return (
            "["
            + "■" * filled
            + "□" * empty
            + "]"
        )

    def update_playback_bar(
        self,
        current,
        total,
    ):

        widget = self.query_one(
            "#progress",
            Static,
        )

        if total <= 0:

            widget.update(
                "[□□□□□□□□□□□□□□"
                "□□□□□□□□□□□□□□]"
                " 00:00 / 00:00"
            )

            return

        percentage = (
            current / total
        ) * 100

        bar = self.make_progress_bar(
            percentage,
            30,
        )

        current_min, current_sec = divmod(
            int(current),
            60,
        )

        total_min, total_sec = divmod(
            int(total),
            60,
        )

        widget.update(
            f"{bar} "
            f"{current_min:02}:{current_sec:02} / "
            f"{total_min:02}:{total_sec:02}"
        )

    def update_task_progress(
        self,
        percentage,
    ):

        bar = self.make_progress_bar(
            percentage,
            30,
        )

        self.query_one(
            "#task-progress",
            Static,
        ).update(
            f"{bar} {percentage:.0f}%"
        )

    def show_task_progress(self):

        self.query_one(
            "#task-progress",
            Static,
        ).display = True

    def hide_task_progress(self):

        self.query_one(
            "#task-progress",
            Static,
        ).display = False

    def set_task_status(
        self,
        message,
    ):

        self.query_one(
            "#message",
            Static,
        ).update(
            message
        )

    # ---------------------------------------------------------
    # Podcast / episode highlighting
    # ---------------------------------------------------------

    def on_list_view_highlighted(
        self,
        event: ListView.Highlighted,
    ):

        global SELECTED_PDC

        podcast_list = self.query_one(
            "#podcast-list",
            ListView,
        )

        episode_list = self.query_one(
            "#episodes-list",
            ListView,
        )

        # Get index from event - Textual's Highlighted event may not have index
        index = getattr(event, 'index', None)
        if index is None:
            # Try to get from item
            if hasattr(event, 'item') and event.item is not None:
                # Get index from the list view
                if event.list_view == podcast_list:
                    index = podcast_list.index
                elif event.list_view == episode_list:
                    index = episode_list.index

        if event.list_view == podcast_list:

            if not podcasts:
                return

            if index is None or index < 0:
                return

            if index >= len(podcasts):
                return

            SELECTED_PDC = index

            self.selected_podcast = podcasts[
                index
            ]

            self.selected_episode = None

            self.refresh_episode_list()

            return

        if event.list_view == episode_list:

            if self.selected_podcast is None:
                return

            if index is None or index < 0:
                return

            # Use visible_episodes when search is active, otherwise use all episodes
            episodes = (
                self.visible_episodes
                if self.search_query
                else self.selected_podcast.episodes
            )

            if index >= len(episodes):
                return

            self.selected_episode = episodes[
                index
            ]

    # ---------------------------------------------------------
    # Enter selection
    # ---------------------------------------------------------

    def on_list_view_selected(
        self,
        event: ListView.Selected,
    ):

        global SELECTED_PDC

        podcast_list = self.query_one(
            "#podcast-list",
            ListView,
        )

        episode_list = self.query_one(
            "#episodes-list",
            ListView,
        )

        queue_list = self.query_one(
            "#queue-list",
            ListView,
        )

        # -----------------------------------------------------
        # Podcast
        # -----------------------------------------------------

        if event.list_view == podcast_list:

            if not podcasts:
                return

            SELECTED_PDC = event.index

            self.selected_podcast = podcasts[
                event.index
            ]

            self.selected_episode = None

            self.refresh_episode_list()

            # IMPORTANT:
            #
            # Changing podcasts does NOT stop playback.
            #
            # Only selected_podcast changes.
            #
            # playing_podcast
            # playing_episode
            # current_player
            #
            # remain untouched.

            self.set_task_status(
                f"Selected: "
                f"{self.selected_podcast.title}"
            )

            return

        # -----------------------------------------------------
        # Episode
        # -----------------------------------------------------

        if event.list_view == episode_list:

            if self.selected_podcast is None:
                return

            if event.index < 0:
                return

            # Use visible_episodes when search is active, otherwise use all episodes
            episodes = (
                self.visible_episodes
                if self.search_query
                else self.selected_podcast.episodes
            )

            if event.index >= len(episodes):
                return

            episode = episodes[
                event.index
            ]

            self.selected_episode = episode

            self.play_episode(
                self.selected_podcast,
                episode,
            )

            return

        # -----------------------------------------------------
        # Queue
        # -----------------------------------------------------

        if event.list_view == queue_list:

            self.play_queue_item(
                event.index
            )

    # ---------------------------------------------------------
    # List rendering
    # ---------------------------------------------------------

    def add_episode_list_item(
        self,
        list_view,
        episode,
    ):

        status = ""

        if episode.is_downloaded:

            status += "[D] "

        if episode.watched:

            status += "[W] "

        if (
            self.playing_episode is episode
        ):

            status += "[>] "

        # Use markup=False to safely render user-controlled strings
        list_view.append(
            ListItem(
                Label(
                    f"{status}"
                    f"{episode.title}",
                    markup=False,
                )
            )
        )

    def refresh_podcast_list(self):

        podcast_list = self.query_one(
            "#podcast-list",
            ListView,
        )

        podcast_list.clear()

        for podcast in podcasts:

            podcast_list.append(
                ListItem(
                    Label(
                        podcast.title,
                        markup=False,
                    )
                )
            )

    def refresh_episode_list(self):

        episodes_list = self.query_one(
            "#episodes-list",
            ListView,
        )

        episodes_list.clear()

        if self.selected_podcast is None:
            return

        for episode in (
            self.selected_podcast.episodes
        ):

            self.add_episode_list_item(
                episodes_list,
                episode,
            )

    # ---------------------------------------------------------
    # Queue
    # ---------------------------------------------------------

    def add_selected_to_queue(self):

        if self.selected_podcast is None:

            self.set_task_status(
                "Select a podcast first."
            )

            return

        if self.selected_episode is None:

            self.set_task_status(
                "Select an episode first."
            )

            return

        podcast = self.selected_podcast
        episode = self.selected_episode

        for item in self.queue:

            queued_episode = item[
                "episode"
            ]

            queued_podcast = item[
                "podcast"
            ]

            if (
                queued_podcast.id
                == podcast.id
                and queued_episode.guid
                == episode.guid
            ):

                self.set_task_status(
                    "Already in queue."
                )

                return

        self.queue.append(
            {
                "podcast": podcast,
                "episode": episode,
            }
        )

        self.refresh_queue_list()

        self.set_task_status(
            f"Queued: {episode.title}"
        )

    def remove_selected_queue_item(self):

        queue_list = self.query_one(
            "#queue-list",
            ListView,
        )

        index = queue_list.index

        if index < 0:

            self.set_task_status(
                "No queue item selected."
            )

            return

        if index >= len(self.queue):
            return

        removed = self.queue.pop(
            index
        )

        self.refresh_queue_list()

        self.set_task_status(
            f"Removed: "
            f"{removed['episode'].title}"
        )

    def clear_queue(self):

        if not self.queue:

            self.set_task_status(
                "Queue is already empty."
            )

            return

        self.queue.clear()

        self.queue_index = 0

        self.refresh_queue_list()

        self.set_task_status(
            "Queue cleared."
        )

    def refresh_queue_list(self):

        queue_list = self.query_one(
            "#queue-list",
            ListView,
        )

        queue_list.clear()

        for index, item in enumerate(
            self.queue
        ):

            episode = item[
                "episode"
            ]

            if (
                episode
                is self.playing_episode
            ):

                prefix = "[>]"

            else:

                prefix = (
                    f"{index + 1:02}"
                )

            queue_list.append(
                ListItem(
                    Label(
                        f"{prefix} "
                        f"{episode.title}",
                        markup=False,
                    )
                )
            )

    # ---------------------------------------------------------
    # Queue playback
    # ---------------------------------------------------------

    def play_next(self):

        if not self.queue:

            self.set_task_status(
                "Queue is empty."
            )

            return

        item = self.queue.pop(
            0
        )

        self.queue_index = 0

        self.refresh_queue_list()

        self.play_episode(
            item["podcast"],
            item["episode"],
        )

    def play_queue_item(
        self,
        index,
    ):

        if index < 0:
            return

        if index >= len(self.queue):
            return

        item = self.queue.pop(
            index
        )

        self.refresh_queue_list()

        self.play_episode(
            item["podcast"],
            item["episode"],
        )

    # ---------------------------------------------------------
    # VLC lifecycle
    # ---------------------------------------------------------

    def release_current_player(self):

        player = self.current_player

        if player is None:
            return

        self.current_player = None

        try:

            player.event_manager().event_detach(
                vlc.EventType.MediaPlayerEndReached
            )

        except Exception:
            pass

        try:

            player.stop()

        except Exception:
            pass

        try:

            player.release()

        except Exception:
            pass

    # ---------------------------------------------------------
    # Play episode
    # ---------------------------------------------------------

    def play_episode(
        self,
        podcast,
        episode,
    ):

        self.release_current_player()

        self.playing_podcast = podcast
        self.playing_episode = episode

        if episode.is_downloaded:

            if not episode.local_path:

                self.set_task_status(
                    "Downloaded episode has no local path."
                )

                self.playing_podcast = None
                self.playing_episode = None

                return

            player = create_player(
                podcast.id,
                episode,
            )

        else:

            if not episode.audio_url:

                self.set_task_status(
                    "Episode has no audio URL."
                )

                self.playing_podcast = None
                self.playing_episode = None

                return

            player = create_network_player(
                podcast.id,
                episode,
            )

        self.current_player = player

        # Capture this exact player.
        #
        # This prevents an old VLC player's
        # EndReached event from advancing the
        # queue after another player has started.
        def on_end(event):

            self.call_from_thread(
                self.handle_playback_finished,
                player,
            )

        player.event_manager().event_attach(
            vlc.EventType.MediaPlayerEndReached,
            on_end,
        )

        # Update playing title with markup=False
        self.query_one(
            "#playing-title",
            Static,
        ).update(
            f"▶ {episode.title}"
        )

        self.update_playback_bar(
            0,
            0,
        )

        self.apply_playback_speed()
        self.update_speed_display()

        start_play(
            player
        )

        self.refresh_episode_list()
        self.refresh_queue_list()

        self.set_task_status(
            f"Playing "
            f"{self.playback_speed:.2f}x"
        )

    # ---------------------------------------------------------
    # Playback finished
    # ---------------------------------------------------------

    def handle_playback_finished(
        self,
        finished_player,
    ):

        if (
            finished_player
            is not self.current_player
        ):

            return

        finished_episode = (
            self.playing_episode
        )

        self.release_current_player()

        self.playing_episode = None
        self.playing_podcast = None

        self.query_one(
            "#playing-title",
            Static,
        ).update(
            "Nothing playing"
        )

        self.update_playback_bar(
            0,
            0,
        )

        self.refresh_episode_list()
        self.refresh_queue_list()

        if finished_episode:

            self.set_task_status(
                f"Finished: "
                f"{finished_episode.title}"
            )

        if self.queue:

            self.play_next()

    # ---------------------------------------------------------
    # Play / pause
    # ---------------------------------------------------------

    def toggle_playback(self):

        if self.current_player is None:

            if self.queue:

                self.play_next()

            else:

                self.set_task_status(
                    "Nothing is playing."
                )

            return

        if self.current_player.is_playing():

            pause_play(
                self.current_player
            )

            self.set_task_status(
                "Paused."
            )

        else:

            start_play(
                self.current_player
            )

            self.set_task_status(
                f"Playing "
                f"{self.playback_speed:.2f}x"
            )

    # ---------------------------------------------------------
    # Stop
    # ---------------------------------------------------------

    def stop_current(self):

        if self.current_player is None:

            self.set_task_status(
                "Nothing is playing."
            )

            return

        title = None

        if self.playing_episode:

            title = (
                self.playing_episode.title
            )

        self.release_current_player()

        self.playing_episode = None
        self.playing_podcast = None

        self.query_one(
            "#playing-title",
            Static,
        ).update(
            "Nothing playing"
        )

        self.update_playback_bar(
            0,
            0,
        )

        self.refresh_episode_list()
        self.refresh_queue_list()

        if title:

            self.set_task_status(
                f"Stopped: {title}"
            )

        else:

            self.set_task_status(
                "Stopped."
            )

    # ---------------------------------------------------------
    # Seek
    # ---------------------------------------------------------

    def seek(
        self,
        seconds,
    ):

        if self.current_player is None:
            return

        current = (
            self.current_player.get_time()
        )

        total = (
            self.current_player.get_length()
        )

        if current < 0:
            return

        new_time = (
            current
            + seconds * 1000
        )

        if total > 0:

            new_time = min(
                new_time,
                total,
            )

        new_time = max(
            0,
            new_time,
        )

        self.current_player.set_time(
            new_time
        )

    # ---------------------------------------------------------
    # Playback speed
    # ---------------------------------------------------------

    def change_playback_speed(
        self,
        amount,
    ):

        new_speed = (
            self.playback_speed
            + amount
        )

        new_speed = max(
            0.5,
            min(
                2.5,
                new_speed,
            ),
        )

        self.playback_speed = new_speed

        self.apply_playback_speed()
        self.update_speed_display()

        self.set_task_status(
            f"Playback speed: "
            f"{self.playback_speed:.2f}x"
        )

    def update_speed_display(self):
        """Update the persistent speed display in the player area."""
        speed_widget = self.query_one("#playback-speed", Static)
        speed_widget.update(f"Speed: {self.playback_speed:.2f}x")

    def apply_playback_speed(self):

        if self.current_player is None:
            return

        try:

            self.current_player.set_rate(
                self.playback_speed
            )

        except Exception:
            pass

    # ---------------------------------------------------------
    # Playback timer
    # ---------------------------------------------------------

    def update_player_time(self):

        if self.current_player is None:
            return

        current, total = get_timer(
            self.current_player
        )

        if current < 0:
            return

        if total <= 0:
            return

        current_seconds = (
            current / 1000
        )

        total_seconds = (
            total / 1000
        )

        self.update_playback_bar(
            current_seconds,
            total_seconds,
        )

    # ---------------------------------------------------------
    # Help
    # ---------------------------------------------------------

    def show_help(self):

        self.set_task_status(
            "Tab panels | "
            "Enter play | "
            "Space pause | "
            "a queue | "
            "n next | "
            "x remove | "
            "c clear | "
            "d download | "
            "A add podcast | "
            "u update | "
            "/ search | "
            "Esc clear search | "
            "j/l seek | "
            "[/] speed | "
            "s stop | "
            "r refresh | "
            "q quit"
        )

    def update_key_help(self):
        """Update the key-help widget with safe text (markup=False)."""
        key_help = self.query_one("#key-help", Static)
        key_help.update(
            "←/→ Panels | "
            "Tab Cycle | "
            "Enter Play | "
            "Space Pause | "
            "a Queue | "
            "n Next | "
            "x Remove | "
            "c Clear | "
            "d Download | "
            "A Add | "
            "u Update | "
            "/ Search | "
            "Esc Clear Search | "
            "j/l Seek | "
            "[/] Speed | "
            "s Stop | "
            "? Help | "
            "q Quit"
        )

    # ---------------------------------------------------------
    # Compose
    # ---------------------------------------------------------

    def compose(self) -> ComposeResult:

        yield Header(
            show_clock=True,
            name="Podcatcher",
        )

        with Horizontal(
            id="main-content"
        ):

            # -------------------------------------------------
            # Podcasts
            # -------------------------------------------------

            with Vertical(
                id="podcasts"
            ):

                yield Static(
                    "Podcasts",
                    classes="section-title",
                )

                yield ListView(
                    id="podcast-list"
                )

            # -------------------------------------------------
            # Episodes
            # -------------------------------------------------

            with Vertical(
                id="episodes"
            ):

                yield Static(
                    "Episodes",
                    classes="section-title",
                )

                yield ListView(
                    id="episodes-list"
                )

            # -------------------------------------------------
            # Queue
            # -------------------------------------------------

            with Vertical(
                id="queue-panel"
            ):

                yield Static(
                    "Queue",
                    classes="section-title",
                )

                yield ListView(
                    id="queue-list"
                )

        # -----------------------------------------------------
        # Player
        # -----------------------------------------------------

        with Vertical(
            id="player-area"
        ):

            yield Static(
                "Nothing playing",
                id="playing-title",
            )

            yield Static(
                "[□□□□□□□□□□□□□□"
                "□□□□□□□□□□□□□□]"
                " 00:00 / 00:00",
                id="progress",
            )

            yield Static(
                "Speed: 1.00x",
                id="playback-speed",
            )

            yield Static(
                "Ready.",
                id="message",
            )

            yield Static(
                "[□□□□□□□□□□□□□□"
                "□□□□□□□□□□□□□□]"
                " 0%",
                id="task-progress",
            )

            yield Input(
                placeholder="Command...",
                id="command-input",
            )

        # Use markup=False to avoid MarkupError from [/] in help text
        yield Static(
            "←/→ Panels | "
            "Tab Cycle | "
            "Enter Play | "
            "Space Pause | "
            "a Queue | "
            "n Next | "
            "x Remove | "
            "c Clear | "
            "d Download | "
            "A Add | "
            "u Update | "
            "/ Search | "
            "j/l Seek | "
            "[/] Speed | "
            "s Stop | "
            "? Help | "
            "q Quit",
            id="key-help",
            markup=False,
        )

        yield Footer()

    # ---------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------

    def on_unmount(self):

        if self.current_player is not None:

            self.release_current_player()


if __name__ == "__main__":

    app = PodcatcherApp()
    app.run()