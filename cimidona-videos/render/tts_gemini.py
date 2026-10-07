"""Saudi-dialect voiceover via Google AI Studio (Gemini API TTS), one clip per script line.

python3 tts_gemini.py <project_dir> [v1 v2 ...]     (GEMINI_API_KEY or network secret)

Each take is transcribed back by a Gemini text model; takes whose transcript drifts
from the script are regenerated (up to MAX_TRIES). Output: <project>/audio/<vid>/lNN.wav
"""
import base64, difflib, json, os, re, subprocess, sys, time, urllib.error, urllib.request

proj = sys.argv[1]
only = sys.argv[2:] or None
# Key comes from GEMINI_API_KEY, or (preferred) a cloud-environment network secret that the
# agent proxy attaches as the x-goog-api-key header for generativelanguage.googleapis.com.
KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
HDR = {}
QS = f"?key={KEY}" if KEY else ""  # query-param auth (a Bearer-prefixed header secret is rejected by Google)
API = "https://generativelanguage.googleapis.com/v1beta"
S = json.load(open(f"{proj}/scripts.json", encoding="utf-8"))
G = S.get("gemini_tts", {})
VOICE = G.get("voice", "Leda")
MAX_TRIES = G.get("max_tries", 4)
STYLE = G.get("style", (
    "Read the Arabic line below aloud exactly as written, in a natural Saudi Arabic dialect "
    "(Riyadh/Najdi, khaleeji), as a warm, sincere Saudi woman in her forties speaking to a friend in a social-media ad. "
    "Native Saudi pronunciation, natural rhythm, clear articulation, no Modern Standard Arabic newsreader tone. "
    "Speak only the Arabic line, nothing else."))


def post(model, body, tries=6):
    url = f"{API}/models/{model}:generateContent{QS}"
    data = json.dumps(body).encode()
    for k in range(tries):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **HDR})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code in (429, 500, 503) and k < tries - 1:
                time.sleep(min(60, 5 * 2 ** k)); continue
            raise SystemExit(f"{model} HTTP {e.code}: {msg}")
        except Exception:
            if k < tries - 1:
                time.sleep(5 * 2 ** k); continue
            raise


def pick_models():
    with urllib.request.urlopen(urllib.request.Request(f"{API}/models?pageSize=200" + QS.replace("?", "&"), headers=HDR)) as r:
        names = [m["name"].split("/")[-1] for m in json.load(r)["models"]]
    tts = [n for n in names if "tts" in n]
    pref = G.get("tts_model")
    tts_model = pref if pref in names else next((n for n in sorted(tts, reverse=True) if "pro" in n), None) or sorted(tts)[-1]
    text = [n for n in names if n.startswith("gemini") and "tts" not in n and "image" not in n and "live" not in n and "embedding" not in n]
    qa_model = G.get("qa_model") if G.get("qa_model") in names else next((n for n in text if "2.5-flash" == n.replace("gemini-", "")), None) or next(n for n in text if "flash" in n)
    return tts_model, qa_model


def tts(model, text, voice=None, style=None):
    body = {"contents": [{"parts": [{"text": f"{style or STYLE}\n\n{text}"}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice or VOICE}}}}}
    r = post(model, body)
    part = r["candidates"][0]["content"]["parts"][0]["inlineData"]
    rate = int(re.search(r"rate=(\d+)", part.get("mimeType", "")).group(1)) if "rate=" in part.get("mimeType", "") else 24000
    return base64.b64decode(part["data"]), rate


def transcribe(model, wav):
    b = base64.b64encode(open(wav, "rb").read()).decode()
    body = {"contents": [{"parts": [
        {"inlineData": {"mimeType": "audio/wav", "data": b}},
        {"text": "Transcribe this Arabic audio exactly, word for word, in Arabic script, without diacritics. "
                 "Then on a new line write DIALECT: followed by the dialect you hear (e.g. Saudi, Egyptian, Levantine, MSA). Output nothing else."}]}],
        "generationConfig": {"temperature": 0}}
    r = post(model, body)
    return "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"]).strip()


def norm(s):
    s = re.sub(r"[ً-ْـ]", "", s)          # diacritics, tatweel
    s = re.sub(r"[أإآ]", "ا", s).replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"[^ء-ي ]", " ", s).split()


def score(script, heard):
    return difflib.SequenceMatcher(None, norm(script), norm(heard)).ratio()



WHOLE_STYLE = (
    "Read the following Arabic voiceover script aloud exactly as written, word for word, in natural Saudi Arabic "
    "(Riyadh/Najdi dialect), as {persona}. Native Saudi pronunciation and rhythm, no Modern Standard Arabic newsreader tone. "
    "Each line is a separate sentence: leave a clear pause of about one second between lines. "
    "Speak only the script lines, nothing else.")


def load_mono(path, sr=24000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"], check=True, capture_output=True).stdout
    import numpy as np
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


def split_lines(x, texts, sr=24000):
    """Cut a whole-script take into lines. Candidate cut points are pauses; dynamic programming picks the
    N-1 pauses whose position (in voiced time) best matches each line boundary's expected position from
    character counts, preferring longer pauses. Robust to mid-line pauses such as after «ثانياً:»."""
    import numpy as np
    hop = int(0.01 * sr)
    e = np.sqrt(np.convolve(x * x, np.ones(hop) / hop, mode="same"))[::hop]
    thr = max(e.max() * 0.03, 3e-4)
    voiced = e >= thr
    cumv = np.concatenate([[0], np.cumsum(voiced)])
    total_v = cumv[-1]
    runs, k = [], 0
    while k < len(voiced):
        if not voiced[k]:
            j = k
            while j < len(voiced) and not voiced[j]: j += 1
            if k > 0 and j < len(voiced) and j - k >= 8:      # pauses >= 80 ms
                runs.append(((k + j) // 2, (j - k) / 100.0))
            k = j
        else:
            k += 1
    n = len(texts)
    if len(runs) < n - 1:
        return None, f"only {len(runs)} pauses for {n} lines"
    ch = np.array([len(t.replace(" ", "")) for t in texts], float)
    F = np.cumsum(ch)[:-1] / ch.sum()                       # expected boundary fractions
    pf = np.array([cumv[m] / total_v for m, _ in runs])     # voiced fraction at each pause
    pl = np.array([L for _, L in runs])
    cost = lambda i, c: ((pf[c] - F[i]) * 10) ** 2 - 1.5 * min(pl[c], 1.2)
    m = len(runs); INF = 1e18
    D = np.full((n - 1, m), INF); P = np.zeros((n - 1, m), int)
    for c in range(m): D[0, c] = cost(0, c)
    for i in range(1, n - 1):
        best, arg = INF, -1
        for c in range(m):
            if c > 0 and D[i - 1, c - 1] < best: best, arg = D[i - 1, c - 1], c - 1
            if arg >= 0: D[i, c] = best + cost(i, c); P[i, c] = arg
    c = int(np.argmin(D[n - 2])); sel = [c]
    for i in range(n - 2, 0, -1):
        c = P[i, c]; sel.append(c)
    sel = sorted(sel)
    bounds = [0] + [runs[c][0] * hop for c in sel] + [len(x)]
    segs = [x[bounds[i]:bounds[i + 1]] for i in range(n)]
    dev = [abs(pf[c] - F[i]) for i, c in enumerate(sel)]
    bad = [i + 1 for i, d in enumerate(dev) if d > 0.06]
    return segs, (f"uncertain boundaries before lines {bad}" if bad else None)


def judge_video(model, wav, texts):
    b = base64.b64encode(open(wav, "rb").read()).decode()
    script = "\n".join(f"{i}: {t}" for i, t in enumerate(texts))
    body = {"contents": [{"parts": [
        {"inlineData": {"mimeType": "audio/wav", "data": b}},
        {"text": "You are a native Saudi (Riyadh) Arabic speaker checking a female voiceover against its script. Script lines:\n" + script +
         "\nReturn JSON only: {\"dialect_heard\":..., \"saudi_authenticity_1to10\":n, \"naturalness_1to10\":n, "
         "\"lines\":[{\"i\":n, \"heard\":..., \"matches\":true/false, \"issue\":...}], \"overall_ok\":true/false}"}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    errs = []
    for m in [model] + [x for x in G.get("qa_fallbacks", []) if x != model]:
        try:
            r = post(m, body, tries=2)
            out = json.loads("".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"]))
            out["judge_model"] = m
            return out
        except (SystemExit, Exception) as e:
            errs.append(f"{m}: {str(e)[:60]}")
    raise SystemExit("; ".join(errs))


tts_model = G.get("tts_model", "gemini-3.8-flash-tts")
qa_model = G.get("qa_model", "gemini-3.8-flash")
report_path = f"{proj}/audio/qa_report.json"
report = json.load(open(report_path, encoding="utf-8")) if os.path.exists(report_path) else {}
for vid, V in S["videos"].items():
    if only and vid not in only:
        continue
    d = f"{proj}/audio/{vid}"
    os.makedirs(d, exist_ok=True)
    texts = [ln["text"] for ln in V["lines"]]
    if all(os.path.exists(f"{d}/l{i:02d}.wav") for i in range(len(texts))) and os.environ.get("FORCE") != "1":
        continue
    voice = V.get("voice", VOICE)
    style = WHOLE_STYLE.format(persona=V.get("persona", "a warm, sincere Saudi woman in her forties"))
    best = None
    for k in range(MAX_TRIES):
        pcm, rate = tts(tts_model, "\n".join(texts), voice=voice, style=style)
        take = f"{d}/full.take{k}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", "-", take], input=pcm, check=True)
        segs, problem = split_lines(load_mono(take, rate), texts, rate)
        if segs is None:
            print(f"{vid} take{k}: split failed ({problem})", flush=True); continue
        try:
            j = judge_video(qa_model, take, texts)
        except SystemExit as e:
            print(f"{vid} take{k}: judge unavailable ({e}); relying on split check", flush=True)
            j = {"overall_ok": problem is None, "lines": []}
        badl = [l["i"] for l in j.get("lines", []) if not l.get("matches", True)]
        ok = j.get("overall_ok", False) and not badl and problem is None
        print(f"{vid} take{k} voice={voice} ok={ok} dialect={j.get('dialect_heard')} auth={j.get('saudi_authenticity_1to10')} "
              f"nat={j.get('naturalness_1to10')} bad_lines={badl} split={problem or 'ok'}", flush=True)
        cand = (ok, -len(badl), take, segs, rate, j, problem)
        if best is None or cand[:2] > best[:2]:
            best = cand
        if ok:
            break
    if best is None:
        sys.exit(f"{vid}: no usable take")
    _, _, take, segs, rate, j, problem = best
    os.replace(take, f"{d}/full.wav")
    import numpy as np
    for i, sgm in enumerate(segs):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", "-", f"{d}/l{i:02d}.wav"],
                       input=(np.clip(sgm, -1, 1) * 32767).astype(np.int16).tobytes(), check=True)
    for f in os.listdir(d):
        if ".take" in f: os.remove(f"{d}/{f}")
    report[vid] = {"tts_model": tts_model, "voice": voice, "judge": j, "split_check": problem or "ok"}
    json.dump(report, open(report_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done")
