import re
import subprocess
from pathlib import Path
from typing import Callable


def is_youtube_url(source: str) -> bool:
    return bool(re.match(r"https?://(www\.)?(youtube\.com|youtu\.be)/", source))


def download_audio(
    url: str,
    output_dir: Path,
    progress_callback: Callable[[str], None] | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    template = str(output_dir / "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--no-playlist",
        "--progress",
        "-o", template,
        url,
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    for line in process.stdout:
        line = line.strip()
        if line and progress_callback:
            progress_callback(line)

    process.wait()
    if process.returncode != 0:
        raise RuntimeError("yt-dlp falló al descargar el audio")

    mp3_files = list(output_dir.glob("*.mp3"))
    if not mp3_files:
        raise RuntimeError("No se encontró el archivo de audio descargado")

    return max(mp3_files, key=lambda f: f.stat().st_mtime)
