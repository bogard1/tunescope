# tunescope

TUI for audio analysis and chord library browsing, built with [Textual](https://textual.textualize.io/).

[Leer en Español](README.es.md)

## Installation

```bash
make install
```

Creates a virtualenv at `venv/` and installs all dependencies. For stem separation (requires PyTorch, ~2 GB):

```bash
venv/bin/pip install demucs
```

## Usage

```bash
make run
# or directly:
venv/bin/music-tui
```

## Features

### Process Audio

Accepts a local audio file or a YouTube URL and runs the full pipeline:

1. **Download** audio via `yt-dlp` (if a YouTube URL is given)
2. **Separate instruments** with [Demucs](https://github.com/facebookresearch/demucs): drums, bass, vocals, other
3. **Analyze** the `other` stem (harmonics without vocals or percussion):
   - Key — Krumhansl-Kessler profiles on chroma CQT
   - BPM — `librosa.beat.beat_track`
   - Chords — template matching on chroma (24 chords: 12 major + 12 minor)
4. **Save** `results.json` alongside the stems at `~/.music-processor/stems/<song>/`

From the results screen each stem can be played back with `mpv` or `ffplay`.

### Chord Library

Browse and search a local chord library. Search supports:

- Partial text: `soda` → Soda Stereo
- Without accents: `beatles` → The Beatles
- Initials: `gc` → Gustavo Cerati, `vp` → Violeta Parra
- Initials + continuation: `vparra` → Violeta Parra

**Two-step search flow:**

1. Search for the artist → Enter to select
2. Search for a song within their catalogue → Enter to open
3. ESC returns to the artist list

**Inside a song screen:**

- Numbered buttons to switch between versions (chords / tab / bass / harmonica / etc.)
- Keys **1–N** to switch versions from the keyboard
- **▶ Watch on YouTube** — opens the video in the default browser
- **⬇ Download + Separate** — downloads the audio and runs the analysis pipeline
- **⬡ Export PDF** — generates a multi-column PDF optimized to fit on as few pages as possible, saved to `~/Downloads/`

---

## Chord Library Format

The library is a directory with the following structure:

```
<library-root>/
├── {artist_slug}/
│   ├── {song_slug}/
│   │   ├── meta.json
│   │   ├── version_main.txt
│   │   ├── version_2.txt        ← additional versions (optional)
│   │   └── version_3.txt
│   └── {another_song_slug}/
│       ├── meta.json
│       └── version_main.txt
└── {another_artist_slug}/
    └── ...
```

Slugs use lowercase and underscores (`violeta_parra`, `la_cancion`).

### meta.json

Each song requires a `meta.json` file with the following schema:

```json
{
  "title": "The Song",
  "artist": "The Artist",
  "artist_slug": "the_artist",
  "song_slug": "the_song",
  "youtube_url": "https://www.youtube.com/embed/VIDEO_ID",
  "versions": [
    {
      "version_num": 1,
      "type": "chords",
      "file": "version_main.txt",
      "youtube_url": "https://www.youtube.com/embed/VIDEO_ID"
    },
    {
      "version_num": 2,
      "type": "tab",
      "file": "version_2.txt",
      "youtube_url": "https://www.youtube.com/embed/VIDEO_ID"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Song display name |
| `artist` | string | Artist display name |
| `artist_slug` | string | Must match the parent directory name |
| `song_slug` | string | Must match the song directory name |
| `youtube_url` | string \| null | YouTube embed URL (see format below) |
| `versions` | array | At least one version required |
| `versions[].version_num` | int | Version number (1, 2, 3…) |
| `versions[].type` | string | Type: `chords`, `tab`, `bass`, `harmonica`, `drums`, `ukulele`, `piano`, etc. |
| `versions[].file` | string | Text file name within the same directory |
| `versions[].youtube_url` | string \| null | Can repeat the root-level URL or differ |

### YouTube URL format

The `youtube_url` field must use the **embed** format, not the watch format:

```
✓  https://www.youtube.com/embed/VIDEO_ID
✗  https://www.youtube.com/watch?v=VIDEO_ID
✗  https://youtu.be/VIDEO_ID
```

The TUI automatically converts the embed format to the watch format for `yt-dlp` downloads and for opening in the browser.

Set to `null` if the song has no associated video; the YouTube buttons will not appear in that case.

### Content files (version_main.txt, version_2.txt…)

Plain text files with the chord/tab content. The TUI displays the content as-is, but automatically strips header and footer blocks delimited by `===` lines:

```
=====================================   ← stripped (header)
| ARTIST: The Artist                 |
| SONG:   The Song                   |
=====================================   ← stripped

[VISIBLE CONTENT: lyrics and chords]

=====================================   ← stripped (footer)
All rights reserved...
=====================================   ← stripped
```

If the file does not follow this format, it is displayed in full without modification.

### SQLite index (optional, for faster loading)

With thousands of artists, the initial load can be slow if the TUI has to read one `meta.json` per artist to get display names. A SQLite index can be provided with the following table:

```sql
CREATE TABLE artists (
    slug TEXT PRIMARY KEY,
    name TEXT,
    status TEXT DEFAULT 'done'
);
```

The TUI auto-detects it if a `library.db` file exists inside the library directory or its parent. The path can also be set explicitly with `CHORD_LIBRARY_DB` (see Environment variables).

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHORD_LIBRARY` | `~/chord-library` | Path to the chord library root directory |
| `CHORD_LIBRARY_DB` | auto-detected | Path to the artist index SQLite file (optional) |

Variables can be set in a `.env` file in the directory where you run `music-tui` — it is loaded automatically on startup. Copy the provided example to get started:

```bash
cp .env.example .env
# then edit .env with your paths
```

Or export them in your shell:

```bash
export CHORD_LIBRARY=/data/my-chords
export CHORD_LIBRARY_DB=/data/my-chords/library.db
make run
```

---

## System dependencies

| Tool | Purpose |
|------|---------|
| `yt-dlp` | YouTube download |
| `ffmpeg` | Audio conversion |
| `mpv` or `ffplay` | Stem playback in the TUI |

## Generated files

```
~/.music-processor/
├── downloads/          # audio downloaded from YouTube
└── stems/<song>/
    └── htdemucs/<song>/
        ├── drums.mp3
        ├── bass.mp3
        ├── vocals.mp3
        ├── other.mp3
        └── results.json    # detected key, BPM, and chords
```
