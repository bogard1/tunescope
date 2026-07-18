import webbrowser

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static

from ..i18n import t


class SongScreen(Screen):
    DEFAULT_CSS = """
    SongScreen {
        padding: 1 2;
    }

    #song-header {
        height: 3;
        border: solid $accent;
        padding: 0 2;
        margin-bottom: 1;
        content-align: left middle;
    }

    #controls {
        height: 3;
        align: left middle;
        margin-bottom: 1;
    }

    #version-label {
        color: $text-muted;
        content-align: left middle;
        height: 3;
        width: auto;
        margin-right: 1;
    }

    .version-btn {
        margin-right: 1;
        min-width: 14;
        height: 3;
    }

    #action-sep {
        width: 1fr;
    }

    #btn-youtube {
        height: 3;
        margin-right: 1;
        min-width: 20;
    }

    #btn-download {
        height: 3;
        margin-right: 1;
        min-width: 28;
    }

    #btn-pdf {
        height: 3;
        min-width: 18;
    }

    #key-hint {
        height: 1;
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
    }

    #content-area {
        height: 1fr;
        border: solid $panel;
        padding: 1 2;
    }

    #chord-content {
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("y", "youtube", show=False),
        Binding("d", "download", show=False),
        Binding("p", "pdf", show=False),
    ]

    def __init__(self, meta: dict) -> None:
        super().__init__()
        self._meta = meta
        self._active_version_idx = 0
        self._current_content: str = ""

    def compose(self) -> ComposeResult:
        meta = self._meta
        title = meta.get("title", "")
        artist = meta.get("artist", "")
        versions: list[dict] = meta.get("versions", [])
        youtube_url = meta.get("youtube_url")

        yield Header()
        yield Footer()
        yield Static(f"  {title}  —  {artist}", id="song-header")

        with Horizontal(id="controls"):
            if versions:
                yield Label(t("song.version_label"), id="version-label")
            for i, v in enumerate(versions):
                label = f"{v['type']}  ({i + 1})" + ("  ✓" if i == 0 else "")
                yield Button(label, id=f"version-{i}", variant="primary" if i == 0 else "default", classes="version-btn")
            yield Static("", id="action-sep")
            if youtube_url:
                yield Button(t("song.btn_youtube"), id="btn-youtube")
                yield Button(t("song.btn_download"), id="btn-download")
            yield Button(t("song.btn_pdf"), id="btn-pdf")

        if len(versions) > 1:
            yield Label(t("song.version_hint", n=len(versions)), id="key-hint")

        with ScrollableContainer(id="content-area"):
            yield Static(t("song.loading"), id="chord-content", markup=False)

    def on_mount(self) -> None:
        if self._meta.get("versions"):
            self._load_content(0)

    def action_back(self) -> None:
        self.app.pop_screen()

    def on_key(self, event: Key) -> None:
        versions = self._meta.get("versions", [])
        if event.character and event.character.isdigit():
            idx = int(event.character) - 1
            if 0 <= idx < len(versions):
                self._switch_version(idx)
                event.stop()
        elif event.key == "right":
            self._focus_control_button(1)
            event.stop()
        elif event.key == "left":
            self._focus_control_button(-1)
            event.stop()
        elif event.key == "up":
            self.query_one("#content-area", ScrollableContainer).scroll_relative(y=-3)
            event.stop()
        elif event.key == "down":
            self.query_one("#content-area", ScrollableContainer).scroll_relative(y=3)
            event.stop()

    def _focus_control_button(self, direction: int) -> None:
        buttons: list[Button] = []
        versions = self._meta.get("versions", [])
        for i in range(len(versions)):
            try:
                buttons.append(self.query_one(f"#version-{i}", Button))
            except Exception:
                pass
        for btn_id in ("btn-youtube", "btn-download", "btn-pdf"):
            try:
                buttons.append(self.query_one(f"#{btn_id}", Button))
            except Exception:
                pass
        if not buttons:
            return
        focused = self.focused
        if focused in buttons:
            idx = (buttons.index(focused) + direction) % len(buttons)
        else:
            idx = 0 if direction > 0 else len(buttons) - 1
        buttons[idx].focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("version-"):
            self._switch_version(int(btn_id.split("-", 1)[1]))
        elif btn_id == "btn-youtube":
            self._open_youtube()
        elif btn_id == "btn-download":
            self._trigger_download()
        elif btn_id == "btn-pdf":
            self._export_pdf()

    def _switch_version(self, idx: int) -> None:
        versions = self._meta.get("versions", [])
        if idx >= len(versions):
            return
        for i, v in enumerate(versions):
            try:
                btn = self.query_one(f"#version-{i}", Button)
                active = i == idx
                btn.variant = "primary" if active else "default"
                btn.label = f"{v['type']}  ({i + 1})" + ("  ✓" if active else "")
            except Exception:
                pass
        self._active_version_idx = idx
        self._load_content(idx)

    @work(thread=True)
    def _load_content(self, version_idx: int) -> None:
        from ..library.index import get_song_content

        versions = self._meta.get("versions", [])
        if version_idx >= len(versions):
            return
        try:
            content = get_song_content(
                self._meta["artist_slug"],
                self._meta["song_slug"],
                versions[version_idx]["file"],
            )
        except Exception as exc:
            content = t("song.err_content", error=exc)
        self.app.call_from_thread(self._update_content, content)

    def _update_content(self, content: str) -> None:
        self._current_content = content
        self.query_one("#chord-content", Static).update(content)

    def action_youtube(self) -> None:
        self._open_youtube()

    def action_download(self) -> None:
        self._trigger_download()

    def action_pdf(self) -> None:
        self._export_pdf()

    def _open_youtube(self) -> None:
        from ..library.index import embed_to_watch_url
        url = embed_to_watch_url(self._meta.get("youtube_url") or "")
        if url:
            webbrowser.open(url)
        else:
            self.notify(t("song.notify_no_url"), severity="warning")

    def _trigger_download(self) -> None:
        from ..library.index import embed_to_watch_url
        from .home import HomeScreen
        url = embed_to_watch_url(self._meta.get("youtube_url") or "")
        if not url:
            self.notify(t("song.notify_no_url_dl"), severity="error")
            return
        self.app.push_screen(HomeScreen(initial_url=url))

    @work(thread=True)
    def _export_pdf(self) -> None:
        from ..pdf_export import generate_chord_pdf

        text = self._current_content
        title = self._meta.get("title", "cancion")
        artist = self._meta.get("artist", "artista")
        try:
            output_path = generate_chord_pdf(title, artist, text)
            self.app.call_from_thread(
                self.notify, t("song.notify_pdf_saved", path=output_path), timeout=8
            )
        except Exception as exc:
            self.app.call_from_thread(
                self.notify, t("song.notify_pdf_error", error=exc), severity="error"
            )
