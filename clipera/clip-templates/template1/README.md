# Template 1: caja roja + panel ladrillo

Recreado el 2026-10-01 a partir del mockup del usuario (`example/referencia.webp`). Comparación lado a lado en `example/comparacion_referencia.png` y muestra renderizada en `example/muestra_01.mp4`.

## Formato

| Elemento | Especificación (lienzo 1080×1920) |
|---|---|
| Encabezado | Franja negra y=0–352 |
| Titular | Oswald Bold 121, MAYÚSCULAS, blanco con borde negro 5, palabras clave en amarillo #F8F13B (`*así*`). Va en una caja roja #E32421 ajustada al texto (margen 29/28/23/16 px), centrada en y≈200. Corte automático en 2 líneas con la de arriba más larga; con `|` el corte se fuerza a mano |
| Video | Ancho completo 1080×774 desde y=352, recorte de toda la altura del original centrado en la cara (`x`). Se funde a #5A2115 entre y=900 y 1100, donde el zócalo del canal queda apagado |
| Panel | Degradado #5A2115 → #882A15 (1100–1240), luego #882A15 liso hasta abajo |
| Nombre + fecha | Oswald Bold 86, blanco. Nombre a la izquierda (x=47) y fecha a la derecha (borde x=951), con la parte superior en y=1158. El nombre sale del `tag` de cada segmento y la fecha de `"date"` en clips.json |
| Subtítulos | Oswald Bold 146.5, MAYÚSCULAS, blanco con borde negro 3 y sombra, alineados a la izquierda en x=49 con ancho máximo 902. Bloques de hasta 2 líneas (y=1232 y 1336), palabra actual en amarillo; cortan en puntuación y en pausas >0.45 s |
| Audio | −14 LUFS, TP −1.5 |

**Tipografía.** Oswald Bold con tracking −50 (−0.05 em, aplicado con `\fsp` en línea porque libass ignora el Spacing del estilo). El usuario indicó 140 % de escala vertical, pero con 140 % las letras salían 18 % más altas que en su mockup. Con **118 %** los tres textos coinciden al píxel (alto, ancho y grosor del trazo). Para usar 140 % literal hay que cambiar `SCY` en t1.py y volver a medir `TOP_OFF`.

## Flujo

Es igual al de template 0 (ver `../template0/README.md`) y usa el mismo `clips.json`. Diferencias: no hay `kicker`, hay un campo `"date"` de nivel superior, y los segmentos usan por defecto `y` 0 y `h` 1080 (el original completo).

```
<hermes python> ../template1/t1.py transcribe
python t1.py faces
python t1.py cut
python t1.py thumb      # miniatura; si existe, subs la pone en el fotograma 0
python t1.py subs
```

t1.py importa `../template0/t0.py` para la transcripción, las caras, el corte y las palabras de los subtítulos. Si cambias t0, vuelve a probar t1.

## Miniatura (portada de TikTok)

`python t1.py thumb` → `miniaturas/<clip>.png` (1080×1920). Agregado el 2026-10-02.

| Elemento | Especificación |
|---|---|
| Zona segura | La grilla del perfil de TikTok recorta la portada a 3:4 (y=240–1680): cara y titular van dentro de esa franja |
| Franja negra | y=0–240 con nombre (izq.) + fecha (der.), Oswald Bold 86. Queda fuera de la grilla: es info secundaria |
| Video | Fotograma en y=240–1126, recorte del original de y=0 a 820 (corta antes del zócalo del canal, ~835) centrado en la cara. Funde al panel entre y=1000 y 1130 |
| Titular | El del clip, caja roja Oswald Bold **180** (geometría escalada desde 121), ancho máx. 980, centrado en y=1400. Hasta 3 líneas |
| Fotograma | Automático: cara más grande × más nítida, con los dos ojos abiertos. Para elegirlo a mano: `"thumb": <segundo de YouTube>` en el clip dentro de clips.json |

**Portada en el primer fotograma.** Si `miniaturas/<clip>.png` existe cuando corre `subs`, el fotograma 0 del final pasa a ser la miniatura (dura 1/30 s, no cambia la duración ni la sincronía) y TikTok la toma como portada por defecto. Orden: `cut` → `thumb` → `subs`.
