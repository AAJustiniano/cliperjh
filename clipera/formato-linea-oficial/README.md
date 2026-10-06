# Formato Línea Oficial — Clips verticales de J. H. Antelo

Sistema de 4 formatos para clips verticales (TikTok / Reels / Shorts) del **Concejal José Hugo Antelo**, Santa Cruz de la Sierra. Este documento es el contexto completo para editar y animar clips con estos formatos. Las referencias HTML en `formatos/` son la **fuente de verdad visual y de timing**: abrilas en el navegador para ver la animación en loop.

```
formato-linea-oficial/
├─ README.md               ← este documento
├─ index.html              ← vista de los 4 formatos lado a lado
├─ formatos/
│  ├─ pleno.html           ← 01 · sesión del Concejo (video horizontal)
│  ├─ cara-a-cara.html     ← 02 · respuesta a cámara (video vertical)
│  ├─ la-cifra.html        ← 03 · dato / número protagonista
│  ├─ tapa-serie.html      ← 04 · portada de serie / primer frame
│  ├─ base.css             ← fuentes + estilos compartidos
│  └─ motion.js            ← motor de animación de referencia
└─ assets/
   ├─ fonts/               ← Bastardo Grotesk (Thin 100 → Black 900)
   ├─ banderines/          ← banderín: blanco, rojo, negro, amarillo ×2 (PNG transparente)
   └─ colores.png          ← hoja oficial de colores
```

Parámetros de las referencias: `?static` muestra el estado final (para thumbnails), `?guias` superpone zonas seguras, `?ms=2500` congela el frame en ese milisegundo. Un click en el lienzo reinicia la animación. Los elementos llevan `data-layer`, `data-slot` (donde va el video/foto), `data-fx` (efecto), `data-in` / `data-dur` / `data-out` (ms).

---

## 1. Marca — lo mínimo que hay que respetar

**Colores** (no hay otros; sin degradados, sin texturas):
| Token | Hex | Uso |
|---|---|---|
| Rojo | `#FA0404` | Señal principal, bloques, acentos |
| Navy | `#011B34` | Fondo de Pleno, autoridad |
| Ámbar | `#ECA400` | Palabra clave en subtítulos sobre fondo oscuro |
| Onyx | `#161616` | Tinta, fondos oscuros, palabra clave sobre rojo |
| Off White | `#F5EFEE` | Papel, texto sobre color |

**Tipografía:** solo **Bastardo Grotesk**.
- Titulares y subtítulos: Black 900, MAYÚSCULAS, tracking −0.02 a −0.04em, interlineado 0.84–0.94.
- Kickers/etiquetas: Bold 700, MAYÚSCULAS, tracking +0.18em, 18–24px.
- Nada de itálicas, sombras de texto, contornos ni emoji.

**Marcas:** el **banderín** (PNG en `assets/banderines/`) y el **monograma "JH."** (texto JH en Black + cuadrado rojo de 0.19em). No usar otros logos.
- Banderín **blanco** sobre rojo o navy. Banderín **rojo** sobre off white. Nunca deformar: escalar proporcional (relación 1.79:1).

**Voz:** español de Bolivia con voseo (*"Sumate"*, *"Conocé"*). Directo y concreto. Hashtag: `#PorVosSantaCruz` (opcional en la descripción del post, no en el video).

**Esquinas rectas siempre.** Bloques planos. Nada redondeado.

---

## 2. Reglas globales del lienzo

- **Lienzo:** 1080 × 1920 px, 9:16, 30 fps (25 si la fuente es 25), H.264 High, 12–16 Mbps, audio AAC 48 kHz.
- **Duración:** 15–60 s. Gancho en los primeros 1.5 s.
- **Zonas seguras** (la interfaz de TikTok las tapa):
  - Arriba: `y 0–150` — nada importante.
  - Derecha: `x 940–1080`, `y 720–1540` — columna de botones.
  - Abajo: `y 1540–1920` — descripción y música. Los subtítulos tienen que **terminar antes de y≈1560**. Si un cue llega a 3 líneas, reducir el tamaño un 10% antes que invadir la zona.
- **Margen lateral de texto:** 72 px.

---

## 3. Movimiento — tokens

| Token | Valor |
|---|---|
| Easing de entrada | `cubic-bezier(0.2, 0, 0, 1)` (sale rápido, frena suave) |
| Easing de salida | `cubic-bezier(0.4, 0, 1, 1)` |
| Bloques (wipe) | 400–450 ms |
| Texto (slide-up) | 400 ms, desplazamiento 24 px + fade |
| Etiquetas | 300 ms |
| Salidas | 300 ms, el orden inverso de la entrada |
| Escalonado entre capas | 70–150 ms |

**Efectos permitidos** (`data-fx`):
- `wipe-l / wipe-r / wipe-t / wipe-b` — el bloque se revela con un recorte (clip) desde un lado. Es el gesto de la marca: **los bloques de color se "dibujan", no aparecen con fade.**
- `up` — texto sube 24 px y aparece. Siempre **después** de su bloque (+120–150 ms).
- `left` — el banderín entra desde la izquierda 48 px + fade.
- `grow-y` — barras rojas que crecen desde abajo.
- `fade` — solo para el monograma y el corte de entrada del video.
- `push` — zoom lento 1.00 → 1.04 lineal, solo en la foto de Tapa.

**Prohibido:** rebotes, overshoot, elastic, giros, blur, glitch, typewriter letra por letra, loops decorativos, transiciones de plantilla de CapCut. El movimiento es seco y editorial.

---

## 4. Subtítulos — cómo se animan

Son el elemento más importante. Reglas comunes a todos los formatos:

1. **Fuente:** transcripción con timestamps por palabra (ej. Whisper / WhisperX). Corregir ortografía, tildes y nombres propios (*Plan 3000, Concejo, Santa Cruz*).
2. **Cortes de cue:** 2–6 palabras por cue, máximo 3 líneas, máximo ~22 caracteres por línea a 78 px. Cortar en pausas naturales y signos de puntuación. Nunca dejar una palabra sola en la última línea (usar `text-wrap: balance`). Duración mínima de un cue: 700 ms.
3. **Entrada por palabra:** cada palabra aparece cuando se dice: opacidad 0 → 1 y sube 0.15em, **140 ms**, easing de entrada. La palabra queda en su lugar final (el bloque no "se arma" moviéndose: la posición de cada palabra está fija desde el inicio del cue, solo se revela).
4. **Cambio de cue:** corte seco (≤ 60 ms de fade). Sin deslizamientos entre cues.
5. **Palabra clave:** como máximo **una frase destacada por cue** (la promesa, la cifra, el problema). Se pinta con el color de acento del formato desde que aparece. En las referencias se marca con `*asteriscos*` en el JSON de cues.
6. **Posición fija:** el bloque de subtítulos no se mueve en todo el clip, aunque entre o salga otra capa.
7. MAYÚSCULAS, Black 900. Mantener signos `¿?` `¡!`.

Formato de cues usado en las referencias:
```json
[{ "t": 1200, "d": 1400, "text": "Primero hay que" },
 { "t": 2600, "d": 1600, "text": "*ordenar las rutas*" }]
```
`t` = inicio en ms, `d` = duración en ms. En producción, `t` de cada palabra debe venir del timestamp real del audio, no del reparto uniforme que hace `motion.js`.

---

## 5. Los formatos

### 01 · Pleno — `formatos/pleno.html`
Para fragmentos de **sesiones del Concejo**, que se graban en **horizontal**. El video 16:9 va en una franja central y el resto del lienzo es marca.

| Capa | Posición (x, y, ancho × alto) | Contenido |
|---|---|---|
| Fondo | 0, 0, 1080 × 1920 | Navy `#011B34` |
| Encabezado | 0, 0, 1080 × 380 | Bloque off white. Kicker "Sesión del Concejo Municipal" + titular del tema (Black 86 px, máx. 3 líneas, alineado abajo con padding 44 px) |
| Banderín | 48, 425, 221 × 123 | Banderín blanco |
| Video | 0, 592, 1080 × 608 | Video horizontal escalado a 1080 de ancho (recorte cover si no es exacto 16:9) |
| Bloque inferior | 0, 1216, 1080 × 704 | Rojo `#FA0404`, padding 44/72 |
| ↳ Nombre (izq.) | arriba-izquierda del bloque | "JOSÉ HUGO ANTELO" Black 44 + "CONCEJAL · SANTA CRUZ" Bold 20 |
| ↳ Fecha (der.) | arriba-derecha del bloque | "14 OCT 2026" Black 44 + tipo de sesión Bold 20, alineada a la derecha |
| ↳ Regla | ancho completo, 3 px | Off white, 32 px arriba / 36 px abajo |
| ↳ Subtítulos | debajo de la regla | Black 78 px off white. Palabra clave en **onyx** |

**Timeline (ms):**
- `0` encabezado wipe desde arriba (400) → `200` kicker sube → `280` titular sube
- `300` corte de entrada del video
- `350` bloque rojo wipe desde abajo (450)
- `450` banderín entra desde la izquierda
- `650` nombre sube · `700` regla wipe izq→der · `720` fecha sube
- `1000` primer subtítulo (o cuando empieza a hablar)
- Nombre y fecha **permanecen** todo el clip (es la firma del formato).
- **Cierre** (últimos 1.4 s): bloque rojo a pantalla completa wipe desde abajo (400) + banderín blanco centrado, 640 px de ancho, sube a los +250 ms. Se mantiene hasta el final.

### 02 · Cara a cara — `formatos/cara-a-cara.html`
Para entrevistas y respuestas a cámara grabadas en **vertical** (o horizontal recortado a 9:16 centrado en la cara).

| Capa | Posición | Contenido |
|---|---|---|
| Video | 0, 0, 1080 × 1920 | Pantalla completa |
| Etiqueta | 72, 180 | Rojo, "ENTREVISTA" Bold 22 |
| Pregunta | 72, ~240, máx. 860 ancho | Bloque off white, Black 64 px onyx. Es el gancho |
| Monograma | derecha 72, 188 | "JH." off white 64 px, cuadrado rojo |
| **Lower third** | 72, 1060 | Barra roja 14 px + panel off white: "JOSÉ HUGO ANTELO" Black 40 + cargo Bold 18 |
| Subtítulos | 72, 1210, 936 ancho | Black 68 px off white, cada línea en caja onyx (`box-decoration-break: clone`, padding 2/16). Palabra clave en **ámbar** |

**Lower third — entra y sale.** Identifica al concejal y se retira para que queden solo los subtítulos y la cara:
- Entrada: `800` barra roja crece desde abajo (250) → `950` panel wipe izq→der (350) → `1080` texto sube (400).
- Permanencia: **~3.2 s** (hasta `4300`). En clips de más de 30 s puede reaparecer una sola vez en la mitad.
- Salida (orden inverso, 300 ms cada una, easing de salida): `4300` texto baja y se desvanece → `4450` panel wipe der→izq → `4600` barra se encoge.
- Los subtítulos **no se mueven** cuando el lower third sale.

**Pregunta:** `150` etiqueta wipe → `300` bloque wipe → `450` texto sube. Queda fija todo el clip (contexto para quien entra a mitad del loop). Si el clip tiene varias preguntas, la pregunta sale (wipe der→izq 300) y entra la siguiente con la misma secuencia.

**Monograma:** fade 300 ms a los `200`, fijo.

### 03 · La cifra — `formatos/la-cifra.html`
Para clips cuyo argumento es **un número** (barrios, montos, porcentajes, vecinos escuchados).

| Capa | Posición | Contenido |
|---|---|---|
| Fondo | — | Off white `#F5EFEE` |
| Kicker | 72, 170 | Frase corta de tono: "ES INSOSTENIBLE" Bold 22 |
| Banderín | arriba a la derecha, alto 96 | Banderín rojo |
| Cifra | 72, ~230 | Black 300 px rojo, `tabular-nums`. Formato boliviano: punto de miles (`+12.400`) |
| Etiqueta de la cifra | debajo | Black 60 px onyx, máx. 2 líneas |
| Video | 72, 740, 936 × 527 | 16:9 con márgenes |
| Banda inferior | 0, 1300, 1080 × 620 | Onyx. Firma (nombre · cargo izq., fecha der., Bold 20) + subtítulos Black 72 off white, clave en **ámbar** |

**Timeline:** `100` kicker sube · `200` banderín entra · `200–1100` **la cifra cuenta de 0 al valor** (900 ms, ease-out cúbico; los dígitos no saltan de ancho gracias a tabular-nums; el prefijo `+`/`Bs` queda fijo) · `600` video wipe izq→der · `800` banda wipe desde abajo · `950` etiqueta sube · `1100` firma sube · `1400` subtítulos.
Si la cifra se menciona en el audio, el conteo debe **terminar** justo cuando se pronuncia.

### 04 · Tapa de serie — `formatos/tapa-serie.html`
Portada para series recurrentes ("Concejo al día", episodios). Se usa como **thumbnail** (exportar `?static`) y como **primer segundo** del clip antes de cortar al contenido.

| Capa | Posición | Contenido |
|---|---|---|
| Fondo | — | Rojo |
| Foto | 0, 0, 1080 × 1080 | Retrato documental del concejal |
| Etiquetas | 72, 260 | "EP. 03" (off white / onyx) + nombre de la serie (onyx / off white) |
| Título | 72, 1120 | Black 150 px off white, máx. 3 líneas |
| Bajada | debajo del título | "→ …" Bold 24 onyx |
| Banderín | 52, 1560, alto 150 | Banderín blanco |

**Recorte del perfil:** la grilla de TikTok muestra solo `y 240–1680` (3:4). Título y etiquetas tienen que estar dentro de esa franja.

**Timeline (0.9–1.5 s antes de cortar):** foto con push lento 1.00→1.04 durante todo el plano · `300` "EP." wipe · `420` serie wipe · `500` / `580` líneas del título suben escalonadas · `800` bajada sube · `900` banderín entra. Corte seco al primer plano del contenido.

---

## 6. Flujo sugerido para producir clips (Claude Code)

1. **Elegir formato** según la fuente: sesión horizontal → Pleno · entrevista/vertical → Cara a cara · argumento numérico → La cifra · serie → Tapa como intro.
2. **Transcribir** con timestamps por palabra y armar los cues según §4.
3. **Rellenar textos**: titular del tema, fecha (`DD MMM AAAA` en Pleno, `DD.MM.AAAA` en La cifra), pregunta, cifra.
4. **Componer** reproduciendo las capas y timings de las referencias. Opciones recomendadas:
   - **Remotion** (React): portar cada HTML a una composición 1080×1920 @30fps; convertir los ms a frames (`frame = ms × 0.03`); reemplazar `data-slot` por `<OffthreadVideo>`.
   - **Overlay + ffmpeg**: renderizar la gráfica como video con alfa (ProRes 4444 / WebM VP9) y superponer sobre el video escalado/recortado a la caja del `data-slot`.
5. **Revisar con `?guias`** que nada importante caiga en zonas seguras.
6. **Exportar** según §2 y generar el thumbnail desde Tapa (`?static`) o desde el frame final del formato.

**Checklist antes de publicar:** tildes y voseo correctos · una sola palabra clave por cue · lower third sale a los ~4.3 s · subtítulos fuera de la zona inferior · nada redondeado, sin degradados, sin emoji · banderín sin deformar.
