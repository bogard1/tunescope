from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import DataTable, Footer, Header, Input, Label

from ..i18n import t

MAX_ARTISTS = 200


class LibraryScreen(Screen):
    DEFAULT_CSS = """
    LibraryScreen {
        padding: 1 2;
    }

    #search {
        margin-bottom: 0;
    }

    #breadcrumb {
        height: 1;
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
        padding: 0 1;
    }

    #panels {
        height: 1fr;
    }

    #artist-panel {
        width: 35;
        border: solid $panel;
        padding: 0 1;
        margin-right: 1;
    }

    #artist-panel > Label {
        text-style: bold;
        color: $accent;
        height: 2;
        content-align: left middle;
    }

    #artist-table {
        height: 1fr;
    }

    #song-panel {
        width: 1fr;
        border: solid $panel;
        padding: 0 1;
    }

    #song-panel > Label {
        text-style: bold;
        color: $accent;
        height: 2;
        content-align: left middle;
    }

    #song-table {
        height: 1fr;
    }

    #status {
        height: 1;
        color: $text-muted;
        text-style: italic;
        dock: bottom;
    }
    """

    BINDINGS = [Binding("escape", "back", "Back")]

    def __init__(self) -> None:
        super().__init__()
        self._all_artists: list[dict] = []
        self._shown_artists: list[dict] = []
        self._all_songs: list[dict] = []
        self._shown_songs: list[dict] = []
        self._selected_artist: dict | None = None
        self._phase: str = "artists"
        self._search_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Input(placeholder=t("library.search_artists"), id="search")
        yield Label("", id="breadcrumb")
        with Horizontal(id="panels"):
            with Vertical(id="artist-panel"):
                yield Label(t("library.label_artists"), id="artist-label")
                yield DataTable(id="artist-table", cursor_type="row", show_header=False)
            with Vertical(id="song-panel"):
                yield Label(t("library.label_songs"), id="song-label")
                yield DataTable(id="song-table", cursor_type="row", show_header=False)
        yield Label(t("library.status_loading"), id="status")

    def on_mount(self) -> None:
        self.query_one("#artist-table", DataTable).add_column("name", key="name")
        self.query_one("#song-table", DataTable).add_column("title", key="title")
        self._load_artists()

    def action_back(self) -> None:
        if self._phase == "songs":
            self._exit_song_phase()
        else:
            self.app.pop_screen()

    # ── phase transitions ─────────────────────────────────────────────────────

    def _enter_song_phase(self, artist: dict) -> None:
        self._phase = "songs"
        self._selected_artist = artist
        search = self.query_one("#search", Input)
        search.value = ""
        search.placeholder = t("library.search_songs", artist=artist["name"])
        self.query_one("#breadcrumb", Label).update(
            t("library.breadcrumb", artist=artist["name"])
        )
        self._set_status(t("library.status_loading_songs", artist=artist["name"]))
        self._load_songs(artist)
        search.focus()

    def _exit_song_phase(self) -> None:
        self._phase = "artists"
        self._selected_artist = None
        self._all_songs = []
        self._shown_songs = []
        search = self.query_one("#search", Input)
        search.value = ""
        search.placeholder = t("library.search_artists")
        self.query_one("#breadcrumb", Label).update("")
        self.query_one("#song-label", Label).update(t("library.label_songs"))
        self.query_one("#song-table", DataTable).clear()
        suffix = f"  (mostrando {MAX_ARTISTS})" if len(self._all_artists) > MAX_ARTISTS else ""
        self.query_one("#artist-label", Label).update(
            t("library.label_artists") + suffix if not suffix
            else t("library.label_artists_max", max=MAX_ARTISTS)
        )
        self._set_status(t("library.status_artists", n=len(self._all_artists)))
        search.focus()

    # ── data loading (background threads) ────────────────────────────────────

    @work(thread=True)
    def _load_artists(self) -> None:
        from ..library.index import get_artists
        artists = get_artists()
        self.app.call_from_thread(self._set_artists, artists)

    @work(thread=True)
    def _load_songs(self, artist: dict) -> None:
        from ..library.index import get_songs
        songs = get_songs(artist["slug"])
        self.app.call_from_thread(self._set_songs, artist, songs)

    @work(thread=True)
    def _search_artists(self, query: str) -> None:
        from ..library.index import fuzzy_search_artists
        results = fuzzy_search_artists(query, self._all_artists)
        self.app.call_from_thread(self._apply_artist_search, results, query)

    @work(thread=True)
    def _search_songs(self, query: str) -> None:
        from ..library.index import fuzzy_search_songs
        results = fuzzy_search_songs(query, self._all_songs)
        self.app.call_from_thread(self._apply_song_search, results, query)

    # ── UI updates (main thread) ──────────────────────────────────────────────

    def _set_artists(self, artists: list[dict]) -> None:
        self._all_artists = artists
        self._fill_artist_table(artists[:MAX_ARTISTS])
        label = (
            t("library.label_artists_max", max=MAX_ARTISTS)
            if len(artists) > MAX_ARTISTS
            else t("library.label_artists")
        )
        self.query_one("#artist-label", Label).update(label)
        self._set_status(t("library.status_artists_hint", n=len(artists)))

    def _set_songs(self, artist: dict, songs: list[dict]) -> None:
        self._all_songs = songs
        self._shown_songs = songs
        self._fill_song_table(songs)
        self.query_one("#song-label", Label).update(
            t("library.label_songs_count", artist=artist["name"], n=len(songs))
        )
        self._set_status(t("library.status_songs_hint", n=len(songs)))

    def _apply_artist_search(self, results: list[dict], query: str) -> None:
        self._fill_artist_table(results)
        self.query_one("#artist-label", Label).update(
            t("library.label_artists_count", n=len(results)) if results
            else t("library.label_no_results")
        )
        self._set_status(t("library.search_result_artists", q=query, n=len(results)))

    def _apply_song_search(self, results: list[dict], query: str) -> None:
        self._fill_song_table(results)
        name = self._selected_artist["name"] if self._selected_artist else ""
        self.query_one("#song-label", Label).update(
            t("library.label_songs_count", artist=name, n=len(results)) if results
            else t("library.label_no_results")
        )
        self._set_status(t("library.search_result_songs", q=query, n=len(results)))

    def _fill_artist_table(self, artists: list[dict]) -> None:
        self._shown_artists = artists
        table = self.query_one("#artist-table", DataTable)
        table.clear()
        table.add_rows([[a["name"]] for a in artists])

    def _fill_song_table(self, songs: list[dict]) -> None:
        self._shown_songs = songs
        table = self.query_one("#song-table", DataTable)
        table.clear()
        table.add_rows([[s.get("title", s.get("song_slug", ""))] for s in songs])

    def _set_status(self, msg: str) -> None:
        self.query_one("#status", Label).update(msg)

    # ── events ────────────────────────────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        if self._search_timer is not None:
            self._search_timer.stop()
        query = event.value.strip()

        if self._phase == "artists":
            if not query:
                self._fill_artist_table(self._all_artists[:MAX_ARTISTS])
                label = (
                    t("library.label_artists_max", max=MAX_ARTISTS)
                    if len(self._all_artists) > MAX_ARTISTS
                    else t("library.label_artists")
                )
                self.query_one("#artist-label", Label).update(label)
                self._set_status(t("library.status_artists_hint", n=len(self._all_artists)))
            else:
                self._search_timer = self.set_timer(0.35, lambda: self._search_artists(query))

        else:
            if not query:
                self._fill_song_table(self._all_songs)
                name = self._selected_artist["name"] if self._selected_artist else ""
                self.query_one("#song-label", Label).update(
                    t("library.label_songs_count", artist=name, n=len(self._all_songs))
                )
                self._set_status(t("library.status_songs_hint", n=len(self._all_songs)))
            else:
                self._search_timer = self.set_timer(0.35, lambda: self._search_songs(query))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_idx = event.cursor_row
        if event.data_table.id == "artist-table":
            if row_idx < len(self._shown_artists):
                self._enter_song_phase(self._shown_artists[row_idx])
        elif event.data_table.id == "song-table":
            if row_idx < len(self._shown_songs):
                from .song import SongScreen
                self.app.push_screen(SongScreen(self._shown_songs[row_idx]))
