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
    raw = f"{out}/_{key}.png"
    urllib.request.urlretrieve(J["audio_base"] + fn, raw)
    if key.endswith("_cut"):
        name = key[:-4]  # box_front / box_angle
        subprocess.run(["convert", raw, "-trim", "+repage", "-resize", "1000x1000>", f"{out}/{name}.png"], check=True)
    else:
        subprocess.run(["convert", raw, "-resize", "1200x", "-quality", "90", f"{out}/{key}.jpg"], check=True)
    os.remove(raw)


with ThreadPoolExecutor(8) as ex:
    list(ex.map(get, J["images"].items()))
print(sorted(os.listdir(out)))
