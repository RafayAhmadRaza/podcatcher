from pathlib import Path
import vlc
import time

is_playing = False
is_resumeable = False
is_paused = False
is_done = False

def create_player(podcast_id,episode):

    player = vlc.MediaPlayer(episode.local_path)
    return player

def start_play(player:vlc.MediaPlayer):
    global is_playing, is_resumeable, is_paused
    is_playing = True
    is_resumeable = False
    is_paused = False

    player.play()


def pause_play(player:vlc.MediaPlayer):
    global is_resumeable, is_paused
    is_resumeable = True
    is_paused = True

    player.pause()

def stop_play(player:vlc.MediaPlayer):
    global is_playing, is_resumeable, is_paused
    player.stop()
    is_playing, is_resumeable, is_paused = False, False, False

def done_playback(event=None):
    global is_playing, is_resumeable, is_paused,is_done
    is_playing = False
    is_resumeable = False
    is_paused = False
    is_done = True    

if __name__ == "__main__":

    music_path = Path.home() / "Music" / "Linkin Park - 2024 - From Zero [Cassette]" / "04. Heavy Is the Crown.flac"

    pID,player,ep = create_player(music_path)
    # player = create_player("/home/rafayahmadraza/Music/Linkin Park - 2024 - From Zero [Cassette]/04. Heavy Is the Crown.flac")
    event_manager = player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached,
    done_playback)
    print("playing")

    start_play(player)

    
    while is_playing or is_resumeable:
        time.sleep(1)
    
