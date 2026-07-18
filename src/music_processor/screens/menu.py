from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label

from ..i18n import get_lang, set_lang, t


class MenuScreen(Screen):
    DEFAULT_CSS = """
    MenuScreen {
        align: center middle;
    }

    #menu-container {
        width: 50;
        height: auto;
        align: center middle;
    }

    #app-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 2;
        padding: 0 2;
    }

    .menu-btn {
        width: 100%;
        height: 5;
        margin-bottom: 1;
        content-align: center middle;
    }

    .menu-btn-label {
        text-align: center;
        color: $text-muted;
        width: 100%;
        margin-bottom: 2;
    }
    """

    BINDINGS = [
        Binding("a", "open_audio", show=False),
        Binding("b", "open_library", show=False),
        Binding("l", "switch_to_es", "Español"),
        Binding("l", "switch_to_en", "English"),
    ]

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        if action == "switch_to_es":
            return get_lang() == "en"
        if action == "switch_to_en":
            return get_lang() == "es"
        return True

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Center():
            with Vertical(id="menu-container"):
                yield Label("Music Processor", id="app-title")
                yield Button(t("menu.btn_audio"), id="btn-audio", variant="primary", classes="menu-btn")
                yield Label(t("menu.btn_audio_desc"), id="lbl-audio-desc", classes="menu-btn-label")
                yield Button(t("menu.btn_library"), id="btn-library", variant="default", classes="menu-btn")
                yield Label(t("menu.btn_library_desc"), id="lbl-library-desc", classes="menu-btn-label")

    def on_mount(self) -> None:
        self.query_one("#btn-audio", Button).focus()

    def on_key(self, event: Key) -> None:
        if event.key == "down":
            self.app.action_focus_next()
            event.stop()
        elif event.key == "up":
            self.app.action_focus_previous()
            event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-audio":
            self.action_open_audio()
        elif event.button.id == "btn-library":
            self.action_open_library()

    def action_open_audio(self) -> None:
        from .home import HomeScreen
        self.app.push_screen(HomeScreen())

    def action_open_library(self) -> None:
        from .library import LibraryScreen
        self.app.push_screen(LibraryScreen())

    def action_switch_to_es(self) -> None:
        set_lang("es")
        self._refresh_ui()
        self.refresh_bindings()

    def action_switch_to_en(self) -> None:
        set_lang("en")
        self._refresh_ui()
        self.refresh_bindings()

    def _refresh_ui(self) -> None:
        self.query_one("#btn-audio", Button).label = t("menu.btn_audio")
        self.query_one("#btn-library", Button).label = t("menu.btn_library")
        self.query_one("#lbl-audio-desc", Label).update(t("menu.btn_audio_desc"))
        self.query_one("#lbl-library-desc", Label).update(t("menu.btn_library_desc"))
