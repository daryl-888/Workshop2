# -*- coding: utf-8 -*-
"""
Renders the picture assets the deck uses, straight from the workshop's own
photo and the programs' real output. Run from the repo root:

    python lab/verify.py          # produces build/gray.ppm and build/blur.ppm
    python slides/make_assets.py
"""
import os
import sys
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(REPO, "build")
OUT = os.path.join(REPO, "slides", "assets")
os.makedirs(OUT, exist_ok=True)

src = os.path.join(REPO, "images", "sample_1920x1280.ppm")
need = {"gray": os.path.join(BUILD, "gray.ppm"), "blur": os.path.join(BUILD, "blur.ppm")}

missing = [p for p in [src] + list(need.values()) if not os.path.exists(p)]
if missing:
    print("Missing inputs:")
    for m in missing:
        print("  " + m)
    print("\nRun `python lab/verify.py` first — it produces the two .ppm outputs.")
    sys.exit(1)

before = Image.open(src).convert("RGB")
gray = Image.open(need["gray"]).convert("RGB")
blur = Image.open(need["blur"]).convert("RGB")


def save(img, name, width):
    h = round(img.height * width / img.width)
    img.resize((width, h), Image.LANCZOS).save(os.path.join(OUT, name), quality=92)
    print("  " + name + "  " + str(width) + "x" + str(h))


# Full-frame versions for the "what we're building" slide.
print("writing " + OUT)
save(before, "before.jpg", 1000)
save(gray, "gray.jpg", 1000)
save(blur, "blur.jpg", 1000)

# A detailed crop, so the blur is actually visible on a projector.
# Same "busiest square" logic the notebook uses.
import numpy as np                                                   # noqa: E402

g = np.asarray(before.convert("L"), dtype=np.float32)
size = 420
best, best_v = (0, 0), -1.0
for y in range(0, g.shape[0] - size, (g.shape[0] - size) // 8):
    for x in range(0, g.shape[1] - size, (g.shape[1] - size) // 8):
        v = float(g[y:y + size, x:x + size].std())
        if v > best_v:
            best_v, best = v, (y, x)
y, x = best
box = (x, y, x + size, y + size)
print("  crop at " + str(box))
save(before.crop(box), "crop_before.jpg", 520)
save(blur.crop(box), "crop_blur.jpg", 520)
print("done")
