from pathlib import Path
import re

import httpx


def sanitize_filename(name: str, max_length: int = 180) -> str:
    """Make a podcast title safe to use as a filename."""

    # Remove characters that are invalid/problematic in filenames.
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)

    # Collapse repeated whitespace.
    name = re.sub(r"\s+", " ", name).strip()

    # Avoid filenames ending with a period or space.
    name = name.rstrip(". ")

    # Prevent empty filenames.
    if not name:
        name = "episode"

    # Keep filenames at a reasonable length.
    name = name[:max_length].rstrip(". ")

    return name


def download_ep(
    podcast_title,
    episode_title,
    audio_url,
    progress_callback=None,
):
    download_dir = (
        Path.home()
        / "Podcasts"
        / sanitize_filename(podcast_title)
    )

    download_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{sanitize_filename(episode_title)}.mp3"
    file_path = download_dir / filename
    partial_path = Path(str(file_path) + ".part")

    downloaded = 0

    if partial_path.exists():
        downloaded = partial_path.stat().st_size

    headers = {}

    if downloaded > 0:
        headers["Range"] = f"bytes={downloaded}-"

    try:
        with httpx.stream(
            "GET",
            audio_url,
            headers=headers,
            follow_redirects=True,
            timeout=None,
        ) as response:

            response.raise_for_status()

            # Server accepted our Range request.
            if response.status_code == 206:
                mode = "ab"

                total = downloaded + int(
                    response.headers.get(
                        "Content-Length",
                        0,
                    )
                )

            # Server ignored Range and is sending
            # the entire file again.
            elif response.status_code == 200:
                mode = "wb"
                downloaded = 0

                total = int(
                    response.headers.get(
                        "Content-Length",
                        0,
                    )
                )

            else:
                return False, None

            current = downloaded

            with open(partial_path, mode) as file:
                for chunk in response.iter_bytes(
                    chunk_size=1024 * 1024
                ):
                    if not chunk:
                        continue

                    file.write(chunk)
                    current += len(chunk)

                    if progress_callback:
                        progress_callback(
                            current,
                            total,
                        )

        partial_path.replace(file_path)

        if progress_callback:
            progress_callback(
                total,
                total,
            )

        return True, str(file_path)

    except (
        OSError,
        httpx.HTTPError,
    ):
        return False, None