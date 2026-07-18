import subprocess
import sys
from pathlib import Path
from typing import Callable


def separate_stems(
    audio_path: Path,
    output_dir: Path,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "demucs",
        "--mp3",
        "-o", str(output_dir),
        str(audio_path),
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
        raise RuntimeError(
            "Demucs falló. Instalalo con: pip install demucs"
        )

    # Demucs outputs to: output_dir/htdemucs/<song_stem>/<drum|bass|vocals|other>.mp3
    stems_dir = output_dir / "htdemucs" / audio_path.stem
    stems: dict[str, Path] = {}
    for stem_name in ("drums", "bass", "vocals", "other"):
        candidate = stems_dir / f"{stem_name}.mp3"
        if candidate.exists():
            stems[stem_name] = candidate

    if not stems:
        raise RuntimeError(
            f"No se generaron stems en {stems_dir}. Verificá la instalación de Demucs."
        )

    return stems
