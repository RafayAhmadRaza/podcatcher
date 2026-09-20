import httpx
from pathlib import Path
path = Path("Podcaster/downloader")


def download_ep(title,episode_name,url):
    file_path = path / title /f"{episode_name}.mp3"

    if file_path.exists():
        print("Already downloaded")
        return

    path.mkdir(parents=True, exist_ok=True)
    file_path.parent.mkdir(parents=True,exist_ok=True)
    file = httpx.get(url, follow_redirects=True)
    file.raise_for_status()

    with open(file_path, "wb") as f:
        f.write(file.content)


if __name__ == "__main__":
    download_ep("LINUX Unplugged","Episode 1: Too Much Choice","https://dts.podtrac.com/redirect.mp3/mgln.ai/e/211/rss.art19.com/episodes/761a2733-c9c2-4fec-8c15-627cd3472417.mp3")