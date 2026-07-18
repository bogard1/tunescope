_lang: str = "en"

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # App
        "app.quit": "Quit",
        # Menu
        "menu.btn_audio": "🎵  Process Audio  (a)",
        "menu.btn_audio_desc": "Download audio and analyze chords, BPM and key",
        "menu.btn_library": "📖  Chord Library  (b)",
        "menu.btn_library_desc": "Browse and search 145,000+ songs with chords",
        # Home
        "home.label": "Enter an audio file or YouTube URL:",
        "home.placeholder": "~/music/song.mp3  or  https://youtube.com/watch?v=...",
        "home.btn_process": "Process  (Enter)",
        "home.notify_empty": "Enter a file or URL",
        "home.log_downloading": "[bold cyan]Downloading audio from YouTube...[/]",
        "home.log_downloaded": "[green]✓ Downloaded:[/] {name}",
        "home.log_file": "[green]✓ File:[/] {name}",
        "home.log_separating": "[bold cyan]Separating instruments with Demucs...[/]",
        "home.log_model": "[dim]First run downloads the model (~80 MB). May take a few minutes.[/]",
        "home.log_stems": "[green]✓ Stems:[/] {stems}",
        "home.log_analyzing": "[bold cyan]Analyzing key and chords...[/]",
        "home.log_key_bpm": "[green]✓ Key:[/] {key}  [green]BPM:[/] {bpm}",
        "home.log_saved": "[green]✓ Saved:[/] {path}",
        "home.err_not_found": "File not found: {path}",
        # Results
        "results.summary": "  {name}  |  Key: {key}  |  BPM: {bpm}",
        "results.stems_label": "Generated stems",
        "results.no_stems": "No stems available",
        "results.chords_label": "Detected chords",
        "results.col_time": "Time",
        "results.col_chord": "Chord",
        "results.col_duration": "Duration",
        "results.btn_back": "← New song  (Esc)",
        "results.notify_no_player": "Install mpv to play audio",
        # Song
        "song.version_label": "Version:",
        "song.version_hint": "Keys 1–{n} to switch version",
        "song.loading": "Loading...",
        "song.btn_youtube": "▶  Watch on YouTube  (y)",
        "song.btn_download": "⬇  Download + Separate  (d)",
        "song.btn_pdf": "⬡  Export PDF  (p)",
        "song.notify_pdf_saved": "PDF saved: {path}",
        "song.notify_pdf_error": "Error generating PDF: {error}",
        "song.notify_no_url": "YouTube URL not available",
        "song.notify_no_url_dl": "Could not get YouTube URL",
        "song.err_content": "Error loading content: {error}",
        # Library
        "library.search_artists": "Search artist...",
        "library.search_songs": "Search in {artist}...",
        "library.breadcrumb": "Artists  ›  {artist}   (ESC to go back)",
        "library.label_artists": "Artists",
        "library.label_songs": "Songs",
        "library.status_loading": "Loading...",
        "library.status_loading_songs": "Loading songs for {artist}...",
        "library.status_artists_hint": "{n} artists — search to filter",
        "library.status_songs_hint": "{n} songs — search to filter",
        "library.label_artists_max": "Artists  (showing {max})",
        "library.label_artists_count": "Artists ({n})",
        "library.label_no_results": "No results",
        "library.label_songs_count": "{artist}  ({n})",
        "library.search_result_artists": '"{q}" → {n} artists',
        "library.search_result_songs": '"{q}" → {n} songs',
    },
    "es": {
        # App
        "app.quit": "Salir",
        # Menu
        "menu.btn_audio": "🎵  Procesar Audio  (a)",
        "menu.btn_audio_desc": "Descarga audio y analiza acordes, BPM y tonalidad",
        "menu.btn_library": "📖  Biblioteca de Acordes  (b)",
        "menu.btn_library_desc": "Busca y explora 145,000+ canciones con acordes",
        # Home
        "home.label": "Ingresa un archivo de audio o URL de YouTube:",
        "home.placeholder": "~/musica/cancion.mp3  o  https://youtube.com/watch?v=...",
        "home.btn_process": "Procesar  (Enter)",
        "home.notify_empty": "Ingresa un archivo o URL",
        "home.log_downloading": "[bold cyan]Descargando audio de YouTube...[/]",
        "home.log_downloaded": "[green]✓ Descargado:[/] {name}",
        "home.log_file": "[green]✓ Archivo:[/] {name}",
        "home.log_separating": "[bold cyan]Separando instrumentos con Demucs...[/]",
        "home.log_model": "[dim]La primera vez descarga el modelo (~80 MB). Puede tardar unos minutos.[/]",
        "home.log_stems": "[green]✓ Stems:[/] {stems}",
        "home.log_analyzing": "[bold cyan]Analizando tonalidad y acordes...[/]",
        "home.log_key_bpm": "[green]✓ Tonalidad:[/] {key}  [green]BPM:[/] {bpm}",
        "home.log_saved": "[green]✓ Guardado:[/] {path}",
        "home.err_not_found": "Archivo no encontrado: {path}",
        # Results
        "results.summary": "  {name}  |  Tonalidad: {key}  |  BPM: {bpm}",
        "results.stems_label": "Stems generados",
        "results.no_stems": "Sin stems disponibles",
        "results.chords_label": "Acordes detectados",
        "results.col_time": "Tiempo",
        "results.col_chord": "Acorde",
        "results.col_duration": "Duración",
        "results.btn_back": "← Nueva canción  (Esc)",
        "results.notify_no_player": "Instala mpv para reproducir audio",
        # Song
        "song.version_label": "Versión:",
        "song.version_hint": "Teclas 1–{n} para cambiar versión",
        "song.loading": "Cargando...",
        "song.btn_youtube": "▶  Ver en YouTube  (y)",
        "song.btn_download": "⬇  Descargar + Separar  (d)",
        "song.btn_pdf": "⬡  Exportar PDF  (p)",
        "song.notify_pdf_saved": "PDF guardado: {path}",
        "song.notify_pdf_error": "Error al generar PDF: {error}",
        "song.notify_no_url": "URL de YouTube no disponible",
        "song.notify_no_url_dl": "No se pudo obtener la URL de YouTube",
        "song.err_content": "Error al cargar el contenido: {error}",
        # Library
        "library.search_artists": "Buscar artista...",
        "library.search_songs": "Buscar en {artist}...",
        "library.breadcrumb": "Artistas  ›  {artist}   (ESC para volver)",
        "library.label_artists": "Artistas",
        "library.label_songs": "Canciones",
        "library.status_loading": "Cargando...",
        "library.status_loading_songs": "Cargando canciones de {artist}...",
        "library.status_artists_hint": "{n} artistas — busca para filtrar",
        "library.status_songs_hint": "{n} canciones — busca para filtrar",
        "library.label_artists_max": "Artistas  (mostrando {max})",
        "library.label_artists_count": "Artistas ({n})",
        "library.label_no_results": "Sin resultados",
        "library.label_songs_count": "{artist}  ({n})",
        "library.search_result_artists": '"{q}" → {n} artistas',
        "library.search_result_songs": '"{q}" → {n} canciones',
    },
}


def get_lang() -> str:
    return _lang


def set_lang(lang: str) -> None:
    global _lang
    if lang in _TRANSLATIONS:
        _lang = lang


def t(key: str, **kwargs: object) -> str:
    strings = _TRANSLATIONS.get(_lang, _TRANSLATIONS["en"])
    text = strings.get(key) or _TRANSLATIONS["en"].get(key) or key
    return text.format(**kwargs) if kwargs else text
