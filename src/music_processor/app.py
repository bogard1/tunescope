from textual.app import App
from textual.binding import Binding

from .screens.menu import MenuScreen


class MusicProcessorApp(App):
    TITLE = "Music Processor"
    BINDINGS = [Binding("q", "quit", "Salir")]

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())
