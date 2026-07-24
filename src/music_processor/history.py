import json
import uuid
from datetime import datetime
from pathlib import Path

HISTORY_PATH = Path.home() / ".music-processor" / "history.json"


def load_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_entry(name: str, source: str, key: str, bpm: float, output_dir: str) -> None:
    entry = {
        "id": str(uuid.uuid4()),
        "name": name,
        "source": source,
        "analyzed_at": datetime.now().isoformat(),
        "key": key,
        "bpm": bpm,
        "output_dir": output_dir,
    }
    history = load_history()
    history.insert(0, entry)
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def delete_entry(entry_id: str) -> None:
    history = [e for e in load_history() if e.get("id") != entry_id]
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
