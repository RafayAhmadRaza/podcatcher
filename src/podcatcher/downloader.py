import httpx
from pathlib import Path
path = Path("Podcaster/downloader")


def download_ep(title:str,episode_name:str,url:str) -> None:
    file_path = path / title /f"{episode_name}.mp3"

    if file_path.exists():
        print("Already downloaded")
        return True, file_path

    
    path.mkdir(parents=True, exist_ok=True)
    file_path.parent.mkdir(parents=True,exist_ok=True)

    with httpx.stream("GET",url,follow_redirects=True) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length",0))

        with open(file_path,"wb") as f:
            downloaded = 0
            for chunk in response.iter_bytes():
                f.write(chunk)
                downloaded +=len(chunk)


                print(downloaded,total)

            return True,file_path
    
if __name__ == "__main__":
    download_ep("LINUX Unplugged","Episode Test 1: Too Much Choice","https://dts.podtrac.com/redirect.mp3/mgln.ai/e/211/rss.art19.com/episodes/761a2733-c9c2-4fec-8c15-627cd3472417.mp3")