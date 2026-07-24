# tunescope

TUI para análisis de audio y exploración de una biblioteca de acordes, construido con [Textual](https://textual.textualize.io/).

[Read in English](README.md)

## Instalación

```bash
make install
```

Crea un virtualenv en `venv/` e instala todas las dependencias. Para separación de stems (requiere PyTorch, ~2 GB):

```bash
venv/bin/pip install demucs
```

## Uso

```bash
make run
# o directamente:
venv/bin/music-tui
```

## Funcionalidades

### Soporte de idiomas

La interfaz está disponible en **inglés** y **español**. Presioná **`l`** desde el menú principal para cambiar de idioma en cualquier momento — todos los labels, hints y notificaciones se actualizan al instante.

### Procesar Audio

Recibe un archivo de audio local o una URL de YouTube y ejecuta el pipeline completo:

1. **Descarga** el audio via `yt-dlp` (si es URL de YouTube)
2. **Separa instrumentos** con [Demucs](https://github.com/facebookresearch/demucs): drums, bass, vocals, other
3. **Analiza** el stem `other` (armónicos sin voz ni percusión):
   - Tonalidad — perfiles de Krumhansl-Kessler sobre chroma CQT
   - BPM — `librosa.beat.beat_track`
   - Acordes — template matching sobre chroma (108 templates: mayor, menor, dim, aug, sus2, sus4, 7, maj7, m7 × 12 notas)
   - Secciones — segmentación estructural con `librosa.segment.agglomerative`, etiquetadas A/B/C/D/E
4. **Guarda** `results.json` junto a los stems en `~/.music-processor/stems/<canción>/`

Desde la pantalla de resultados se puede reproducir cada stem con `mpv` o `ffplay`.

### Historial

Cada canción analizada se guarda en `~/.music-processor/history.json`. Presioná **h** desde el menú principal (o usá el botón Historial) para navegar análisis anteriores y reabrir cualquier resultado sin volver a correr el pipeline. Presioná **d** sobre una entrada para eliminarla.

### Biblioteca de Acordes

Navega y busca en una biblioteca local de acordes. La búsqueda soporta:

- Texto parcial: `soda` → Soda Stereo
- Sin acentos: `beatles` → The Beatles
- Iniciales: `gc` → Gustavo Cerati, `vp` → Violeta Parra
- Iniciales + continuación: `vparra` → Violeta Parra

**Flujo de búsqueda en dos pasos:**

1. Buscá el artista → Enter para seleccionar
2. Buscá la canción dentro de su catálogo → Enter para abrir
3. ESC vuelve a la lista de artistas

**En la pantalla de una canción:**

- Botones numerados para cambiar entre versiones (acordes / tablatura / bajo / armónica / etc.)
- Teclas **1–N** para cambiar de versión desde el teclado
- **▶ Ver en YouTube** — abre el video en el browser predeterminado
- **⬇ Descargar + Separar pistas** — descarga el audio y ejecuta el pipeline de análisis
- **⬡ Exportar PDF** — genera un PDF multi-columna optimizado para ocupar la menor cantidad de páginas posible, guardado en `~/Downloads/`

---

## Formato de la biblioteca de acordes

La biblioteca es un directorio con la siguiente estructura:

```
<library-root>/
├── {artist_slug}/
│   ├── {song_slug}/
│   │   ├── meta.json
│   │   ├── version_main.txt
│   │   ├── version_2.txt        ← versiones adicionales (opcional)
│   │   └── version_3.txt
│   └── {otro_song_slug}/
│       ├── meta.json
│       └── version_main.txt
└── {otro_artist_slug}/
    └── ...
```

Los slugs usan minúsculas y guiones bajos (`violeta_parra`, `la_cancion`).

### meta.json

Cada canción requiere un archivo `meta.json` con el siguiente esquema:

```json
{
  "title": "La Canción",
  "artist": "El Artista",
  "artist_slug": "el_artista",
  "song_slug": "la_cancion",
  "youtube_url": "https://www.youtube.com/embed/VIDEO_ID",
  "versions": [
    {
      "version_num": 1,
      "type": "acordes",
      "file": "version_main.txt",
      "youtube_url": "https://www.youtube.com/embed/VIDEO_ID"
    },
    {
      "version_num": 2,
      "type": "tablatura",
      "file": "version_2.txt",
      "youtube_url": "https://www.youtube.com/embed/VIDEO_ID"
    }
  ]
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `title` | string | Nombre de la canción para mostrar |
| `artist` | string | Nombre del artista para mostrar |
| `artist_slug` | string | Debe coincidir con el nombre del directorio padre |
| `song_slug` | string | Debe coincidir con el nombre del directorio de la canción |
| `youtube_url` | string \| null | URL de embed de YouTube (ver formato abajo) |
| `versions` | array | Al menos una versión requerida |
| `versions[].version_num` | int | Número de versión (1, 2, 3…) |
| `versions[].type` | string | Tipo: `acordes`, `tablatura`, `bajo`, `armonica`, `bateria`, `ukulele`, `piano`, etc. |
| `versions[].file` | string | Nombre del archivo de texto dentro del mismo directorio |
| `versions[].youtube_url` | string \| null | Puede repetir el del nivel raíz o ser diferente |

### Formato del YouTube URL

El campo `youtube_url` debe usar el formato de **embed**, no el de watch:

```
✓  https://www.youtube.com/embed/VIDEO_ID
✗  https://www.youtube.com/watch?v=VIDEO_ID
✗  https://youtu.be/VIDEO_ID
```

El TUI convierte automáticamente el formato embed al formato watch para descargar con `yt-dlp` y para abrir en el browser.

Puede ser `null` si la canción no tiene video asociado; en ese caso los botones de YouTube no aparecen.

### Archivos de contenido (version_main.txt, version_2.txt…)

Texto plano con el contenido de acordes/tablatura. El TUI muestra el contenido tal cual, pero elimina automáticamente bloques de encabezado y pie de página delimitados por líneas de `===`:

```
=====================================   ← eliminado (encabezado)
| ARTISTA: El Artista                |
| CANCION: La Canción                |
=====================================   ← eliminado

[CONTENIDO VISIBLE: letra y acordes]

=====================================   ← eliminado (pie)
Derechos reservados...
=====================================   ← eliminado
```

Si el archivo no tiene este formato, se muestra completo sin modificaciones.

### Índice SQLite (opcional, para carga rápida)

Con miles de artistas, la carga inicial puede ser lenta si el TUI tiene que leer un `meta.json` por artista para obtener los nombres. Se puede proveer un índice SQLite con la siguiente tabla:

```sql
CREATE TABLE artists (
    slug TEXT PRIMARY KEY,
    name TEXT,
    status TEXT DEFAULT 'done'
);
```

El TUI lo detecta automáticamente si existe un archivo `library.db` dentro del directorio de la biblioteca o en su directorio padre. También se puede indicar la ruta explícitamente con `CHORD_LIBRARY_DB` (ver Variables de entorno).

---

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `CHORD_LIBRARY` | `~/chord-library` | Ruta al directorio raíz de la biblioteca de acordes |
| `CHORD_LIBRARY_DB` | auto-detectado | Ruta al SQLite de índice de artistas (opcional) |

Las variables pueden definirse en un archivo `.env` en el directorio desde donde ejecutás `music-tui` — se carga automáticamente al iniciar. Copiá el ejemplo incluido para empezar:

```bash
cp .env.example .env
# luego editá .env con tus rutas
```

O exportarlas en el shell:

```bash
export CHORD_LIBRARY=/data/mis-acordes
export CHORD_LIBRARY_DB=/data/mis-acordes/library.db
make run
```

---

## Dependencias del sistema

| Herramienta | Uso |
|-------------|-----|
| `yt-dlp` | Descarga de YouTube |
| `ffmpeg` | Conversión de audio |
| `mpv` o `ffplay` | Reproducción de stems en el TUI |

## Archivos generados

```
~/.music-processor/
├── downloads/          # audios descargados de YouTube
├── history.json        # índice de todas las canciones analizadas
└── stems/<canción>/
    └── htdemucs/<canción>/
        ├── drums.mp3
        ├── bass.mp3
        ├── vocals.mp3
        ├── other.mp3
        └── results.json    # tonalidad, BPM, acordes y secciones detectadas
```
