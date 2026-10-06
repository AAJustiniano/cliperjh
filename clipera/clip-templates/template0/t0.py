# Template 0: TikTok clips (black header + 0.77 vertical video + Montserrat Bold word captions).
# Run from a project folder that has clips.json (see README.md / example/):
#   <hermes python> t0.py transcribe   whisper large-v3-turbo per segment -> transcript/<clip>_<i>.json
#   python t0.py faces                 fills missing segment "x" (face center) in clips.json
#   python t0.py cut                   -> cortes/<clip>.mp4 (no text)
#   python t0.py subs                  -> final/<clip>.mp4 (headline, captions, loudness -14 LUFS)
# Optional clip names after the command limit the run.
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, TOP = 1080, 1920, 520            # black header 0..520, video 1080x1400 below it
VH = H - TOP                           # video height (other templates override TOP/VH/DEF_*)
DEF_Y, DEF_H = 60, 730                 # default source slice: top y, height (width follows 1080:1400)
CFG = json.load(open("clips.json", encoding="utf-8"))
VIDEO, AUDIO = CFG.get("video", "src/video.mp4"), CFG.get("audio", "src/audio.m4a")
LOWER_THIRD = CFG.get("lower_third_y", 835)   # source y where the channel's lower third starts; slices stay above it
# Video bajado por tramos: [{"file": "src/tramo1.mp4", "start": 550.0}]. Los tiempos de clips.json siguen siendo los de YouTube.
# ponytail: confía en que el tramo arranca exacto en "start" (yt-dlp --force-keyframes-at-cuts); si hay desfase labial, medir el offset por audio.
TRAMOS = CFG.get("tramos")
FIXES = json.load(open("fixes.json", encoding="utf-8")) if os.path.exists("fixes.json") else []


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit(r.stderr[-3000:])


def vsrc(t):
    """(archivo de video, offset) que contiene el segundo t de YouTube."""
    if not TRAMOS:
        return VIDEO, 0
    tr = max((x for x in TRAMOS if x["start"] <= t), key=lambda x: x["start"])
    return tr["file"], tr["start"]


def segs(clip):
    return [{"y": DEF_Y, "h": DEF_H, **s} for s in clip["segments"]]


# ---------------------------------------------------------------- transcribe / faces
def transcribe(clips):
    from faster_whisper import WhisperModel
    os.makedirs("transcript", exist_ok=True)
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=8)
    for c in clips:
        for i, s in enumerate(segs(c)):
            out = f"transcript/{c['name']}_{i}.json"
            if os.path.exists(out):
                continue
            a, b = max(s["from"] - 1.5, 0), s["to"] + 1.5
            wav = out[:-5] + ".wav"
            run(["ffmpeg", "-y", "-v", "error", "-ss", str(a), "-to", str(b), "-i", AUDIO, "-ac", "1", "-ar", "16000", wav])
            res, _ = m.transcribe(wav, language="es", word_timestamps=True, beam_size=5,
                                  initial_prompt=CFG.get("whisper_prompt"))
            words = [{"w": w.word.strip(), "s": round(a + w.start, 2), "e": round(a + w.end, 2)} for r in res for w in r.words]
            json.dump(words, open(out, "w", encoding="utf-8"), ensure_ascii=False)
            print(out, " ".join(w["w"] for w in words), flush=True)


def faces(clips):
    import cv2, numpy as np   # needs opencv-python-headless<5 (5.x dropped CascadeClassifier)
    cas = [cv2.CascadeClassifier(cv2.data.haarcascades + f) for f in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml")]
    for c in clips:
        for s in c["segments"]:
            if "x" in s:
                continue
            v, o = vsrc(s["from"])
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(s["from"] - o), "-to", str(s["to"] - o), "-i", v,
                                  "-vf", "fps=2,scale=480:270,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
            xs = []
            for f in np.frombuffer(raw, np.uint8).reshape(-1, 270, 480):
                d = [r for k in cas for r in k.detectMultiScale(f, 1.1, 5, minSize=(40, 40))]
                d += [(480 - x - w, y, w, h) for x, y, w, h in cas[1].detectMultiScale(cv2.flip(f, 1), 1.1, 5, minSize=(40, 40))]
                if d:
                    x, _, w, _ = max(d, key=lambda r: r[2])
                    xs.append((x + w / 2) * 4)
            s["x"] = int(np.median(xs)) if xs else 960
            print(c["name"], s["from"], f"x={s['x']}", f"({len(xs)} detections)", flush=True)
    json.dump(CFG, open("clips.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- cut
def cut(clip):
    args, chains = [], []
    for i, s in enumerate(segs(clip)):
        a, b, y, ch = s["from"], s["to"], s["y"], s["h"]
        assert y + ch < LOWER_THIRD, f"{clip['name']}: slice bottom {y + ch} reaches the lower third"
        cw = round(ch * W / VH / 2) * 2
        x = min(max(s.get("x", 960) - cw // 2, 0), 1920 - cw)
        v, o = vsrc(a)
        args += ["-ss", str(a - o), "-to", str(b - o), "-i", v, "-ss", str(a), "-to", str(b), "-i", AUDIO]
        chains.append(f"[{2*i}:v]crop={cw}:{ch}:{x}:{y},scale={W}:{VH}:flags=lanczos,unsharp=5:5:0.5,fps=30,setsar=1,setpts=PTS-STARTPTS[v{i}];"
                      f"[{2*i+1}:a]aresample=48000,asetpts=PTS-STARTPTS[a{i}]")
    n = len(chains)
    fc = ";".join(chains) + ";" + "".join(f"[v{i}][a{i}]" for i in range(n)) + \
        f"concat=n={n}:v=1:a=1[vv][aa];[vv]pad={W}:{H}:0:{TOP}:color=black[out]"
    os.makedirs("cortes", exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", *args, "-filter_complex", fc, "-map", "[out]", "-map", "[aa]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"cortes/{clip['name']}.mp4"])
    print("cut", clip["name"], flush=True)


# ---------------------------------------------------------------- captions
def words_for(clip):
    out, off = [], 0.0
    for i, s in enumerate(segs(clip)):
        a, b = s["from"], s["to"]
        for w in json.load(open(f"transcript/{clip['name']}_{i}.json", encoding="utf-8")):
            if a - 0.05 <= (w["s"] + w["e"]) / 2 < b - 0.15 and w["w"]:   # midpoint: whisper edges drift ~0.3 s
                out.append({"w": w["w"], "s": off + max(w["s"], a) - a, "e": off + min(w["e"], b) - a})
        off += b - a
    return apply_fixes(out), off


def norm(t):
    return re.sub(r"[^\wáéíóúñü]", "", t.lower())


def apply_fixes(ws):
    for old, new in FIXES:   # [old words, new words], matched case/punctuation-insensitively
        o, nw = [norm(t) for t in old.split()], new.split()
        i = 0
        while i <= len(ws) - len(o):
            if [norm(w["w"]) for w in ws[i:i + len(o)]] == o:
                s, e = ws[i]["s"], ws[i + len(o) - 1]["e"]
                step = (e - s) / len(nw)
                punct = re.search(r"[.,;:?!]*$", ws[i + len(o) - 1]["w"]).group()
                nw2 = nw[:-1] + [nw[-1] if re.search(r"[.,;:?!]$", nw[-1]) else nw[-1] + punct]
                ws[i:i + len(o)] = [{"w": t, "s": s + k * step, "e": s + (k + 1) * step} for k, t in enumerate(nw2)]
                i += len(nw)
            else:
                i += 1
    return ws


def chunks(ws, max_words=4, max_chars=14):
    out, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        nxt = ws[i + 1] if i + 1 < len(ws) else None
        text = " ".join(x["w"] for x in cur)
        if (nxt is None or len(cur) >= max_words or re.search(r"[.,;:?!]$", w["w"])
                or len(text) + 1 + len(nxt["w"]) > max_chars or nxt["s"] - w["e"] > 0.45):
            out.append(cur)
            cur = []
    return out


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def clean(t):
    return re.sub(r"[.,;:…]+$", "", t).upper()


YEL, WHT = r"{\c&H00E5FF&}", r"{\c&HFFFFFF&}"
HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,5,5,90,90,0,1
Style: Kick,Montserrat Black,58,&H00FFFFFF,&H00FFFFFF,&H001C1CE3,&H001C1CE3,0,0,0,0,100,100,1,0,3,14,0,8,60,60,0,1
Style: Head,Montserrat Black,88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,4,4,8,50,50,0,1
Style: Tag,Montserrat,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,3,10,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ass(clip):
    ws, dur = words_for(clip)
    ev = []
    D = lambda s, e, st, txt, layer=0: ev.append(f"Dialogue: {layer},{ts(s)},{ts(e)},{st},,0,0,0,,{txt}")
    D(0, dur, "Kick", r"{\pos(540,160)\fscx70\fscy70\t(0,160,\fscx100\fscy100)}" + clip["kicker"])
    headtxt = re.sub(r"\*(.+?)\*", lambda m: YEL + m.group(1) + WHT, clip["headline"])
    D(0.12, dur, "Head", r"{\an5\move(540,368,540,350,120,380)\fad(200,0)}" + headtxt)
    off = 0.0
    for s in segs(clip):   # name tag, green box top-left of the video
        D(off, off + s["to"] - s["from"], "Tag", r"{\pos(40," + str(TOP + 26) + r")\3c&H3A9A1F&\4c&H3A9A1F&}" + s["tag"])
        off += s["to"] - s["from"]
    cs = chunks(ws)
    for ci, c in enumerate(cs):
        end = min(cs[ci + 1][0]["s"], c[-1]["e"] + 0.6) if ci + 1 < len(cs) else min(dur, c[-1]["e"] + 0.8)
        for i, w in enumerate(c):
            s = c[0]["s"] if i == 0 else w["s"]
            e = end if i == len(c) - 1 else c[i + 1]["s"]
            if e - s < 0.02:
                continue
            txt = " ".join((YEL if j == i else "") + clean(x["w"]) + (WHT if j == i else "") for j, x in enumerate(c))
            pop = r"\fscx86\fscy86\t(0,110,\fscx100\fscy100)" if s <= c[0]["s"] + 0.02 else ""
            D(s, e, "Cap", r"{\pos(540,1545)" + pop + "}" + txt, 1)
    os.makedirs("subs", exist_ok=True)
    open(f"subs/{clip['name']}.ass", "w", encoding="utf-8-sig").write(HEAD + "\n".join(ev) + "\n")


def subs(clip):
    ass(clip)
    fonts = os.path.relpath(os.path.join(HERE, "fonts")).replace("\\", "/")   # relative: libass filter args choke on "C:"
    os.makedirs("final", exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", f"cortes/{clip['name']}.mp4", "-i", "scrim.png",
         "-filter_complex", f"[0:v][1:v]overlay,subtitles=subs/{clip['name']}.ass:fontsdir={fonts}",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"final/{clip['name']}.mp4"])
    print("subs", clip["name"], flush=True)


def scrim():
    # bottom ramp 1300..1920 (0 -> 0.7) behind captions + TikTok UI
    a = "if(gt(Y,1300),180*pow((Y-1300)/620,0.8),0)"
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=black:s={W}x{H}:d=1,format=rgba",
         "-vf", f"geq=r=0:g=0:b=0:a='{a}'", "-frames:v", "1", "scrim.png"])


if __name__ == "__main__":
    cmd, names = sys.argv[1], sys.argv[2:]
    pick = [c for c in CFG["clips"] if not names or c["name"] in names]
    if cmd in ("transcribe", "faces"):
        {"transcribe": transcribe, "faces": faces}[cmd](pick)
    else:
        if cmd == "subs":
            scrim()
        with ThreadPoolExecutor(3) as ex:
            list(ex.map({"cut": cut, "subs": subs, "ass": ass}[cmd], pick))
