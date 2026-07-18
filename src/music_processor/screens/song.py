import webbrowser

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static


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
        min-width: 28;
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

    BINDINGS = [Binding("escape", "back", "Volver")]

    def __init__(self, meta: dict) -> None:
        super().__init__()
        self._meta = meta
        self._active_version_idx = 0

    def compose(self) -> ComposeResult:
        meta = self._meta
        title = meta.get("title", "")
        artist = meta.get("artist", "")
        versions: list[dict] = meta.get("versions", [])
        youtube_url = meta.get("youtube_url")

        yield Header()
        yield Footer()
        yield Static(f"  {title}  —  {artist}", id="song-header")

        # Single row: version buttons | spacer | action buttons
        with Horizontal(id="controls"):
            if versions:
                yield Label("Versión:", id="version-label")
            for i, v in enumerate(versions):
                label = f"{i + 1}  {v['type']}" + ("  ✓" if i == 0 else "")
                yield Button(label, id=f"version-{i}", variant="primary" if i == 0 else "default", classes="version-btn")
            yield Static("", id="action-sep")  # pushes action buttons right
            if youtube_url:
                yield Button("▶  Ver en YouTube", id="btn-youtube")
                yield Button("⬇  Descargar + Separar", id="btn-download")

        if len(versions) > 1:
            yield Label(f"Teclas 1–{len(versions)} para cambiar versión", id="key-hint")

        with ScrollableContainer(id="content-area"):
            yield Static("Cargando...", id="chord-content", markup=False)

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("version-"):
            self._switch_version(int(btn_id.split("-", 1)[1]))
        elif btn_id == "btn-youtube":
            self._open_youtube()
        elif btn_id == "btn-download":
            self._trigger_download()

    def _switch_version(self, idx: int) -> None:
        versions = self._meta.get("versions", [])
        if idx >= len(versions):
            return
        for i, v in enumerate(versions):
            try:
                btn = self.query_one(f"#version-{i}", Button)
                active = i == idx
                btn.variant = "primary" if active else "default"
                btn.label = f"{i + 1}  {v['type']}" + ("  ✓" if active else "")
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
            content = f"Error al cargar el contenido: {exc}"
        self.app.call_from_thread(self._update_content, content)

    def _update_content(self, content: str) -> None:
        self.query_one("#chord-content", Static).update(content)

    def _open_youtube(self) -> None:
        from ..library.index import embed_to_watch_url
        url = embed_to_watch_url(self._meta.get("youtube_url") or "")
        if url:
            webbrowser.open(url)
        else:
            self.notify("URL de YouTube no disponible", severity="warning")

    def _trigger_download(self) -> None:
        from ..library.index import embed_to_watch_url
        from .home import HomeScreen
        url = embed_to_watch_url(self._meta.get("youtube_url") or "")
        if not url:
            self.notify("No se pudo obtener la URL de YouTube", severity="error")
            return
        self.app.push_screen(HomeScreen(initial_url=url))
