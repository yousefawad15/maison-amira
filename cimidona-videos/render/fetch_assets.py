"""Download generated images into assets/gen (scenes → 1200px JPEG, cutouts → trimmed PNG)."""
import json, os, subprocess, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

proj = sys.argv[1]
only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
J = json.load(open(f"{proj}/jobs.json"))
out = f"{proj}/assets/gen"
os.makedirs(out, exist_ok=True)


def get(item):
    key, fn = item
    if only and not any(key.startswith(o) for o in only):
        return
    if key.endswith("_cut"):  # cutouts are now made locally by make_cutouts.py
        return
    raw = f"{out}/_{key}.png"
    urllib.request.urlretrieve(J["audio_base"] + fn, raw)
    from PIL import Image
    im = Image.open(raw).convert("RGB")
    im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS).save(f"{out}/{key}.jpg", quality=90)
    os.remove(raw)


with ThreadPoolExecutor(8) as ex:
    list(ex.map(get, J["images"].items()))
print(sorted(os.listdir(out)))
