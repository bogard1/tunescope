from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label


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

    BINDINGS = [Binding("q", "quit", "Salir")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Center():
            with Vertical(id="menu-container"):
                yield Label("Music Processor", id="app-title")
                yield Button("🎵  Procesar Audio", id="btn-audio", variant="primary", classes="menu-btn")
                yield Label("Descargá audio y analizá acordes, BPM y tonalidad", classes="menu-btn-label")
                yield Button("📖  Biblioteca de Acordes", id="btn-library", variant="default", classes="menu-btn")
                yield Label("Buscá y explorá 145,000+ canciones con acordes", classes="menu-btn-label")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-audio":
            from .home import HomeScreen
            self.app.push_screen(HomeScreen())
        elif event.button.id == "btn-library":
            from .library import LibraryScreen
            self.app.push_screen(LibraryScreen())
