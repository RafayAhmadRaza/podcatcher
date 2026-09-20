from dataclasses import dataclass
@dataclass
class Episode:
    title:str
    published:str
    audio_url:str | None
    guid:str

@dataclass
class Podcast:
    title:str
    description:str
    website:str
    rss_url:str
    episodes:[]