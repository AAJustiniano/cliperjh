---
name: clipera
description: Generador de clips verticales (TikTok/Reels) a partir de un video de YouTube con timestamps de una intervención, para la página satélite o la oficial. Usar cuando el usuario pasa un link + tiempos para sacar clips, dice "clipera", "sacá clips", "clips amarillistas", "template 0/1/2", o quiere pasar un clip de la satélite a la oficial.
---

# Clipera

Link + tiempos → propuesta de clips → **el usuario aprueba** → render con el template elegido → entrega + captions.
Nada se renderiza con texto antes de que el usuario apruebe titulares y template.

## 1. Entrada

El usuario manda algo así. Lo que falte (quién habla, destino, template) se pregunta con botones, sin asumir: primero quién habla + destino en un mismo AskUserQuestion; después, en otro, el template de ese destino (y la miniatura si es oficial). La descarga del audio arranca antes de preguntar.

```
/clipera <link>
Intervención: 9:20–13:59 y 55:01–58:40
Responde a: Mario Guerrero 1:57–2:04 (hasta "ha elevado los precios del combustible")   ← opcional
Quién habla: concejal José Hugo Antelo
Destino: satélite | oficial
Template: 0 | 1 | 2             (ver tabla de la sección 4)
Notas: lo más amarillista posible / tema / qué evitar
```

**Template: nunca elegirlo por tu cuenta.** Si vino en el mensaje, usalo. Si no vino, tu primera respuesta es AskUserQuestion con una opción por cada template de la tabla de la sección 4 para ese destino, más "otro formato". La descarga puede arrancar mientras tanto, pero no se escribe nada de la propuesta hasta tener el template, porque cambia los campos (etiqueta en el 0, fecha en el 1).

Apenas llega el link, **arrancá la descarga en segundo plano** (no depende del template) mientras hacés lo demás.

## 2. Descarga y transcripción

Proyecto nuevo en `~/clipera-clips/AAAAMMDD_tema/` (sin guiones). Pasos técnicos, rutas de python y trampas conocidas: `~/.claude/skills/clipera/clip-templates/template0/README.md` → sección Flujo.

**Nunca bajar el en vivo completo sin preguntar.** Orden:
1. **Audio completo primero** (`-f 140`, ~60 MB/hora) → `src/audio.m4a`. Transcribir enseguida los rangos de intervención con whisper large-v3-turbo (hermes venv) y `whisper_prompt` con los nombres propios del caso. La propuesta de clips sale de acá, sin esperar el video.
2. **Video 1080p solo por tramo, en paralelo.** Siempre 1080 (`-f 299`, o el mejor de 1080 si no existe 299); nunca 720. Un archivo por intervención, con ±15 s de colchón:
   `yt-dlp -f 299 --download-sections "*{inicio}-{fin}" --force-keyframes-at-cuts -o src/tramoN.mp4 URL`
   En `clips.json` va `"tramos": [{"file": "src/tramo1.mp4", "start": <inicio en s>}, ...]` y los `from`/`to` de los clips siguen en tiempo de YouTube (t0.py traduce solo).
3. **Verificar cada tramo** con ffprobe: duración ≈ fin − inicio y tamaño razonable (un archivo de pocos KB es basura). Si sale basura, lo más probable es que YouTube no terminó de procesar el en vivo. **No bajes el completo por tu cuenta**: AskUserQuestion con "Esperar y reintentar más tarde" (recomendado; el usuario manda el link de nuevo cuando YouTube lo procese) / "Bajar el en vivo completo".

## 3. Propuesta (puerta de revisión)

Leé la transcripción y proponé los clips. Criterios:
- 15–55 s. Arranca en frase limpia (nunca a mitad de oración) y cierra en el remate.
- Un clip = una idea fuerte: frase picante, golpe directo, humor, dato, desafío.
- Si hay a quién responde, el mejor clip suele ser **pregunta/acusación → respuesta** en un mismo clip (2 segmentos).
- Titulares amarillistas, MAYÚSCULAS, 1–2 palabras clave en `*amarillo*`. Comillas **solo** si la cita es textual; paráfrasis va sin comillas. Nunca inventar algo que no dijo.

Presentá una tabla **antes de cortar nada**:

| # | Archivo | Tramo(s) | Dur. | Arriba: etiqueta | Arriba: titular | Abajo: nombre | Arranca / cierra en |
|---|---|---|---|---|---|---|---|
| 1 | 01_culpa_paz | 1:59–2:04 + 10:11–10:25 | 19 s | ¡SE PRENDIÓ EL CONCEJO! | ¿LA CULPA ES DE PAZ? *ANTELO LE RESPONDE* | MARIO GUERRERO → CONCEJAL JOSÉ HUGO ANTELO | "Y pues no es la culpa…" / "…un prófugo en el Chapare" |

Debajo de la tabla: 1 titular alternativo para cada clip, y las frases que whisper entendió dudosas.

Armá la tabla según el template elegido: con template 1 no hay columna de etiqueta y se suma "fecha" abajo. Arriba de la tabla, recordá qué template quedó ("Template 1 — podés cambiarlo").

El usuario edita lo que quiera (titulares, tramos, quitar/sumar clips). Iterá hasta un OK explícito. Recién ahí escribí `clips.json` + `fixes.json`.

## 4. Templates

Todos en `~/.claude/skills/clipera/clip-templates/`. El `clips.json` es el mismo para todos: cambiar de template = volver a correr `subs` con otro script.

| Línea | Template | Look | Campos |
|---|---|---|---|
| Satélite | `template0` (t0.py) | Franja negra + etiqueta roja + titular Montserrat, video 1080×1400 en la cara, subtítulos Montserrat amarillo palabra a palabra | kicker, headline, tag |
| Satélite | `template1` (t1.py) | Caja roja con titular Oswald, video ancho completo que funde a panel ladrillo, nombre + fecha, subtítulos Oswald grandes. **Miniatura**: `t1.py thumb` → `miniaturas/NN.png` (portada de TikTok con el mismo titular, dentro de la zona 3:4 de la grilla; ver README) | headline (`\|` fuerza corte), tag, date, `thumb` opcional |
| Satélite | `template2` (t2.py) — "Contexto hor" | Fondo papel, titular Anton negro con frase resaltada en lima, video del pleno 4:3 a ancho completo debajo, píldora lima con el nombre, subtítulos Archivo Black blancos con borde y 1–2 palabras clave en lima. Ideal para tomas horizontales/planos abiertos | headline (`*frase*` en lima, `\|` fuerza corte), tag, `keywords` opcional |
| Oficial | `pleno` | Sesión del Concejo (video horizontal en franja central), encabezado off white, bloque rojo con nombre + fecha fijos y subtítulos | kicker, headline, fecha, tipo de sesión |
| Oficial | `cara-a-cara` | Video vertical a pantalla completa, pregunta-gancho arriba, lower third que entra y sale, subtítulos en cajas onyx | pregunta, tag |
| Oficial | `la-cifra` | Número gigante que cuenta hasta el valor, video 16:9 con márgenes, banda onyx con subtítulos | kicker, cifra, etiqueta de la cifra, fecha |
| Oficial | `tapa-serie` (decile **miniatura**) | No es un clip: portada con episodio, serie y título sobre foto. Se ofrece como extra con 3 opciones: "Sin miniatura" / "Solo miniatura" (imagen para subir como portada en TikTok) / "Miniatura + intro" (además entra como el primer segundo del clip) | episodio, serie, título, bajada, foto |

Línea oficial: spec y referencias HTML (fuente de verdad visual y de timing) en `~/.claude/skills/clipera/formato-linea-oficial/` (leé su README entero antes de usarla: colores, Bastardo Grotesk, zonas seguras, movimiento seco, sin emoji). Todavía no tiene script de render: la primera vez que se use, construilo (README §6) en `clip-templates/oficial/` y probalo contra la referencia con `?ms=` antes de renderizar en serie.

Con destino satélite, las opciones del botón son los templates satélite; con oficial, `pleno` / `cara-a-cara` / `la-cifra` (+ pregunta aparte por la miniatura). Sugerí en la opción recomendada el que calce con la fuente (sesión horizontal → pleno, entrevista → cara a cara, argumento numérico → la cifra).

Cada README tiene la spec completa. Al sumar un template nuevo: carpeta `templateN/` con README + script + `example/`, y una fila acá.

## 5. Render y control

`transcribe` → `faces` → `cut` → `thumb` → `subs` (ver README del template). Con template 1 la miniatura va siempre: `subs` la pone en el fotograma 0 de cada final, así TikTok la toma como portada sin subirla a mano. Entregá también la ruta completa de `miniaturas/`. Después sacá una hoja de control (2 fotogramas por clip) y revisá: cabeza entera, subtítulos bajo el mentón, sin zócalo del canal, primera palabra completa. Corregí y re-renderizá solo los clips afectados.

## 6. Entrega

- SendUserFile con los finales + **ruta completa de Windows** a la carpeta `final/`, sola en un bloque de código para copiar y pegar en el Explorador, por ejemplo:
  ```
  ~/clipera-clips/20261001_movilidad\final
  ```
  Ruta absoluta entera, con barras invertidas. Nunca la acortes a las últimas carpetas ni la des como link relativo: el usuario mira los clips desde el Explorador porque el visor de videos de Claude se traba.
- Lista corta de frases a escuchar antes de publicar (correcciones de transcripción que hiciste sin oír).
- Captions **muy cortos**, uno por clip, **máximo 5 palabras** sin contar emoji ni hashtag: `"Frase gancho" 🔥 #santacruz #transportepublico #politica #josehugoconcejal` (el usuario rechazó los largos; el 2.º hashtag cambia según el tema del clip, los otros tres van fijos). Cada caption en su propio bloque de código para copiar.
- Nombres de archivo `NN_tema.mp4`, máximo un guion.
- Agregá una fila por clip a `~/clipera-clips/registro.csv` (`fecha,proyecto,clip,titular,template,destino,vistas`; vistas queda vacío, lo llena el usuario). Sirve para elegir qué clips pasan a la oficial.

### Borrar el original (solo con botón)

**Nunca borres `src/` por tu cuenta**, ni al entregar: puede haber cambios que lo necesiten. Al final de la entrega, AskUserQuestion: "¿Borro el video original de este proyecto (`src/`, N MB)?" con "Todavía no" (primera opción) / "Sí, borrar". Solo con "Sí, borrar" se borra; `cortes/` y `final/` quedan siempre. Si elige "Todavía no", el usuario puede pedirlo más adelante en cualquier sesión ("borrá el original de <proyecto>"): mostrá el tamaño y volvé a confirmar con el botón antes de borrar.

## Pasar un clip a la oficial

El usuario dice qué clips rindieron. Copiá su `clips.json` (solo esos clips) a un proyecto nuevo, revisá titulares con el tono de la oficial (otra vez puerta de revisión), y renderizá con el template oficial. Sin template oficial todavía: pedile la línea gráfica.
