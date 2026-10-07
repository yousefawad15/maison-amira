"""Saudi-dialect voiceover via Google AI Studio (Gemini API TTS), one clip per script line.

python3 tts_gemini.py <project_dir> [v1 v2 ...]     (needs GEMINI_API_KEY)

Each take is transcribed back by a Gemini text model; takes whose transcript drifts
from the script are regenerated (up to MAX_TRIES). Output: <project>/audio/<vid>/lNN.wav
"""
import base64, difflib, json, os, re, subprocess, sys, time, urllib.error, urllib.request

proj = sys.argv[1]
only = sys.argv[2:] or None
KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not KEY:
    sys.exit("GEMINI_API_KEY is not set")
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
    url = f"{API}/models/{model}:generateContent"
    data = json.dumps(body).encode()
    for k in range(tries):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
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
    with urllib.request.urlopen(urllib.request.Request(f"{API}/models?pageSize=200", headers={"x-goog-api-key": KEY})) as r:
        names = [m["name"].split("/")[-1] for m in json.load(r)["models"]]
    tts = [n for n in names if "tts" in n]
    pref = G.get("tts_model")
    tts_model = pref if pref in names else next((n for n in sorted(tts, reverse=True) if "pro" in n), None) or sorted(tts)[-1]
    text = [n for n in names if n.startswith("gemini") and "tts" not in n and "image" not in n and "live" not in n and "embedding" not in n]
    qa_model = G.get("qa_model") if G.get("qa_model") in names else next((n for n in text if "2.5-flash" == n.replace("gemini-", "")), None) or next(n for n in text if "flash" in n)
    return tts_model, qa_model


def tts(model, text):
    body = {"contents": [{"parts": [{"text": f"{STYLE}\n\n{text}"}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}
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


tts_model, qa_model = pick_models()
print("TTS model:", tts_model, "| QA model:", qa_model, "| voice:", VOICE, flush=True)
report = {}
for vid, V in S["videos"].items():
    if only and vid not in only:
        continue
    os.makedirs(f"{proj}/audio/{vid}", exist_ok=True)
    for i, ln in enumerate(V["lines"]):
        out = f"{proj}/audio/{vid}/l{i:02d}.wav"
        if os.path.exists(out) and os.environ.get("FORCE") != "1":
            continue
        best = None
        for k in range(MAX_TRIES):
            pcm, rate = tts(tts_model, ln["text"])
            tmp = f"{out}.take{k}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", "-", tmp], input=pcm, check=True)
            heard = transcribe(qa_model, tmp)
            text_part = heard.split("DIALECT:")[0]
            dialect = heard.split("DIALECT:")[-1].strip() if "DIALECT:" in heard else "?"
            sc = score(ln["text"], text_part)
            print(f"{vid} l{i:02d} take{k} score={sc:.2f} dialect={dialect} | {text_part.strip()}", flush=True)
            if best is None or sc > best[0]:
                best = (sc, tmp, text_part.strip(), dialect)
            if sc >= 0.85:
                break
        os.replace(best[1], out)
        for f in os.listdir(f"{proj}/audio/{vid}"):
            if ".take" in f:
                os.remove(f"{proj}/audio/{vid}/{f}")
        report[f"{vid}/l{i:02d}"] = {"script": ln["text"], "heard": best[2], "score": round(best[0], 2), "dialect": best[3]}
if report:
    path = f"{proj}/audio/qa_report.json"
    old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    old.update(report)
    json.dump(old, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("low-score lines:", {k: v["score"] for k, v in old.items() if v["score"] < 0.85})
