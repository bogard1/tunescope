# Roadmap — Music Processor

Features planeadas para versiones futuras, ordenadas por complejidad aproximada.

---

## Corto plazo

### Transposición de acordes en tiempo real
En `ResultsScreen`, atajos `+` / `-` para transponer todos los acordes N semitonos hacia arriba o abajo. Útil para adaptar a diferentes afinaciones o posiciones de cápodastro.
- Solo manipulación de strings en memoria, sin re-análisis.
- Mostrar indicador de transposición activa en el `#summary`.

### Capo advisor
Dado el set de acordes detectados, calcular en qué posición de cápodastro (1–7) el número de acordes con cejilla se minimiza. Lógica pura, sin dependencias nuevas.
- Agregar como sugerencia en `ResultsScreen` debajo del summary.

### Exportación ChordPro
Exportar la hoja de acordes en formato `.cho` / `.chopro` estándar, legible por apps como OnSong, Songbook, GuitarTapp.
- Formato: `{title:...}`, `{artist:...}`, `[Am]palabra [G]siguiente`
- Alternativa liviana al PDF actual. Agregar botón en `ResultsScreen`.

---

## Medio plazo

### Generación MIDI de progresión
Generar un archivo `.mid` básico con la progresión de acordes detectada usando `mido` (sin torch, sin dependencias pesadas).
- Cada acorde ocupa su duración detectada.
- Permite importar la progresión en cualquier DAW.

### Reproducción con barra de progreso
Mejora al sistema de playback ya existente en `ResultsScreen`:
- Mostrar tiempo actual / duración total mientras suena un stem.
- Requiere polling periódico al proceso mpv (con `--input-ipc-server`) o uso de `sounddevice` / `pygame.mixer`.

### Búsqueda por similitud de progresión
Dado el set de acordes detectados en una canción, buscar canciones similares en la biblioteca local usando Jaccard similarity entre sets de acordes.
- Implementable en `library/index.py` con una función `find_similar(chord_set)`.
- Mostrar resultados en una nueva pantalla o modal.

---

## Largo plazo

### Detección de letra (speech-to-text)
Transcribir automáticamente la letra de la canción a partir del stem `vocals` generado por Demucs, usando [OpenAI Whisper](https://github.com/openai/whisper).
- Agregar `transcribe()` en `pipeline/` que corra `whisper` sobre `vocals.mp3`
- Mostrar la letra sincronizada con los acordes en `ResultsScreen` (letra + acorde por encima de cada línea)
- Exportar en el PDF junto a los acordes detectados
- Requiere `pip install openai-whisper` (~1.5 GB con modelo `medium`); el modelo `tiny` (~75 MB) es suficiente para un borrador rápido

### Batch processing
Aceptar como input una carpeta de archivos o una playlist de YouTube y encolar todas las canciones para procesarlas en secuencia.
- Agregar una pantalla de cola con progreso individual por canción.
- Guardar cada resultado en `~/.music-processor/` y en el historial automáticamente.

### Modo comparación
Mostrar dos canciones analizadas lado a lado en `ResultsScreen` para comparar progresiones, tonalidad y BPM.
- Útil para analizar covers o versiones alternativas.

### Integración con Spotify
Buscar canciones en Spotify, obtener la URL de preview (30s) o abrir en el cliente de Spotify.
- Requiere Spotify API credentials (Client ID + Secret).
- Puede complementar la biblioteca de acordes con metadatos (álbum, año, popularidad).

### Detección de modo / escala sugerida
A partir de la tonalidad detectada, sugerir escalas para improvisar (pentatónica, dórica, lidia, etc.).
- Mostrar en el summary de `ResultsScreen`.
- Sin dependencias extra: solo lógica de teoría musical.
