# Template 1: black header with a red headline box, full-width video fading into a brick-red panel,
# name + date line, big left-aligned Oswald captions (2 lines). Same clips.json/fixes.json as template 0.
#   <hermes python> t1.py transcribe | python t1.py faces | python t1.py cut | python t1.py subs   [clip names...]
# Reuses template0/t0.py for transcribe, faces, cut and caption words (only geometry and design differ).
import os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "template0"))
import t0
from t0 import CFG, W, H, run, ts, words_for

TOP, VH = 352, 774                     # black header 0..352, video 1080x774 below it (fades into the panel)
t0.TOP, t0.VH, t0.DEF_Y, t0.DEF_H, t0.LOWER_THIRD = TOP, VH, 0, 1080, 10**6   # full-height source slice; lower third sits under the fade

# Oswald Bold, tracking -50 (= -0.05 em). Sizes/scale calibrated against the reference mockup (2026-10-01):
# with ScaleY 140 the type came out 18% taller than the mockup, 118 matches it to the pixel.
FONT = os.path.join(HERE, "fonts", "Oswald-Bold.ttf")
EMK, SCY = 0.581, 118                  # em px per libass size unit (measured); vertical scale %
HEAD_S, NAME_S, CAP_S = 121, 86, 146.5
CAP_X, CAP_TOP, CAP_PITCH, CAP_W = 49, 1232, 104, 902      # glyph-ink geometry from the mockup
HEAD_PITCH, HEAD_CAP, BOX_PAD = 85, 70, (29, 28, 23, 16)   # left, right, top, bottom
NAME_TOP, DATE_RIGHT = 1158, 951
TOP_OFF = {HEAD_S: 43, NAME_S: 30, CAP_S: 51}              # ink top below \pos with \an7/\an8 (measured)
RED, YELLOW = "&H2124E3&", "&H3BF1F8&"                     # #E32421, #F8F13B (BGR)
PANEL_FADE, PANEL_DARK, PANEL_RED = (900, 1100), (0x5A, 0x21, 0x15), (0x88, 0x2A, 0x15)


def fsp(S):
    return round(-0.05 * EMK * S, 2)


_fonts = {}


def width(text, S):
    from PIL import ImageFont
    f = _fonts.setdefault(S, ImageFont.truetype(FONT, size=round(S * EMK * 4)))
    l, _, r, _ = f.getbbox(text)
    return (r - l) / 4 + (len(text) - 1) * fsp(S)


def wrap_headline(head, S=HEAD_S, maxw=900):
    words = head.replace("|", " | ").split()
    plain = lambda ws: re.sub(r"\*", "", " ".join(ws))
    if "|" in words:                   # manual breaks
        lines, cur = [], []
        for w in words + ["|"]:
            if w == "|":
                lines.append(cur); cur = []
            else:
                cur.append(w)
        return lines
    if width(plain(words), S) <= maxw:
        return [words]
    splits = [(max(width(plain(words[:i]), S), width(plain(words[i:]), S)), i) for i in range(1, len(words))]
    best = min(splits)[0]   # among near-ties prefer the longer top line (pyramid), like the mockup
    i = max((width(plain(words[:i]), S), i) for m, i in splits if m <= best * 1.05)[1]
    if best <= maxw:
        return [words[:i], words[i:]]
    n = len(words)          # 3 lines: narrowest split, near-ties go to the widest top line
    three = [(max(width(plain(p), S) for p in (words[:i], words[i:j], words[j:])), i, j) for i in range(1, n - 1) for j in range(i + 1, n)]
    best = min(three)[0]
    i, j = max((width(plain(words[:i]), S), i, j) for m, i, j in three if m <= best * 1.05)[1:]
    return [words[:i], words[i:j], words[j:]]


def chunks(ws):
    """Caption blocks of up to 2 lines that fit CAP_W; break on punctuation and pauses."""
    out, lines = [], [[]]
    for i, w in enumerate(ws):
        txt = " ".join(t0.clean(x["w"]) for x in lines[-1] + [w])
        if lines[-1] and width(txt, CAP_S) > CAP_W * 0.98:
            if len(lines) == 2:
                out.append(lines); lines = [[]]
            else:
                lines.append([])
        lines[-1].append(w)
        nxt = ws[i + 1] if i + 1 < len(ws) else None
        if nxt is None or re.search(r"[.,;:?!]$", w["w"]) or nxt["s"] - w["e"] > 0.45:
            out.append(lines); lines = [[]]
    return [c for c in out if c[0]]


HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Box,Oswald,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Head,Oswald,{HEAD_S},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,{SCY},0,0,1,5,2,8,0,0,0,1
Style: Name,Oswald,{NAME_S},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,{SCY},0,0,1,0,0,7,0,0,0,1
Style: Cap,Oswald,{CAP_S},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,{SCY},0,0,1,3,2,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def headline(D, head, dur, S=HEAD_S, cy=200, maxw=900):
    """Red box sized to the measured lines, centred at (540, cy). Geometry scales with S from the mockup's 121."""
    k = S / HEAD_S
    lines = wrap_headline(head.upper(), S, maxw)
    plain = [re.sub(r"\*", "", " ".join(l)) for l in lines]
    mw = max(width(p, S) for p in plain)
    block = (HEAD_CAP + (len(lines) - 1) * HEAD_PITCH) * k
    l, r, t, b = (p * k for p in BOX_PAD)
    top1 = cy - (block + t + b) / 2 + t
    x0, x1, y0, y1 = round(540 - mw / 2 - l), round(540 + mw / 2 + r), round(top1 - t), round(top1 + block + b)
    D(0, dur, "Box", rf"\an7\pos(0,0)\p1\1c{RED}", f"m {x0} {y0} l {x1} {y0} l {x1} {y1} l {x0} {y1}{{\\p0}}", 0)
    for i, ln in enumerate(lines):
        txt = re.sub(r"\*(.+?)\*", lambda m: rf"{{\1c{YELLOW}}}" + m.group(1) + r"{\1c&HFFFFFF&}", " ".join(ln))
        y = round(top1 + i * HEAD_PITCH * k - TOP_OFF.get(S, S * TOP_OFF[HEAD_S] / HEAD_S))
        D(0, dur, "Head", rf"\an8\pos(540,{y})\fs{S}\bord{5 * k:.1f}\fsp{fsp(S)}", txt)


def ass(clip):
    ws, dur = words_for(clip)
    ev = []
    D = lambda s, e, st, tags, txt, layer=1: ev.append(f"Dialogue: {layer},{ts(s)},{ts(e)},{st},,0,0,0,,{{{tags}}}{txt}")
    headline(D, clip["headline"], dur)   # in the black header
    # name (per segment) + date
    off = 0.0
    for s in t0.segs(clip):
        D(off, off + s["to"] - s["from"], "Name", rf"\an7\pos({47 - 3},{NAME_TOP - TOP_OFF[NAME_S]})\fsp{fsp(NAME_S)}", s["tag"].upper())
        off += s["to"] - s["from"]
    if CFG.get("date"):
        D(0, dur, "Name", rf"\an9\pos({DATE_RIGHT + 3},{NAME_TOP - TOP_OFF[NAME_S]})\fsp{fsp(NAME_S)}", CFG["date"])
    # captions: block of <=2 lines, current word yellow
    cs = chunks(ws)
    for ci, c in enumerate(cs):
        flat = [w for line in c for w in line]
        end = min(cs[ci + 1][0][0]["s"], flat[-1]["e"] + 0.6) if ci + 1 < len(cs) else min(dur, flat[-1]["e"] + 0.8)
        for k, w in enumerate(flat):
            s = flat[0]["s"] if k == 0 else w["s"]
            e = end if k == len(flat) - 1 else flat[k + 1]["s"]
            if e - s < 0.02:
                continue
            for li, line in enumerate(c):
                txt = " ".join((rf"{{\1c{YELLOW}}}" if x is w else "") + t0.clean(x["w"]) + (r"{\1c&HFFFFFF&}" if x is w else "") for x in line)
                D(s, e, "Cap", rf"\an7\pos({CAP_X - 5},{CAP_TOP + li * CAP_PITCH - TOP_OFF[CAP_S]})\fsp{fsp(CAP_S)}", txt)
    os.makedirs("subs", exist_ok=True)
    open(f"subs/{clip['name']}.ass", "w", encoding="utf-8-sig").write(HEAD + "\n".join(ev) + "\n")


def panel(top=TOP, fade=PANEL_FADE, out="panel.png"):
    """Overlay: black header, video fades into dark red, then brick-red panel."""
    import numpy as np, cv2
    y = np.arange(H, dtype=float)[:, None]
    f0, f1 = fade
    a = np.clip((y - f0) / (f1 - f0), 0, 1); a = a * a * (3 - 2 * a)
    g = np.clip((y - f1) / 140, 0, 1)
    rgb = (1 - g) * np.array(PANEL_DARK) + g * np.array(PANEL_RED)
    alpha = np.where(y < top, 1, a)
    rgb = np.where(y < top, 0, rgb)
    img = np.repeat(np.concatenate([rgb[:, ::-1], alpha * 255], axis=1)[:, None, :], W, axis=1)
    cv2.imwrite(out, img.round().astype(np.uint8))


# ---------------------------------------------------------------- thumbnail (TikTok cover)
# TikTok's profile grid crops covers to 3:4 = y 240..1680, so face + headline live in that band.
TH_TOP, TH_FADE, TH_S, TH_CY = 240, (1000, 1130), 180, 1400   # video y 240..1126, headline centre in the panel
TH_SRC_H = 820                         # source slice height: stops above the channel lower third (~835), so the face comes out bigger


def best_frame(clip):
    """(YouTube second, face x in 1920 px). clip["thumb"] (YouTube seconds) overrides the pick."""
    import cv2, numpy as np
    seg = t0.segs(clip)
    if "thumb" in clip:
        return clip["thumb"], next((s.get("x", 960) for s in seg if s["from"] <= clip["thumb"] <= s["to"]), seg[0].get("x", 960))
    face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    eye = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
    best = (-1, seg[0]["from"] + 1, seg[0].get("x", 960))
    for s in seg:
        v, o = t0.vsrc(s["from"])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(s["from"] - o), "-to", str(s["to"] - o), "-i", v,
                              "-vf", "fps=4,scale=960:540,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
        for k, f in enumerate(np.frombuffer(raw, np.uint8).reshape(-1, 540, 960)):
            d = face.detectMultiScale(f, 1.1, 5, minSize=(60, 60))
            if not len(d):
                continue
            x, y, w, h = max(d, key=lambda r: r[2])
            roi = f[y:y + h, x:x + w]
            if len(eye.detectMultiScale(roi[: h // 2], 1.1, 4)) < 2:   # skip blinks / looking down
                continue
            # ponytail: size x sharpness, no expression scoring; set "thumb" in clips.json to choose by hand
            score = w * cv2.Laplacian(roi, cv2.CV_64F).var()
            if score > best[0]:
                best = (score, s["from"] + k / 4, int((x + w / 2) * 2))
    return best[1], best[2]


def thumb(clip):
    t, fx = best_frame(clip)
    ev = []
    D = lambda s, e, st, tags, txt, layer=1: ev.append(f"Dialogue: {layer},{ts(s)},{ts(e)},{st},,0,0,0,,{{{tags}}}{txt}")
    headline(D, clip["headline"], 5, TH_S, TH_CY, 980)
    name_top = (TH_TOP - HEAD_CAP * NAME_S / HEAD_S) / 2          # name + date centred in the black band
    tag = next(s["tag"] for s in t0.segs(clip) if s["from"] <= t <= s["to"]) if any(s["from"] <= t <= s["to"] for s in t0.segs(clip)) else clip["segments"][-1]["tag"]
    D(0, 5, "Name", rf"\an7\pos({47 - 3},{round(name_top - TOP_OFF[NAME_S])})\fsp{fsp(NAME_S)}", tag.upper())
    if CFG.get("date"):
        D(0, 5, "Name", rf"\an9\pos({DATE_RIGHT + 3},{round(name_top - TOP_OFF[NAME_S])})\fsp{fsp(NAME_S)}", CFG["date"])
    os.makedirs("subs", exist_ok=True); os.makedirs("miniaturas", exist_ok=True)
    open(f"subs/{clip['name']}_thumb.ass", "w", encoding="utf-8-sig").write(HEAD + "\n".join(ev) + "\n")
    vh = 1126 - TH_TOP
    cw = round(TH_SRC_H * W / vh / 2) * 2                        # slice above the lower third, width to fill 1080 x vh
    x = min(max(fx - cw // 2, 0), 1920 - cw)
    v, o = t0.vsrc(t)
    fonts = os.path.relpath(os.path.join(HERE, "fonts")).replace("\\", "/")
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(t - o), "-i", v, "-i", "panel_thumb.png", "-frames:v", "1", "-filter_complex",
         f"[0:v]crop={cw}:{TH_SRC_H}:{x}:0,scale={W}:{vh}:flags=lanczos,unsharp=5:5:0.5,pad={W}:{H}:0:{TH_TOP}:black[b];"
         f"[b][1:v]overlay,subtitles=subs/{clip['name']}_thumb.ass:fontsdir={fonts}", f"miniaturas/{clip['name']}.png"])
    print("thumb", clip["name"], f"t={t:.2f}", flush=True)


def subs(clip):
    ass(clip)
    fonts = os.path.relpath(os.path.join(HERE, "fonts")).replace("\\", "/")   # relative: libass filter args choke on "C:"
    os.makedirs("final", exist_ok=True)
    fc = f"[0:v][1:v]overlay,subtitles=subs/{clip['name']}.ass:fontsdir={fonts}"
    cover = f"miniaturas/{clip['name']}.png"   # if `thumb` ran first, frame 0 becomes the thumbnail = TikTok's default cover
    extra = ["-i", cover] if os.path.exists(cover) else []
    if extra:
        fc += "[v];[v][2:v]overlay=enable='eq(n\\,0)'"
    run(["ffmpeg", "-y", "-v", "error", "-i", f"cortes/{clip['name']}.mp4", "-i", "panel.png", *extra,
         "-filter_complex", fc,
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
        if cmd == "subs":
            panel()
        if cmd == "thumb":
            panel(TH_TOP, TH_FADE, "panel_thumb.png")
        with ThreadPoolExecutor(3) as ex:
            list(ex.map({"cut": t0.cut, "subs": subs, "ass": ass, "thumb": thumb}[cmd], pick))
