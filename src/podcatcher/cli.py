from database import get_connection,create_db,add_podcast,remove_podcast,get_podcasts,update_podcast, set_download
from feeds import get_feed
import argparse
from models import Podcast
from downloader import download_ep

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
    podcast = get_podcasts()
    for pdc in podcast:
        if pdc.title == args.remove:
            podcast.remove(pdc)
            remove_podcast(pdc)
            break

if args.update:
    podcast = get_podcasts()
    name = args.update
    old_podcast = ''
    for pdc in podcast:
        if pdc.title == name: 
            old_podcast = pdc
            break
    if old_podcast:
        update_podcast(old_podcast)
    
    else:
        print(f"Podcast '{name}' not found")


if args.download:
    podcasts = get_podcasts()

    name = args.download
    podcast_to_download = None
    for pdc in podcasts:
        if pdc.title == name:
            podcast_to_download = pdc
            break
        print(pdc.title)
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

            is_downloaded,local_path = download_ep(podcast_to_download.title,episode.title,episode.audio_url)

            if is_downloaded == False:
                print("Download Failed")
            else:
                set_download(podcast_to_download.id,episode,is_downloaded,local_path)
                
            


if args.list:
    podcasts = get_podcasts()

    print(podcasts)
        