
import feedparser
from models import Episode, Podcast


def get_feed(url):



    feed = feedparser.parse(url)

    title = feed.feed.title
    desc = feed.feed.description
    web_link = feed.feed.link

    episode_list = []
    for episode in feed.entries:
        if episode.enclosures:
            audio_url = episode.enclosures[0].href
        else:
            audio_url = None
        
        new_episode = Episode(
        title = episode.title,
        published = episode.published,
        audio_url = audio_url,
        guid=episode.guid,
        )
        episode_list.append(new_episode)
    podcast = Podcast(title=title,description=desc,website=web_link,episodes=episode_list)
    return podcast



if __name__ == "__main__":
    get_feed('https://feeds.megaphone.fm/somethingscary')
