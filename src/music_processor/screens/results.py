import shutil
import subprocess
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, Static

from ..i18n import t


class ResultsScreen(Screen):
    DEFAULT_CSS = """
    ResultsScreen {
        padding: 1 2;
    }

    #summary {
        height: 3;
        border: solid $accent;
        padding: 0 2;
        margin-bottom: 1;
        content-align: left middle;
    }

    #columns {
        height: 1fr;
        margin-bottom: 1;
    }

    #stems-panel {
        width: 34;
        border: solid $panel;
        padding: 1 2;
        margin-right: 1;
    }

    #stems-panel > Label {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .stem-row {
        height: 3;
        align: left middle;
        margin-bottom: 0;
    }

    .play-btn {
        min-width: 16;
        margin-right: 1;
    }

    .stem-label {
        color: $text-muted;
        content-align: left middle;
        height: 3;
    }

    #chords-panel {
        width: 1fr;
        border: solid $panel;
        padding: 1 2;
    }

    #chords-panel > Label {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #chords-table {
        height: 1fr;
    }

    #output-path {
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
        height: 1;
    }

    #sections-panel {
        height: 9;
        border: solid $panel;
        padding: 1 2;
        margin-bottom: 1;
    }

    #sections-panel.hidden {
        display: none;
    }

    #sections-panel > Label {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #sections-table {
        height: 1fr;
    }

    #back-area {
        height: 5;
        align: center middle;
    }

    #btn-back {
        min-width: 28;
    }
    """

    BINDINGS = [Binding("escape", "back", "Back")]

    def __init__(self, result: dict) -> None:
        super().__init__()
        self._result = result
        self._player: subprocess.Popen | None = None
        self._playing_stem: str | None = None

    def compose(self) -> ComposeResult:
        result = self._result
        key = result.get("key", "—")
        bpm = result.get("bpm", "—")
        name = result.get("audio_name", "")
        stems: dict[str, Path] = result.get("stems", {})
        chords: list[dict] = result.get("chords", [])
        output_dir: Path | None = result.get("output_dir")

        yield Header()
        yield Footer()
        yield Static(t("results.summary", name=name, key=key, bpm=bpm), id="summary")

        with Horizontal(id="columns"):
            with Vertical(id="stems-panel"):
                yield Label(t("results.stems_label"))
                for i, (stem_name, stem_path) in enumerate(stems.items()):
                    size_mb = stem_path.stat().st_size / (1024 * 1024)
                    with Horizontal(classes="stem-row"):
                        yield Button(f"▶ Play  ({i + 1})", id=f"play-{stem_name}", classes="play-btn")
                        yield Static(f"{stem_name}  ({size_mb:.1f} MB)", classes="stem-label")
                if not stems:
                    yield Static(t("results.no_stems"))
                if output_dir:
                    yield Static(f"📁 {output_dir}", id="output-path")

            with Vertical(id="chords-panel"):
                yield Label(t("results.chords_label"))
                yield DataTable(id="chords-table", zebra_stripes=True)

        with Vertical(id="sections-panel"):
            yield Label(t("results.sections_label"))
            yield DataTable(id="sections-table", zebra_stripes=True)

        with Center(id="back-area"):
            yield Button(t("results.btn_back"), id="btn-back", variant="primary")

    def on_mount(self) -> None:
        chords: list[dict] = self._result.get("chords", [])
        table = self.query_one("#chords-table", DataTable)
        table.add_columns(t("results.col_time"), t("results.col_chord"), t("results.col_duration"))
        for c in chords:
            table.add_row(f"{c['time']:.1f}s", c["chord"], f"{c['duration']:.1f}s")

        sections: list[dict] = self._result.get("sections", [])
        if sections:
            stable = self.query_one("#sections-table", DataTable)
            stable.add_columns(
                t("results.col_section"),
                t("results.col_start"),
                t("results.col_end"),
                t("results.col_duration"),
            )
            for s in sections:
                stable.add_row(
                    s["label"],
                    f"{s['time']:.1f}s",
                    f"{s['end']:.1f}s",
                    f"{s['duration']:.1f}s",
                )
        else:
            self.query_one("#sections-panel").add_class("hidden")

        if not shutil.which("mpv") and not shutil.which("ffplay"):
            for btn in self.query(".play-btn").results(Button):
                btn.disabled = True
            self.notify(t("results.notify_no_player"), severity="warning")

    def on_key(self, event: Key) -> None:
        if event.character and event.character.isdigit():
            idx = int(event.character) - 1
            stems = list(self._result.get("stems", {}).keys())
            if 0 <= idx < len(stems):
                self._toggle_play(stems[idx])
                event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self._stop_playback()
            self.action_back()
        elif event.button.id and event.button.id.startswith("play-"):
            stem_name = event.button.id[len("play-"):]
            self._toggle_play(stem_name)

    def _toggle_play(self, stem_name: str) -> None:
        if self._playing_stem == stem_name:
            self._stop_playback()
            return
        self._stop_playback()
        path = self._result.get("stems", {}).get(stem_name)
        if path:
            self._start_playback(stem_name, path)

    def _start_playback(self, stem_name: str, path: Path) -> None:
        player_bin = shutil.which("mpv") or shutil.which("ffplay")
        if not player_bin:
            return

        cmd = (
            ["mpv", "--no-video", str(path)]
            if "mpv" in player_bin
            else ["ffplay", "-nodisp", "-autoexit", str(path)]
        )
        self._player = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._playing_stem = stem_name
        self._update_play_buttons(stem_name)
        self._watch_playback(stem_name)

    def _stop_playback(self) -> None:
        if self._player and self._player.poll() is None:
            self._player.terminate()
        self._player = None
        self._playing_stem = None
        self._update_play_buttons(None)

    def _update_play_buttons(self, active: str | None) -> None:
        for i, stem_name in enumerate(self._result.get("stems", {})):
            try:
                btn = self.query_one(f"#play-{stem_name}", Button)
                if stem_name == active:
                    btn.label = f"■ Stop  ({i + 1})"
                    btn.variant = "error"
                else:
                    btn.label = f"▶ Play  ({i + 1})"
                    btn.variant = "default"
            except Exception:
                pass

    @work(thread=True)
    def _watch_playback(self, stem_name: str) -> None:
        if self._player:
            self._player.wait()
        if self._playing_stem == stem_name:
            self.app.call_from_thread(self._stop_playback)

    def action_back(self) -> None:
        self.app.pop_screen()
