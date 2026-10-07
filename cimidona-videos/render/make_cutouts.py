"""Cut the product box out of the white-background product photos (no external services).

python3 make_cutouts.py <project_dir>  ->  assets/gen/box_front.png, assets/gen/box_angle.png
"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter
from collections import deque

proj = sys.argv[1]
out = f"{proj}/assets/gen"
os.makedirs(out, exist_ok=True)


def hull(points):
    pts = sorted(set(points))
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def cutout(src, dst, tol=7, edge=212):
    """Box = (pixels not connected to the near-white border) ∩ convex hull of the box's own
    pixels (coloured print, text, and the darker grey of its edges). The box is convex; the soft
    floor shadow is brighter than `edge`, so it falls outside the hull and is dropped."""
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    h, w, _ = a.shape
    light = a.min(2); sat = a.max(2) - a.min(2)
    cand = (255 - light) < tol
    bg = np.zeros((h, w), bool)
    q = deque([(y, x) for y in (0, h - 1) for x in range(w)] + [(y, x) for x in (0, w - 1) for y in range(h)])
    while q:
        y, x = q.popleft()
        if bg[y, x] or not cand[y, x]:
            continue
        bg[y, x] = True
        if y > 0: q.append((y - 1, x))
        if y < h - 1: q.append((y + 1, x))
        if x > 0: q.append((y, x - 1))
        if x < w - 1: q.append((y, x + 1))
    strong = (~bg) & ((light < edge) | (sat > 25))
    ys, xs = np.nonzero(strong[::2, ::2])
    poly = hull(list(zip((xs * 2).tolist(), (ys * 2).tolist())))
    from PIL import ImageDraw
    hm = Image.new("L", (w, h), 0); ImageDraw.Draw(hm).polygon(poly, fill=255)
    mask = (~bg) & (np.asarray(hm) > 0)
    alpha = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    rgba = im.copy(); rgba.putalpha(alpha)
    rgba = rgba.crop(rgba.getbbox())
    rgba.thumbnail((1000, 1000))
    rgba.save(dst)
    print(dst, rgba.size)


cutout(f"{proj}/assets/box-front-en.jpg", f"{out}/box_front.png")
cutout(f"{proj}/assets/box-angle-ar.jpg", f"{out}/box_angle.png")
