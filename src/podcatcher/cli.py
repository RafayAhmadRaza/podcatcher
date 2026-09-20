from feeds import get_feed
import argparse
from models import Podcast


parser = argparse.ArgumentParser(
    prog="Podcatcher",
    description="A Program To Fetch,Listen And Download Podcasts",
    epilog="Made By Rafay Ahmad Raza"
)

parser.add_argument('-a','--add')
parser.add_argument('-l','--list',action='store_true')
parser.add_argument('-u','--update')
parser.add_argument('-r','--remove')





args = parser.parse_args()
TEST_PODCASTS = {
    "kate_and_veronica": "https://kateandveronica.net/feed.xml",
    "something_scary": "https://feeds.megaphone.fm/somethingscary",

    "linux_unplugged": "https://linuxunplugged.com/rss",
    "darknet_diaries": "https://podcast.darknetdiaries.com/",
    "99_percent_invisible": "https://feeds.simplecast.com/BqbsxVfO",
    "welcome_to_night_vale": "https://feeds.nightvalepresents.com/welcometonightvalepodcast",
    "no_such_thing_as_a_fish": "https://audioboom.com/channels/2399216.rss",
}


podcast = []
for name,url in TEST_PODCASTS.items():
    podcast.append(get_feed(url))

if args.add:
    feed_link = args.add
    print(feed_link)
    podcast.append(get_feed(feed_link))

if args.remove:
    for pdc in podcast:
        if pdc.title == args.remove:
            podcast.remove(pdc)
            break

if args.update:
    name = args.update
    old_podcast = ''
    for pdc in podcast:
        if pdc.title == name: 
            old_podcast = pdc
            break
    if old_podcast:
        new_feed = get_feed(old_podcast.rss_url)
    
        
        old_episode_guids = {episode.guid for episode in old_podcast.episodes}

        for episode in new_feed.episodes:
            if episode.guid not in old_episode_guids:
                old_podcast.episodes.append(episode)
    else:
        print(f"Podcast '{name}' not found")


if args.list:
    print(podcast)
        