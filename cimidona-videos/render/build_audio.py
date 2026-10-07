"""Build the voiceover timeline, word timings, music bed and final audio mix.

python3 build_audio.py <project_dir> <video_id> <work_dir>
Writes <work_dir>/timing.json and <work_dir>/mix.wav
"""
import json, os, subprocess, sys, urllib.request
import numpy as np

proj, vid, work = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(work, exist_ok=True)
S = json.load(open(f"{proj}/scripts.json", encoding="utf-8"))
J = json.load(open(f"{proj}/jobs.json", encoding="utf-8"))
V = S["videos"][vid]
cfg = V.get("timeline", {})
SR = 44100
vnum = int(vid[1:])
TEMPO = cfg.get("tempo", S.get("tempo", 1.1))


def sh(*a):
    subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def load_wav(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", f"atempo={TEMPO}", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def trim(x, thr_db=-42, pad=0.03):
    thr = 10 ** (thr_db / 20)
    win = int(0.01 * SR)
    env = np.sqrt(np.convolve(x * x, np.ones(win) / win, mode="same"))
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(x), idx[-1] + int(pad * SR))
    return x[a:b]


# ---- download + trim each line ------------------------------------------
clips = []
for i, ln in enumerate(V["lines"]):
    key = ln.get("audio", str(vnum * 100 + i))
    fn = J["audio"][key]
    local = f"{work}/l{i:02d}.wav"
    if not os.path.exists(local):
        urllib.request.urlretrieve(J["audio_base"] + fn, local)
    x = trim(load_wav(local))
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.89
    clips.append(x)

# ---- word timings via faster-whisper + char interpolation ----------------
from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8", download_root="/opt/whisper-models")


def word_times(x, words):
    tmp = f"{work}/_w.wav"
    import wave
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    dur = len(x) / SR
    segs, _ = model.transcribe(tmp, word_timestamps=True, language="ar")
    ww = [w for s in segs for w in (s.words or [])]
    lens = [max(1, len(w)) for w in words]
    tot = sum(lens)
    fr = np.concatenate([[0], np.cumsum(lens)]) / tot  # script char fractions at word boundaries
    if len(ww) >= 1:
        wl = [max(1, len(w.word.strip())) for w in ww]
        wf = np.concatenate([[0], np.cumsum(wl)]) / sum(wl)
        wt = [ww[0].start] + [w.start for w in ww[1:]] + [ww[-1].end]
        wt = np.clip(np.array(wt, dtype=float), 0, dur)
        wt = np.maximum.accumulate(wt)
        f = lambda q: float(np.interp(q, wf, wt))
    else:
        f = lambda q: q * dur
    out = []
    for k in range(len(words)):
        out.append((f(fr[k]), f(fr[k + 1])))
    return out


lead = cfg.get("lead", 0.5)
tail = cfg.get("tail", 3.0)
gaps = {int(k): v for k, v in cfg.get("gaps", {}).items()}
gap_default = cfg.get("gap", 0.3)

lines = []
cur = lead
for i, (ln, x) in enumerate(zip(V["lines"], clips)):
    words = ln["text"].split()
    wts = word_times(x, words)
    dur = len(x) / SR
    hl = set(ln.get("hl", []))
    lines.append({
        "i": i, "text": ln["text"], "start": round(cur, 3), "end": round(cur + dur, 3),
        "words": [{"w": w, "s": round(cur + a, 3), "e": round(cur + b, 3), "hl": w in hl} for w, (a, b) in zip(words, wts)],
    })
    cur += dur + (gaps.get(i, gap_default) if i < len(V["lines"]) - 1 else 0)
total = round(cur + tail, 3)
timing = {"video": vid, "total": total, "lines": lines}
json.dump(timing, open(f"{work}/timing.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- voice track ----------------------------------------------------------
N = int(total * SR) + SR
vo = np.zeros(N, dtype=np.float32)
for ln, x in zip(lines, clips):
    a = int(ln["start"] * SR)
    vo[a:a + len(x)] += x

# ---- music bed (synthesised) -----------------------------------------------
style = cfg.get("music", "soft")
rnd = np.random.default_rng(7)
t = np.arange(N) / SR


def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


progs = {
    "neon":  [[45, 57, 60, 64, 67], [41, 53, 57, 60, 64], [48, 55, 60, 64, 67], [43, 55, 59, 62, 67]],
    "soft":  [[53, 60, 64, 69, 72], [48, 55, 64, 67, 71], [45, 57, 60, 64, 67], [43, 55, 62, 65, 71]],
    "story": [[50, 57, 62, 65, 69], [46, 53, 58, 62, 65], [41, 53, 57, 60, 65], [48, 55, 60, 64, 67]],
}
bpm = {"neon": 100, "soft": 84, "story": 72}[style]
beat = 60 / bpm
bar = beat * 4
prog = progs[style]
pad = np.zeros(N, dtype=np.float32)
pl = np.zeros(N, dtype=np.float32)
nb = int(total / bar) + 2
for b in range(nb):
    ch = prog[b % len(prog)]
    a = int(b * bar * SR)
    L = int((bar + 1.2) * SR)
    if a >= N:
        break
    seg = np.arange(min(L, N - a)) / SR
    envp = np.minimum(1, seg / 0.9) * np.clip((bar + 1.2 - seg) / 1.2, 0, 1)
    s = np.zeros_like(seg)
    for m in ch[1:]:
        f = note(m)
        for det in (-0.0015, 0.0015):
            s += np.sin(2 * np.pi * f * (1 + det) * seg) + 0.25 * np.sin(4 * np.pi * f * (1 + det) * seg)
    s += 0.8 * np.sin(2 * np.pi * note(ch[0]) * seg)
    pad[a:a + len(seg)] += (s * envp * 0.05).astype(np.float32)
    # arpeggio plucks on 8ths
    arp = ch[1:] + [ch[2] + 12]
    for k in range(8):
        st = a + int(k * beat / 2 * SR)
        if st >= N:
            break
        m = arp[(k * 3 + b) % len(arp)] + 12
        ln_ = min(int(0.9 * SR), N - st)
        sg = np.arange(ln_) / SR
        f = note(m)
        tone = (np.sin(2 * np.pi * f * sg) + 0.3 * np.sin(4 * np.pi * f * sg)) * np.exp(-sg * 5.5)
        tone *= np.minimum(1, sg / 0.004)
        vel = 0.05 if k % 2 == 0 else 0.032
        pl[st:st + ln_] += (tone * vel).astype(np.float32)
    if style == "neon":
        for k in range(4):
            st = a + int(k * beat * SR)
            if st >= N:
                break
            ln_ = min(int(0.35 * SR), N - st)
            sg = np.arange(ln_) / SR
            f = 50 + 70 * np.exp(-sg * 30)
            ph = 2 * np.pi * np.cumsum(f) / SR
            pl[st:st + ln_] += (np.sin(ph) * np.exp(-sg * 9) * 0.22).astype(np.float32)
            # soft hat on off-beat
            st2 = st + int(beat / 2 * SR)
            if st2 < N:
                hl_ = min(int(0.05 * SR), N - st2)
                hn = rnd.standard_normal(hl_) * np.exp(-np.arange(hl_) / SR * 80)
                hn = np.diff(np.concatenate([[0], hn]))
                pl[st2:st2 + hl_] += (hn * 0.02).astype(np.float32)

music = pad + pl
# gentle fade in/out
fade = np.ones(N, dtype=np.float32)
fi = int(1.0 * SR); fo = int(2.5 * SR); endn = int(total * SR)
fade[:fi] = np.linspace(0, 1, fi)
fade[endn - fo:endn] = np.linspace(1, 0, fo)
fade[endn:] = 0
music *= fade

# ---- sfx ----------------------------------------------------------------
sfx = np.zeros(N, dtype=np.float32)


def whoosh(at, dur=0.7, gain=0.16):
    a = int(max(0, at - dur * 0.6) * SR)
    n = min(int(dur * SR), N - a)
    if n <= 0:
        return
    sg = np.arange(n) / n
    w = rnd.standard_normal(n).astype(np.float32)
    # crude band-limiting: moving average with sweeping width
    out = np.zeros(n, dtype=np.float32)
    k1 = np.cumsum(np.concatenate([[0], w]))
    width = (40 - 34 * np.sin(np.pi * sg)).astype(int)
    idx = np.arange(n)
    lo = np.clip(idx - width, 0, n)
    out = (k1[idx + 1] - k1[lo]) / np.maximum(1, idx + 1 - lo)
    envw = np.sin(np.pi * sg) ** 2
    sfx[a:a + n] += (out * envw * gain * 6).astype(np.float32)


def pop(at, gain=0.25):
    a = int(at * SR)
    n = min(int(0.25 * SR), N - a)
    sg = np.arange(n) / SR
    f = 900 * np.exp(-sg * 18) + 180
    ph = 2 * np.pi * np.cumsum(f) / SR
    sfx[a:a + n] += (np.sin(ph) * np.exp(-sg * 22) * gain).astype(np.float32)


def chime(at, gain=0.12):
    a = int(at * SR)
    n = min(int(2.2 * SR), N - a)
    sg = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * sg) * np.exp(-sg * d) for f, d in ((1318.5, 2.2), (1975.5, 3.0), (2637, 4.0)))
    sfx[a:a + n] += (s * gain / 2).astype(np.float32)


for i in cfg.get("whoosh", []):
    whoosh(lines[i]["start"] - 0.05)
for i in cfg.get("pop", []):
    pop(lines[i]["start"] + 0.05)
for at in cfg.get("whoosh_at", []):
    whoosh(at)
if cfg.get("chime_end", True):
    chime(lines[-1]["end"] + 0.25)

# ---- mix with ducking -----------------------------------------------------
win = int(0.05 * SR)
venv = np.sqrt(np.convolve(vo * vo, np.ones(win) / win, mode="same"))
duck = np.clip(venv / 0.06, 0, 1)
# smooth the ducking curve (attack/release)
k = int(0.25 * SR)
duck = np.convolve(duck, np.ones(k) / k, mode="same")
mgain = 0.55 * (1 - 0.6 * np.clip(duck, 0, 1))
mix = vo * 1.0 + music * mgain * cfg.get("music_gain", 1.0) + sfx
mix = mix[:int(total * SR)]
peak = np.max(np.abs(mix))
mix = mix / max(peak, 1e-6) * 0.93
stereo = np.stack([mix, mix], axis=1)
import wave
with wave.open(f"{work}/premix.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(stereo, -1, 1) * 32767).astype(np.int16).tobytes())
# light room reverb on music+sfx is approximated by aecho; loudness normalise for social
sh("ffmpeg", "-y", "-i", f"{work}/premix.wav", "-af",
   "aecho=0.9:0.6:45|90:0.12|0.07,loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", str(SR), f"{work}/mix.wav")
print(json.dumps({"total": total, "lines": [(l["start"], l["end"]) for l in lines]}))
