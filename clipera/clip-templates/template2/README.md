# Template 2: Satélite · Contexto hor

Instalado el 2026-10-03 desde la maqueta del usuario (`example/template.html` + `styles.css` + `spec.json`). Comparación maqueta (izq.) vs. render (der.) en `example/comparacion_referencia.png`; fotograma real en `example/muestra_01.png`.

## Formato (lienzo 1080×1920, fondo papel #F3F2EE)

| Elemento | Especificación |
|---|---|
| Titular | Anton 100 px, MAYÚSCULAS, tinta #0D0D0C, x=64 y=180, interlínea 108, ancho máx. 952, corte balanceado (`\|` fuerza corte). Máx. 3 líneas (avisa si pasa). `*frase*` → fondo lima #C8F031 (12–92 % de la caja, 10 px de margen) |
| Video | 1080×810 (4:3) a ancho completo, 44 px debajo del titular (y=548 con 3 líneas, 440 con 2). Recorte del original y=0–820, por encima del zócalo del canal, centrado en `x` |
| Nombre | Píldora lima, Archivo ExtraBold 26 px, en (64, 32) del video. Sale del `tag` de cada segmento (se respeta mayúsc./minúsc.) |
| Subtítulos | Archivo Black (la familia aparte, no Archivo 900) 84 px, MAYÚSCULAS, blancos con borde negro, centrados en la zona x=40–900, última línea a 40 px del borde inferior del video. Bloques de hasta 2 líneas × 3 palabras, ≤2 s, cortan en puntuación y pausas >0.45 s. 1–2 palabras clave en lima |
| Audio | −14 LUFS, TP −1.5 |

**Palabras en lima.** `"keywords": [...]` por clip (o global) en clips.json. Si no hay, se pinta la palabra más larga (≥6 letras) de cada bloque.

**Calibración.** Tamaños libass ↔ px CSS medidos (`EMK`, `TOPOFF` en t2.py). Subtítulos con la fuente Archivo Black (`fonts/ArchivoBlack-Regular.ttf`), sin escalado.

## Flujo

Igual a template 0/1 (ver `../template0/README.md`), mismo `clips.json` (sin `kicker` ni `date`). Opcional: `keywords`.

```
<hermes python> ../template2/t2.py transcribe
python t2.py faces
python t2.py cut
python t2.py subs
```

t2.py importa `../template0/t0.py`. Sin miniatura todavía (agregar cuando haga falta, como en t1). Sin las variantes 16:9 / 1:1 de la spec: solo 4:3.
