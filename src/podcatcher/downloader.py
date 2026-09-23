import httpx
from pathlib import Path
import os
path = Path("podcatcher/downloader")


def download_ep(title:str,episode_name:str,url:str) -> None:
    file_path = path / title /f"{episode_name}.mp3"
    # file_path = Path(f"/root/{episode_name}.mp3")

    file_path_temp = Path(str(file_path) + ".part")
    resume_from = 0
    if file_path_temp.exists():
        print("Resuming File Download")
        resume_from = file_path_temp.stat().st_size
    
    headers = {}

    if resume_from >0:
        headers["Range"] = f"bytes={resume_from}-"

    
    

    try:
        with httpx.stream("GET",url,headers=headers,follow_redirects=True) as response:
                response.raise_for_status()
            
                write_instrction = 'wb'
                if file_path.exists():
                    print("Already downloaded")
                    return True, file_path
                path.mkdir(parents=True, exist_ok=True)
                file_path.parent.mkdir(parents=True,exist_ok=True)
            

                content_length = int(response.headers.get("content-length",0))
                if response.status_code == 200:
                    write_instrction = 'wb'
                    total = content_length                
                if response.status_code == 206:
                    write_instrction = 'ab'
                    total = resume_from + content_length

                with open(file_path_temp,write_instrction) as f:

                        downloaded = resume_from
                        for chunk in response.iter_bytes():
                            f.write(chunk)
                            downloaded +=len(chunk)


                            print(downloaded,total)

                        os.rename(file_path_temp,file_path)

                        return True,file_path
    except OSError as exc:
        print(f"OS Error for {exc}")
        return False,None


                    
    except httpx.HTTPError as exc:
            print(f"HTTP Exception for {exc}")
            return False,None
        
if __name__ == "__main__":
    download_ep("LINUX Unplugged","Episode Test 1: Too Much Choice","https://dts.podtrac.com/redirect.mp3/mgln.ai/e/211/rss.art19.com/episodes/761a2733-c9c2-4fec-8c15-627cd3472417.mp3")