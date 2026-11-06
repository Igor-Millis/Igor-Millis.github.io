"""Generate static/og.png (1200×630 social preview). Run locally once: python tools/make_og.py
Requires Pillow and Windows fonts (Consolas, Georgia, Segoe UI); not part of the CI build."""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
F = Path("C:/Windows/Fonts")
W, H = 1200, 630
BG, LINE, TEXT, DIM, ACC = (11, 14, 17), (31, 39, 46), (230, 232, 234), (111, 122, 132), (108, 196, 201)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# particle trails descending a Gaussian well (same idea as the site hero)
random.seed(7)
cx, cy = 0.72, 0.42
for _ in range(260):
    x, y = random.random(), random.random()
    for _ in range(40):
        gx, gy = (x - cx), (y - cy)
        r = math.hypot(gx, gy) + 1e-6
        nx, ny = x - 0.012 * gx / r - 0.004 * gy, y - 0.012 * gy / r + 0.004 * gx
        a = max(0.0, min(1.0, 1.2 - r * 2))
        col = tuple(int(BG[i] + (ACC[i] - BG[i]) * (0.25 + 0.5 * a)) for i in range(3))
        d.line([(x * W, y * H), (nx * W, ny * H)], fill=col, width=1)
        x, y = nx, ny
        if r < 0.02:
            break

mono = ImageFont.truetype(str(F / "consola.ttf"), 22)
sans = ImageFont.truetype(str(F / "segoeuisl.ttf") if (F / "segoeuisl.ttf").exists() else str(F / "segoeui.ttf"), 76)
serif = ImageFont.truetype(str(F / "georgiai.ttf"), 76)

d.line([(0, 64), (W, 64)], fill=LINE)
d.ellipse([60, 27, 70, 37], fill=ACC)
d.text((84, 20), "igor-millis", font=mono, fill=TEXT)
d.text((W - 420, 20), "work · research · about", font=mono, fill=DIM)
d.text((60, 250), "$ whoami --verbose", font=mono, fill=DIM)
d.text((60, 300), "Statistics student", font=sans, fill=TEXT)
d.text((60, 390), "building products ", font=sans, fill=TEXT)
w = d.textlength("building products ", font=sans)
d.text((60 + w, 390), "that hold up.", font=serif, fill=ACC)
d.line([(0, H - 64), (W, H - 64)], fill=LINE)
d.text((60, H - 44), "B.Sc. Statistics (in progress) · UFES   ·   EduData   ·   Credit Default API", font=mono, fill=DIM)

out = ROOT / "static" / "og.png"
img.save(out, optimize=True)
print(out, out.stat().st_size)
