from dataclasses import dataclass
@dataclass
class Episode:
    title:str
    published:str
    audio_url:str | None
    guid:str
    is_downloaded: bool = False
    local_path: str | None = None

@dataclass
class Podcast:
    title:str
    description:str
    website:str
    rss_url:str
    episodes:[]
    id:int | None = None