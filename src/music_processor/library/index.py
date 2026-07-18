import json
import os
import re
import sqlite3
import unicodedata
from pathlib import Path

LIBRARY_PATH = Path(os.environ.get("CHORD_LIBRARY", Path.home() / "chord-library"))


def _sqlite_db() -> Path | None:
    """Return path to SQLite index if available (env var or auto-detected)."""
    env = os.environ.get("CHORD_LIBRARY_DB")
    if env:
        return Path(env)
    for candidate in (LIBRARY_PATH / "library.db", LIBRARY_PATH.parent / "library.db"):
        if candidate.exists():
            return candidate
    return None


def get_artists() -> list[dict]:
    """Return [{slug, name}] sorted by name.

    Uses SQLite index when available (CHORD_LIBRARY_DB or auto-detected
    library.db), otherwise scans the filesystem (slower on first call).
    """
    db = _sqlite_db()
    if db:
        try:
            with sqlite3.connect(db) as conn:
                rows = conn.execute(
                    "SELECT slug, name FROM artists WHERE status='done' ORDER BY name COLLATE NOCASE"
                ).fetchall()
            return [{"slug": slug, "name": name} for slug, name in rows]
        except Exception:
            pass
    return _scan_artists()


def _scan_artists() -> list[dict]:
    artists: list[dict] = []
    for artist_dir in sorted(LIBRARY_PATH.iterdir()):
        if not artist_dir.is_dir():
            continue
        name: str | None = None
        for song_dir in artist_dir.iterdir():
            meta_file = song_dir / "meta.json"
            if meta_file.exists():
                try:
                    data = json.loads(meta_file.read_text(encoding="utf-8"))
                    name = data.get("artist")
                    break
                except Exception:
                    pass
        artists.append({
            "slug": artist_dir.name,
            "name": name or artist_dir.name.replace("_", " ").title(),
        })
    return sorted(artists, key=lambda a: a["name"].lower())


def get_songs(artist_slug: str) -> list[dict]:
    artist_dir = LIBRARY_PATH / artist_slug
    songs: list[dict] = []
    for song_dir in artist_dir.iterdir():
        if not song_dir.is_dir():
            continue
        meta_file = song_dir / "meta.json"
        if meta_file.exists():
            try:
                songs.append(json.loads(meta_file.read_text(encoding="utf-8")))
            except Exception:
                pass
    return sorted(songs, key=lambda s: s.get("title", "").lower())


def _normalize(text: str) -> str:
    """Lowercase + strip accents so 'mana' matches 'Maná'."""
    return unicodedata.normalize("NFD", text.lower()).encode("ascii", "ignore").decode("ascii")


def _acronym_score(query: str, words: list[str]) -> int:
    """Match query consumed word-by-word from the start of each word.

    Handles:
      "vp"     → "Violeta Parra"   (pure initials)
      "vparra" → "Violeta Parra"   (initial + word continuation)
      "gc"     → "Gustavo Cerati"  (pure initials)

    Matches starting at earlier words score higher, so "gc" prefers
    "Gustavo Cerati" over "Cliver y su Grupo Coralí".
    """
    qi = 0
    first_match_word = -1
    for wi, word in enumerate(words):
        if qi >= len(query):
            break
        matched = 0
        for wc in word:
            if qi + matched < len(query) and wc == query[qi + matched]:
                matched += 1
            else:
                break
        if matched > 0:
            if first_match_word == -1:
                first_match_word = wi
            qi += matched

    if qi == len(query):
        # Penalise matches that start late in the name (2 pts per skipped word)
        return max(70, 86 - first_match_word * 2)
    coverage = qi / len(query)
    return int(70 * coverage) if coverage >= 0.5 else 0


def _score(query: str, candidate: str) -> int:
    """Word-boundary-aware score: prefix of any word scores high, fuzzy as fallback."""
    from rapidfuzz import fuzz

    words = candidate.split()
    for word in words:
        if word == query:
            return 100
        if word.startswith(query):
            return 90
    acr = _acronym_score(query, words)
    if acr > 0:
        return acr
    return int(fuzz.token_sort_ratio(query, candidate))


def fuzzy_search_artists(query: str, artists: list[dict], limit: int = 60) -> list[dict]:
    q = _normalize(query)
    scored = [
        (score, a)
        for a in artists
        if (score := _score(q, _normalize(a["name"]))) > 40
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:limit]]


def fuzzy_search_songs(query: str, songs: list[dict], limit: int = 60) -> list[dict]:
    if not songs:
        return []
    q = _normalize(query)
    scored = [
        (score, s)
        for s in songs
        if (score := _score(q, _normalize(s.get("title", "")))) > 40
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:limit]]


def get_song_content(artist_slug: str, song_slug: str, filename: str) -> str:
    path = LIBRARY_PATH / artist_slug / song_slug / filename
    text = path.read_text(encoding="utf-8", errors="replace")
    return _strip_boilerplate(text)


def _strip_boilerplate(text: str) -> str:
    lines = text.splitlines()
    sep_positions = [i for i, line in enumerate(lines) if line.startswith("===")]

    if len(sep_positions) < 3:
        return text

    content_start = sep_positions[2] + 1
    # Footer starts at the second-to-last separator (two footer === lines)
    content_end = sep_positions[-2] if len(sep_positions) >= 4 else sep_positions[-1]

    return "\n".join(lines[content_start:content_end]).strip()


def embed_to_watch_url(embed_url: str) -> str | None:
    match = re.search(r"/embed/([a-zA-Z0-9_-]+)", embed_url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return None
