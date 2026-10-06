# Template 2 "Contexto hor": paper background, Anton headline with a lime highlight, 4:3 full-width video of the
# horizontal plenary, lime name pill on the video, Archivo Black captions (white, black stroke) inside the video.
# Same clips.json/fixes.json as templates 0/1.
#   <hermes python> t2.py transcribe | python t2.py faces | python t2.py cut | python t2.py subs   [clip names...]
# Reuses template0/t0.py for transcribe, faces, cut and caption words. Spec: README.md (from the user's HTML mockup).
import os, re, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "template0"))
import t0
from t0 import CFG, W, H, run, ts, words_for

VW, VH, CUT_TOP = 1080, 810, 548        # 4:3 video; cut renders it at y=548, subs moves it under the headline
t0.TOP, t0.VH, t0.DEF_Y, t0.DEF_H = CUT_TOP, VH, 0, 820   # source slice 0..820 stays above the channel lower third (835)

FONTS = os.path.join(HERE, "fonts")
ANTON, ARCH9, ARCH8 = (os.path.join(FONTS, f) for f in ("Anton-Regular.ttf", "ArchivoBlack-Regular.ttf", "Archivo-ExtraBold.ttf"))
# libass size units -> CSS px (em) and ink top of "H" below \pos at size 100, measured 2026-10-03
EMK = {ANTON: 0.5756, ARCH9: 0.7413, ARCH8: 0.9316}
TOPOFF = {ANTON: 31.5, ARCH9: 25.75, ARCH8: 17.0}
INK, LIME, WHITE = "&H0C0D0D&", "&H31F0C8&", "&HFFFFFF&"   # #0D0D0C, #C8F031 (BGR)
PAPER = "0xF3F2EE"

HEAD_X, HEAD_Y, HEAD_P, HEAD_LH, HEAD_W, GAP = 64, 180, 100, 108, 952, 44
SUB_P, SUB_LH, SUB_CX, SUB_W, SUB_BOTTOM = 84, 85.68, 470, 860, 40   # region x 40..900, 40 px above the video bottom
PILL_P, PILL_X, PILL_Y, PILL_PX, PILL_PY = 26, 64, 32, 22, 10

_f = {}


def font(path, px):
    from PIL import ImageFont
    return _f.setdefault((path, px), ImageFont.truetype(path, px))


def width(text, path, px, track=0.0):
    return font(path, px).getlength(text) + track * px * len(text)


def css(path, px, line_top, lh):
    """(libass size, \\pos y) so the text sits where CSS puts it in a line box of height lh starting at line_top."""
    f = font(path, 1000)
    asc, desc = (m / 1000 for m in f.getmetrics())
    l, t, r, b = f.getbbox("H")
    base = line_top + (lh - (asc + desc) * px) / 2 + asc * px
    S = px / EMK[path]
    return round(S, 2), round(base - (b - t) / 1000 * px - TOPOFF[path] * S / 100, 1)


def plain(ws):
    return re.sub(r"\*", "", " ".join(ws))


def wrap_headline(head):
    """Lines of words like CSS text-wrap: balance (same line count as greedy, narrowest widest line). `|` forces breaks."""
    words = head.upper().replace("|", " | ").split()
    if "|" in words:
        return [l.split() for l in " ".join(words).split(" | ")]
    wd = lambda ws: width(plain(ws), ANTON, HEAD_P) + 20 * ("*" in " ".join(ws))
    n, cur = 1, []
    for w in words:                     # greedy line count
        if cur and wd(cur + [w]) > HEAD_W:
            n, cur = n + 1, [w]
        else:
            cur.append(w)

    def best(ws, k):
        if k == 1:
            return (wd(ws), [ws])
        return min(((max(wd(ws[:i]), m), [ws[:i]] + ls) for i in range(1, len(ws) - k + 2)
                    for m, ls in [best(ws[i:], k - 1)]), key=lambda x: x[0])
    lines = best(words, n)[1]
    if len(lines) > 3:
        print(f"ojo: titular en {len(lines)} líneas (máx. 3): {head}", flush=True)
    return lines


def pill_path(x, y, w, h):
    r, k = h / 2, h / 2 * 0.5523
    x1, y1 = x + w, y + h
    p = lambda *v: " ".join(str(round(a, 1)) for a in v)
    return (f"m {p(x + r, y)} l {p(x1 - r, y)} b {p(x1 - r + k, y, x1, y + r - k, x1, y + r)} "
            f"b {p(x1, y + r + k, x1 - r + k, y1, x1 - r, y1)} l {p(x + r, y1)} "
            f"b {p(x + r - k, y1, x, y + r + k, x, y + r)} b {p(x, y + r - k, x + r - k, y, x + r, y)}")


def rect(x0, y0, x1, y1):
    return f"m {x0:.0f} {y0:.0f} l {x1:.0f} {y0:.0f} l {x1:.0f} {y1:.0f} l {x0:.0f} {y1:.0f}"


def chunks(ws):
    """Caption blocks: up to 2 lines of <=3 words that fit SUB_W, <=2 s on screen; break on punctuation and pauses."""
    fits = lambda line: len(line) <= 3 and width(" ".join(t0.clean(x["w"]) for x in line), ARCH9, SUB_P, -0.02) <= SUB_W
    out, lines = [], [[]]
    for i, w in enumerate(ws):
        if lines[-1] and not fits(lines[-1] + [w]):
            if len(lines) == 2:
                out.append(lines); lines = [[]]
            else:
                lines.append([])
        lines[-1].append(w)
        nxt = ws[i + 1] if i + 1 < len(ws) else None
        if (nxt is None or re.search(r"[.,;:?!]$", w["w"]) or nxt["s"] - w["e"] > 0.45
                or nxt["e"] - lines[0][0]["s"] > 2.0):
            out.append(lines); lines = [[]]
    return [c for c in out if c[0]]


def keyword(block, keys):
    """Lime word(s) for a caption block: clips.json "keywords" if any match, else the longest word >= 6 letters."""
    flat = [w for l in block for w in l]
    hit = [w for w in flat if t0.norm(w["w"]) in keys]
    if hit or keys:
        return hit[:2]
    # ponytail: longest-word heuristic; list "keywords" per clip in clips.json to pick them by hand
    lw = max(flat, key=lambda w: len(t0.norm(w["w"])))
    return [lw] if len(t0.norm(lw["w"])) >= 6 else []


HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Box,Archivo,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Head,Anton,100,&H000C0D0D,&H000C0D0D,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Name,Archivo,28,&H000C0D0D,&H000C0D0D,&H00000000,&H00000000,800,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Cap,Archivo Black,113,&H00FFFFFF,&H00FFFFFF,&H000C0D0D,&H00000000,0,0,0,0,100,100,0,0,1,6,0,8,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def layout(clip):
    lines = wrap_headline(clip["headline"])
    return lines, HEAD_Y + len(lines) * HEAD_LH + GAP   # video top


def ass(clip):
    ws, dur = words_for(clip)
    lines, vtop = layout(clip)
    ev = []
    D = lambda s, e, st, tags, txt, layer=1: ev.append(f"Dialogue: {layer},{ts(s)},{ts(e)},{st},,0,0,0,,{{{tags}}}{txt}")

    # headline: runs of plain / *highlighted* text; highlight = lime band 12%-92% of the content box, 10 px padding
    f = font(ANTON, 1000)
    asc, desc = (m / 1000 * HEAD_P for m in f.getmetrics())
    hl = False
    for i, ln in enumerate(lines):
        top = HEAD_Y + i * HEAD_LH
        S, y = css(ANTON, HEAD_P, top, HEAD_LH)
        ctop = top + (HEAD_LH - asc - desc) / 2
        x = HEAD_X
        for part in re.split(r"(\*)", " ".join(ln)):   # `hl` carries over lines: each fragment gets its own padding (clone)
            if part == "*":
                hl = not hl
                continue
            sp = width(" ", ANTON, HEAD_P)
            x += sp * (len(part) - len(part.lstrip()))
            txt = part.strip()
            if not txt:
                continue
            pad = 10 if hl else 0
            wpart = width(txt, ANTON, HEAD_P)
            if hl:
                D(0, dur, "Box", rf"\an7\pos(0,0)\p1\1c{LIME}", rect(x, ctop + 0.12 * (asc + desc), x + wpart + 2 * pad, ctop + 0.92 * (asc + desc)) + r"{\p0}", 0)
            D(0, dur, "Head", rf"\an7\pos({x + pad:.1f},{y})\fs{S}", txt)
            x += wpart + 2 * pad + sp * (len(part) - len(part.rstrip()))

    # name pill per segment, top-left of the video
    S, _ = css(ARCH8, PILL_P, 0, 0)
    asc8, desc8 = (m / 1000 * PILL_P for m in font(ARCH8, 1000).getmetrics())
    off = 0.0
    for s in t0.segs(clip):
        tag = s["tag"]
        py, ph = vtop + PILL_Y, asc8 + desc8 + 2 * PILL_PY
        pw = width(tag, ARCH8, PILL_P) + 2 * PILL_PX
        a, b = off, off + s["to"] - s["from"]
        D(a, b, "Box", rf"\an7\pos(0,0)\p1\1c{LIME}", pill_path(PILL_X, py, pw, ph) + r"{\p0}", 0)
        _, ty = css(ARCH8, PILL_P, py + PILL_PY, asc8 + desc8)
        D(a, b, "Name", rf"\an7\pos({PILL_X + PILL_PX},{ty})\fs{S}\b800", tag)
        off = b

    # captions: whole block at once, keyword(s) in lime, bottom line 40 px above the video bottom
    keys = {t0.norm(k) for k in clip.get("keywords", []) + CFG.get("keywords", [])}
    vb = vtop + VH
    cs = chunks(ws)
    for ci, c in enumerate(cs):
        flat = [w for l in c for w in l]
        s = flat[0]["s"]
        e = min(cs[ci + 1][0][0]["s"], flat[-1]["e"] + 0.6) if ci + 1 < len(cs) else min(dur, flat[-1]["e"] + 0.8)
        em = keyword(c, keys)
        for li, line in enumerate(c):
            txt = " ".join((rf"{{\1c{LIME}}}" + t0.clean(x["w"]) + rf"{{\1c{WHITE}}}") if x in em else t0.clean(x["w"]) for x in line)
            S, y = css(ARCH9, SUB_P, vb - SUB_BOTTOM - (len(c) - li) * SUB_LH, SUB_LH)
            D(s, e, "Cap", rf"\an8\pos({SUB_CX},{y})\fs{S}\fsp{-0.02 * SUB_P:.2f}", txt, 2)
    os.makedirs("subs", exist_ok=True)
    open(f"subs/{clip['name']}.ass", "w", encoding="utf-8-sig").write(HEAD + "\n".join(ev) + "\n")
    return vtop


def subs(clip):
    vtop = ass(clip)
    fonts = os.path.relpath(FONTS).replace("\\", "/")   # relative: libass filter args choke on "C:"
    os.makedirs("final", exist_ok=True)
    fc = (f"color=c={PAPER}:s={W}x{H}:r=30[bg];[0:v]crop={VW}:{VH}:0:{CUT_TOP}[v];[bg][v]overlay=0:{vtop}:shortest=1,"
          f"subtitles=subs/{clip['name']}.ass:fontsdir={fonts}")
    run(["ffmpeg", "-y", "-v", "error", "-i", f"cortes/{clip['name']}.mp4", "-filter_complex", fc,
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"final/{clip['name']}.mp4"])
    print("subs", clip["name"], flush=True)


if __name__ == "__main__":
    cmd, names = sys.argv[1], sys.argv[2:]
    pick = [c for c in CFG["clips"] if not names or c["name"] in names]
    if cmd in ("transcribe", "faces"):
        getattr(t0, cmd)(pick)
    else:
        with ThreadPoolExecutor(3) as ex:
            list(ex.map({"cut": t0.cut, "subs": subs, "ass": ass}[cmd], pick))
