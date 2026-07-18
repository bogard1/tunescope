from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, ProgressBar, RichLog


class HomeScreen(Screen):
    DEFAULT_CSS = """
    HomeScreen {
        align: center middle;
    }

    #card {
        width: 72;
        height: auto;
        padding: 2 4;
        border: solid $accent;
        background: $surface;
    }

    #card Label {
        color: $text-muted;
        margin-bottom: 1;
    }

    #source-input {
        margin-bottom: 1;
    }

    #process-btn {
        width: 100%;
        margin-bottom: 1;
    }

    #log {
        height: 12;
        border: solid $panel;
        margin-top: 1;
        display: none;
    }

    #log.visible {
        display: block;
    }

    #progress {
        margin-top: 1;
        display: none;
    }

    #progress.visible {
        display: block;
    }
    """

    BINDINGS = [("escape", "back", "Volver")]

    def __init__(self, initial_url: str | None = None) -> None:
        super().__init__()
        self._initial_url = initial_url

    def on_mount(self) -> None:
        if self._initial_url:
            self.query_one("#source-input", Input).value = self._initial_url
            self._start(self._initial_url)

    def action_back(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Center():
            with Vertical(id="card"):
                yield Label("Ingresá un archivo de audio o URL de YouTube:")
                yield Input(
                    placeholder="~/musica/cancion.mp3  o  https://youtube.com/watch?v=...",
                    id="source-input",
                )
                yield Button("Procesar", variant="primary", id="process-btn")
                yield RichLog(id="log", highlight=True, markup=True)
                yield ProgressBar(id="progress", total=100, show_eta=False)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        source = event.value.strip()
        if source:
            self._start(source)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "process-btn":
            source = self.query_one("#source-input", Input).value.strip()
            if not source:
                self.notify("Ingresá un archivo o URL", severity="warning")
                return
            self._start(source)

    def _start(self, source: str) -> None:
        self.query_one("#process-btn", Button).disabled = True
        log = self.query_one("#log", RichLog)
        progress = self.query_one("#progress", ProgressBar)
        log.add_class("visible")
        progress.add_class("visible")
        log.clear()
        self._run_pipeline(source)

    # --- helpers called on the main thread via call_from_thread ---

    def _log(self, msg: str) -> None:
        self.query_one("#log", RichLog).write(msg)

    def _advance(self, amount: int) -> None:
        self.query_one("#progress", ProgressBar).advance(amount)

    def _on_error(self, error: str) -> None:
        self._log(f"[bold red]Error:[/] {error}")
        self.notify(error, severity="error", timeout=12)
        self.query_one("#process-btn", Button).disabled = False

    def _on_complete(self, result: dict) -> None:
        from .results import ResultsScreen
        self.app.push_screen(ResultsScreen(result))

    # --- background worker ---

    @work(thread=True)
    def _run_pipeline(self, source: str) -> None:
        from ..pipeline.analyzer import analyze
        from ..pipeline.downloader import download_audio, is_youtube_url
        from ..pipeline.separator import separate_stems

        def log(msg: str) -> None:
            self.app.call_from_thread(self._log, msg)

        def advance(amount: int = 10) -> None:
            self.app.call_from_thread(self._advance, amount)

        try:
            base_dir = Path.home() / ".music-processor"

            # Step 1: obtain audio file
            if is_youtube_url(source):
                log("[bold cyan]Descargando audio de YouTube...[/]")
                audio_path = download_audio(
                    source,
                    base_dir / "downloads",
                    progress_callback=log,
                )
                log(f"[green]✓ Descargado:[/] {audio_path.name}")
            else:
                audio_path = Path(source).expanduser().resolve()
                if not audio_path.exists():
                    raise FileNotFoundError(f"Archivo no encontrado: {audio_path}")
                log(f"[green]✓ Archivo:[/] {audio_path.name}")

            advance(20)

            # Step 2: source separation
            stems_dir = base_dir / "stems" / audio_path.stem
            log("[bold cyan]Separando instrumentos con Demucs...[/]")
            log("[dim]La primera vez descarga el modelo (~80 MB). Puede tardar unos minutos.[/]")
            stems = separate_stems(audio_path, stems_dir, progress_callback=log)
            log(f"[green]✓ Stems:[/] {', '.join(stems.keys())}")
            advance(40)

            # Step 3: analysis (prefer "other" stem — harmonics without drums/bass/voice)
            analysis_source = stems.get("other", audio_path)
            log("[bold cyan]Analizando tonalidad y acordes...[/]")
            analysis = analyze(analysis_source, progress_callback=log)
            log(f"[green]✓ Tonalidad:[/] {analysis['key']}  [green]BPM:[/] {analysis['bpm']}")
            advance(40)

            # Save results alongside the audio stems
            output_dir = list(stems.values())[0].parent
            import json
            results_file = output_dir / "results.json"
            results_file.write_text(
                json.dumps(
                    {"key": analysis["key"], "bpm": analysis["bpm"], "chords": analysis["chords"]},
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            log(f"[green]✓ Guardado:[/] {results_file}")

            result = {**analysis, "stems": stems, "audio_name": audio_path.stem, "output_dir": output_dir}
            self.app.call_from_thread(self._on_complete, result)

        except Exception as exc:
            self.app.call_from_thread(self._on_error, str(exc))
