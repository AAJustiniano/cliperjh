# Template 0: clip vertical "noticiero amarillista"

Primer uso: clips de José Hugo Antelo en el Concejo (Claude/Projects/antelo-clips, 2026-09-30). Configuración real en `example/`.

## Formato

| Elemento | Especificación |
|---|---|
| Lienzo | 1080×1920, 30 fps, H.264 CRF 18, AAC 192k, −14 LUFS / TP −1.5 |
| Encabezado | Franja negra y=0–520 |
| Etiqueta (kicker) | Montserrat Black 58, blanco sobre caja roja #E31C1C, centrada en y=160, entra con pop 70→100 % |
| Titular | Montserrat Black 88, MAYÚSCULAS, blanco con palabras clave en amarillo #FFE500 (`*así*`), centrado en y≈350, máx. 2–3 líneas |
| Video | 1080×1400 de y=520 al fondo (proporción 0.77), recorte del original centrado en la cara (~1.9× zoom), sin zócalo del canal |
| Nombre | Montserrat Bold 40 en caja verde #1F9A3A, arriba a la izquierda del video (40, 546) |
| Subtítulos | Montserrat Bold 96, MAYÚSCULAS, blanco con borde negro 7 y sombra, centrados en y=1545; palabra actual en amarillo; bloques de ≤4 palabras / ≤14 caracteres, cortan en puntuación y pausas >0.45 s; cada bloque entra con pop 86→100 % |
| Degradado | Negro de y=1300 (0 %) a 1920 (70 %) detrás de los subtítulos y la UI de TikTok |
| Nombres de archivo | `NN_tema.mp4` (máx. un guion, mejor ninguno) |

Titulares: amarillistas, en MAYÚSCULAS. Usa comillas solo si la cita es textual; una paráfrasis va sin comillas.

## Flujo (desde la carpeta del proyecto)

1. Descarga. Preferido: audio completo + video 1080 por tramos (ver skill `/clipera` §2 y el campo `tramos` de clips.json). Con un en vivo recién terminado `--download-sections` devolvió basura (2026-09-30); en ese caso, y solo si el usuario lo confirma, se baja el video completo:
   `python -m yt_dlp --js-runtimes node -f 299 -N 8 -o src/video.mp4 URL` y `-f 140 -o src/audio.m4a`
   (yt-dlp está en `AppData/Local/Python/bin/python.exe`.)
2. Escribe `clips.json` (ver `example/clips.json`). Cada segmento lleva `from`/`to` en segundos, `tag`, y opcionalmente `x` (centro de la cara), `y` (tope del recorte, default 60) y `h` (alto, default 730). `y + h` debe quedar por debajo de `lower_third_y` (835 en el Concejo). Si la cámara encuadra más arriba, usa `y` 40 y `h` 780.
3. `<hermes python> t0.py transcribe`: whisper large-v3-turbo por segmento. faster-whisper solo existe en `AppData/Local/hermes/hermes-agent/venv/Scripts/python`.
4. Revisa el texto y corrige errores en `fixes.json` (`[["palabras mal", "palabras bien"], ...]`).
5. `python t0.py faces`: completa `x` en clips.json. Necesita `opencv-python-headless<5`.
6. `python t0.py cut` y luego `python t0.py subs`. Al final de cualquier comando se pueden poner nombres de clips para procesar solo esos.
7. Control de calidad: saca fotogramas de `final/` y revisa que la cabeza no se corte y que los subtítulos queden debajo del mentón.
