from pathlib import Path
from typing import Callable

import numpy as np

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Krumhansl-Kessler key profiles
_MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

# Triads
_MAJOR_TMPL = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0], dtype=float)
_MINOR_TMPL = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0], dtype=float)
_DIM_TMPL   = np.array([1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0], dtype=float)
_AUG_TMPL   = np.array([1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0], dtype=float)
_SUS2_TMPL  = np.array([1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0], dtype=float)
_SUS4_TMPL  = np.array([1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0], dtype=float)
# Seventh chords
_DOM7_TMPL  = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0], dtype=float)
_MAJ7_TMPL  = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1], dtype=float)
_MIN7_TMPL  = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0], dtype=float)

CHORD_TEMPLATES: dict[str, np.ndarray] = {}
for _i, _note in enumerate(NOTES):
    CHORD_TEMPLATES[_note]          = np.roll(_MAJOR_TMPL, _i)
    CHORD_TEMPLATES[_note + "m"]    = np.roll(_MINOR_TMPL, _i)
    CHORD_TEMPLATES[_note + "dim"]  = np.roll(_DIM_TMPL,   _i)
    CHORD_TEMPLATES[_note + "aug"]  = np.roll(_AUG_TMPL,   _i)
    CHORD_TEMPLATES[_note + "sus2"] = np.roll(_SUS2_TMPL,  _i)
    CHORD_TEMPLATES[_note + "sus4"] = np.roll(_SUS4_TMPL,  _i)
    CHORD_TEMPLATES[_note + "7"]    = np.roll(_DOM7_TMPL,  _i)
    CHORD_TEMPLATES[_note + "maj7"] = np.roll(_MAJ7_TMPL,  _i)
    CHORD_TEMPLATES[_note + "m7"]   = np.roll(_MIN7_TMPL,  _i)


def _detect_key(chroma_mean: np.ndarray) -> str:
    best_key, best_corr = "C major", -np.inf
    for i, note in enumerate(NOTES):
        for mode, profile in (("major", _MAJOR_PROFILE), ("minor", _MINOR_PROFILE)):
            rotated = np.roll(profile, i)
            corr = float(np.corrcoef(chroma_mean, rotated)[0, 1])
            if corr > best_corr:
                best_corr = corr
                best_key = f"{note} {mode}"
    return best_key


def _detect_sections(chroma: np.ndarray, hop_length: int, sr: int) -> list[dict]:
    import librosa

    n_frames = chroma.shape[1]
    if n_frames < 4:
        return []
    k = min(5, max(2, n_frames // 50))

    try:
        bounds = librosa.segment.agglomerative(chroma, k=k)
        bound_times = librosa.frames_to_time(bounds, sr=sr, hop_length=hop_length)
        sections = []
        for i in range(len(bound_times) - 1):
            start = float(bound_times[i])
            end = float(bound_times[i + 1])
            sections.append({
                "label": "ABCDE"[i % 5],
                "time": round(start, 2),
                "end": round(end, 2),
                "duration": round(end - start, 2),
            })
        return sections
    except Exception:
        return []


def _detect_chords(chroma: np.ndarray, hop_length: int, sr: int) -> list[dict]:
    chord_names = list(CHORD_TEMPLATES.keys())
    templates = np.stack([CHORD_TEMPLATES[c] for c in chord_names])  # (n_chords, 12)

    norms = np.linalg.norm(chroma, axis=0, keepdims=True)
    norms[norms == 0] = 1.0
    chroma_norm = chroma / norms  # (12, n_frames)

    scores = templates @ chroma_norm  # (n_chords, n_frames)
    best_idx = np.argmax(scores, axis=0)  # (n_frames,)

    def frame_to_time(f: int) -> float:
        return round(f * hop_length / sr, 2)

    segments: list[dict] = []
    prev_chord: str | None = None
    start_frame = 0

    for i, idx in enumerate(best_idx):
        chord = chord_names[int(idx)]
        if chord != prev_chord:
            if prev_chord is not None:
                segments.append({
                    "time": frame_to_time(start_frame),
                    "chord": prev_chord,
                    "duration": frame_to_time(i - start_frame),
                })
            prev_chord = chord
            start_frame = i

    if prev_chord is not None:
        segments.append({
            "time": frame_to_time(start_frame),
            "chord": prev_chord,
            "duration": frame_to_time(len(best_idx) - start_frame),
        })

    return segments


def analyze(
    audio_path: Path,
    progress_callback: Callable[[str], None] | None = None,
) -> dict:
    import librosa

    def log(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    log("Cargando audio...")
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)

    log("Calculando BPM...")
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    bpm = round(float(tempo.item() if hasattr(tempo, "item") else float(tempo)), 1)

    log("Extrayendo chroma features...")
    hop_length = 4096
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)

    log("Detectando tonalidad...")
    key = _detect_key(chroma.mean(axis=1))

    log("Detectando acordes...")
    chords = _detect_chords(chroma, hop_length, sr)

    log("Detectando secciones...")
    sections = _detect_sections(chroma, hop_length, sr)

    return {"key": key, "bpm": bpm, "chords": chords, "sections": sections}
