import json
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label, Static

from ..history import delete_entry, load_history
from ..i18n import t


class HistoryScreen(Screen):
    DEFAULT_CSS = """
    HistoryScreen {
        padding: 1 2;
    }

    #history-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        height: 1;
    }

    #history-table {
        height: 1fr;
    }

    #history-empty {
        display: none;
        color: $text-muted;
        content-align: center middle;
        height: 1fr;
    }

    #history-empty.visible {
        display: block;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("d", "delete_entry", "Delete"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._entries: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Label(t("history.title"), id="history-title")
        yield Static(t("history.empty"), id="history-empty")
        yield DataTable(id="history-table", cursor_type="row", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one("#history-table", DataTable)
        table.add_columns(
            t("history.col_name"),
            t("history.col_key"),
            t("history.col_bpm"),
            t("history.col_date"),
        )
        self._load()

    @work(thread=True)
    def _load(self) -> None:
        entries = load_history()
        self.app.call_from_thread(self._populate, entries)

    def _populate(self, entries: list[dict]) -> None:
        self._entries = entries
        table = self.query_one("#history-table", DataTable)
        table.clear()

        if not entries:
            self.query_one("#history-empty").add_class("visible")
            return

        self.query_one("#history-empty").remove_class("visible")
        for e in entries:
            date_str = e.get("analyzed_at", "")[:10]
            table.add_row(
                e.get("name", ""),
                e.get("key", "—"),
                str(e.get("bpm", "—")),
                date_str,
                key=e.get("id"),
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        entry_id = str(event.row_key.value)
        entry = next((e for e in self._entries if e.get("id") == entry_id), None)
        if entry:
            self._open_entry(entry)

    @work(thread=True)
    def _open_entry(self, entry: dict) -> None:
        output_dir = Path(entry.get("output_dir", ""))
        results_file = output_dir / "results.json"

        if not results_file.exists():
            self.app.call_from_thread(
                self.notify, t("history.err_not_found"), severity="error"
            )
            return

        try:
            data = json.loads(results_file.read_text(encoding="utf-8"))
        except Exception:
            self.app.call_from_thread(
                self.notify, t("history.err_not_found"), severity="error"
            )
            return

        stems: dict[str, Path] = {}
        for stem_name in ("vocals", "drums", "bass", "other"):
            p = output_dir / f"{stem_name}.mp3"
            if p.exists():
                stems[stem_name] = p

        result = {
            **data,
            "stems": stems,
            "audio_name": entry.get("name", ""),
            "output_dir": output_dir,
        }

        from .results import ResultsScreen
        self.app.call_from_thread(self.app.push_screen, ResultsScreen(result))

    def action_delete_entry(self) -> None:
        table = self.query_one("#history-table", DataTable)
        if not self._entries:
            return
        row_index = table.cursor_row
        if row_index < 0 or row_index >= len(self._entries):
            return
        entry = self._entries[row_index]
        delete_entry(entry.get("id", ""))
        self.notify(t("history.notify_deleted", name=entry.get("name", "")))
        self._load()

    def action_back(self) -> None:
        self.app.pop_screen()
