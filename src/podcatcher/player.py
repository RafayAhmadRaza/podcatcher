from pathlib import Path
import vlc
import time

is_playing = False
def create_player(path:str):
    player = vlc.MediaPlayer(path)
    return player

def start_play(player:vlc.MediaPlayer):
    global is_playing 
    is_playing = True
    player.play()


def pause_play(player:vlc.MediaPlayer):

    player.pause()

def stop_play(player:vlc.MediaPlayer):

    player.stop()

def done_playback(event=None):
    global is_playing
    is_playing = False
    print("Done Playing")
    

if __name__ == "__main__":

    music_path = Path.home() / "Music" / "Linkin Park - 2024 - From Zero [Cassette]" / "04. Heavy Is the Crown.flac"

    player = create_player(music_path)
    # player = create_player("/home/rafayahmadraza/Music/Linkin Park - 2024 - From Zero [Cassette]/04. Heavy Is the Crown.flac")
    event_manager = player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached,
    done_playback)
    print("playing")

    start_play(player)

    
    while is_playing:
        time.sleep(1)
    
