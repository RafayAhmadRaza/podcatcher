from .database import *
from .feeds import get_feed
from .models import Podcast
from .downloader import download_ep
from . import player
import argparse
import time
import vlc
import os
connection = get_connection()

create_db(connection)

parser = argparse.ArgumentParser(
    prog="Podcatcher",
    description="A Program To Fetch,Listen And Download Podcasts",
    epilog="Made By Rafay Ahmad Raza"
)

parser.add_argument('-a','--add')
parser.add_argument('-l','--list',action='store_true')
parser.add_argument('-u','--update')
parser.add_argument('-r','--remove')
parser.add_argument('-d', '--download')
parser.add_argument('-p', '--play')




def search_in_podcast_list(title:str):
    podcasts = get_podcasts()
    for pdc in podcasts:
        if pdc.title == title:
            return pdc
    return None
        

args = parser.parse_args()
# TEST_PODCASTS = {
#     "kate_and_veronica": "https://kateandveronica.net/feed.xml",
#     "something_scary": "https://feeds.megaphone.fm/somethingscary",

#     "linux_unplugged": "https://linuxunplugged.com/rss",
#     "darknet_diaries": "https://podcast.darknetdiaries.com/",
#     "99_percent_invisible": "https://feeds.simplecast.com/BqbsxVfO",
#     "welcome_to_night_vale": "https://feeds.nightvalepresents.com/welcometonightvalepodcast",
#     "no_such_thing_as_a_fish": "https://audioboom.com/channels/2399216.rss",
# }


podcast = []
# for name,url in TEST_PODCASTS.items():
#     podcast.append(get_feed(url))

if args.add:
    feed_link = args.add
    print(feed_link)
    podcast = get_feed(feed_link)

    add_podcast(podcast)

if args.remove:
    podcast = search_in_podcast_list(args.remove)
    if podcast == None:
        print(f"Podcast Name {args.remove} does not exists")
    else:
        remove_podcast(podcast)


if args.update:
    name = args.update
    old_podcast = search_in_podcast_list(name) 
    
    if old_podcast:
        update_podcast(old_podcast)
    
    else:
        print(f"Podcast '{name}' not found")


if args.download:
    name = args.download
    podcast_to_download = search_in_podcast_list(name)
    
    if podcast_to_download == None:
        print("Error Podcast Does Not Exist Or Has Not Being Added")
    else:
        episode_count = len(podcast_to_download.episodes)
        
        for i,ep in enumerate(podcast_to_download.episodes,start=1):
            print(str(i) + " "+ ep.title+" "+ ep.published)

        choice = int(input("Select Episode to download: "))-1

        if choice>=episode_count:
            print("Episode Does Not Exist, Please Fetch the latest episodes")
        else:
            episode = podcast_to_download.episodes[choice]

            if episode.watched:
                choice = input("Episode already watched. Redownload? [y/N]: ")
            
            if choice.lower() != "y":
                print("Download cancelled.")
            else:
                    
                is_downloaded,local_path = download_ep(podcast_to_download.title,episode.title,episode.audio_url)

                if is_downloaded == False:
                    print("Download Failed")
                else:
                    set_download(podcast_to_download.id,episode,is_downloaded,local_path)
            
if args.play:
    pdName = args.play
    podcast = search_in_podcast_list(pdName)

    if podcast is None:
        print(f"Podcast '{pdName}' does not exist")

    else:
        downloaded_episodes = []

        for ep in podcast.episodes:
            if ep.is_downloaded:
                downloaded_episodes.append(ep)

        if not downloaded_episodes:
            print("No downloaded episodes available")

        else:
            for i, ep in enumerate(downloaded_episodes, start=1):
                print(f"[{'Watched' if ep.watched else 'Unwatched'}] [{'Downloaded' if ep.is_downloaded else 'Not Downloaded'}] {i} {ep.title}")

            choice = int(input("Enter Episode Choice: ")) - 1

            if choice < 0 or choice >= len(downloaded_episodes):
                print("Episode is not available")

            else:
                ep = downloaded_episodes[choice]

                media_player = player.create_player(podcast.id, ep)
                player.start_play(media_player)
                event_manager = media_player.event_manager()
                event_manager.event_attach(vlc.EventType.MediaPlayerEndReached,
                player.done_playback)

                while player.is_playing or player.is_resumeable:
                    
                    command = input("Commnad: ")


                    match command:
                        case "p":
                            if player.is_playing:
                                player.pause_play(media_player)
                            elif player.is_paused and player.is_resumeable:
                                player.start_play(media_player)

                        case "s":
                            player.stop_play(media_player)
                    
                    time.sleep(1)

                if player.is_done:
                    os.unlink(ep.local_path)           
                    remove_episode(podcast.id,ep)


                    

if args.list:
    podcasts = get_podcasts()

    print(podcasts)
        