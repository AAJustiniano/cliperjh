# clipera

Skill de Claude Code: link de YouTube + timestamps -> clips verticales (TikTok/Reels) con template, titulares y captions.

## Instalar

Requiere Claude Code, Python 3, ffmpeg y yt-dlp.

```bash
git clone https://github.com/AAJustiniano/cliperjh.git
mkdir -p ~/.claude/skills
cp -r cliperjh/clipera ~/.claude/skills/clipera
```

En Windows (PowerShell):

```powershell
git clone https://github.com/AAJustiniano/cliperjh.git
Copy-Item -Recurse cliperjh\clipera $HOME\.claude\skills\clipera
```

Reiniciá Claude Code y usá `/clipera <link>`.

Incluye: `SKILL.md`, `clip-templates/` (template0, 1, 2 con fuentes) y `formato-linea-oficial/` (spec y referencias HTML de la línea oficial).
