import httpx
from pathlib import Path
path = Path("Podcaster/downloader")


def download_ep(url):
    file_path = path / "episode.mp3"

    if file_path.exists():
        print("Already downloaded")
        return

    path.mkdir(parents=True, exist_ok=True)

    file = httpx.get(url, follow_redirects=True)
    file.raise_for_status()

    with open(file_path, "wb") as f:
        f.write(file.content)


if __name__ == "__main__":
    download_ep("https://dts.podtrac.com/redirect.mp3/mgln.ai/e/211/rss.art19.com/episodes/761a2733-c9c2-4fec-8c15-627cd3472417.mp3")