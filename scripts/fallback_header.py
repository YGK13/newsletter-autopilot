"""
Fallback header image generator.

Runs only if DALL-E 3 is unreachable or returns an unusable image.
Produces a 1920x1080 PNG using YOUR brand palette from config/brand.json
(image_brand.background_hex / accent_hex / accent_dim_hex / accent_bright_hex):
a flat background with a single accent-colored signal-arc + line motif.
"""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def build_fallback_header(
    out_path: Path,
    *,
    background_hex: str,
    accent_hex: str,
    accent_dim_hex: str,
    accent_bright_hex: str,
    seed: int | None = None,
) -> Path:
    bg = _hex(background_hex)
    accent = _hex(accent_hex)
    accent_dim = _hex(accent_dim_hex)
    accent_bright = _hex(accent_bright_hex)

    rand = random.Random(seed or 0)
    img = Image.new("RGB", (W, H), bg)

    # very light noise for editorial texture
    noise = Image.new("L", (W, H), 0)
    npx = noise.load()
    for y in range(H):
        for x in range(W):
            npx[x, y] = rand.randint(0, 6)
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    img = Image.blend(img, Image.eval(noise_rgb, lambda v: min(30, v)), 0.5)
    draw = ImageDraw.Draw(img)

    # signal source dot + horizontal line + concentric arcs
    cx, cy = int(W * 0.30), int(H * 0.55)
    dot_r = 18

    line_x0 = cx + dot_r + 60
    line_x1 = int(W * 0.86)
    segs = 200
    for i in range(segs):
        t = i / (segs - 1)
        x0 = line_x0 + int((line_x1 - line_x0) * (i / segs))
        x1 = line_x0 + int((line_x1 - line_x0) * ((i + 1) / segs))
        a = 1.0 - (t**1.2) * 0.55
        col = tuple(int(accent[c] * a + bg[c] * (1 - a)) for c in range(3))
        draw.rectangle([x0, cy - 1, x1 + 1, cy + 2], fill=col)

    for dr in range(dot_r + 8, dot_r, -1):
        a = (dot_r + 8 - dr) / 8
        col = tuple(int(accent_dim[c] * a + bg[c] * (1 - a)) for c in range(3))
        draw.ellipse([cx - dr, cy - dr, cx + dr, cy + dr], fill=col)
    draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=accent_bright)

    for arc_r, thickness, alpha in [(120, 3, 0.35), (220, 2, 0.20), (340, 2, 0.10)]:
        col = tuple(int(accent[c] * alpha + bg[c] * (1 - alpha)) for c in range(3))
        bbox = [cx - arc_r, cy - arc_r, cx + arc_r, cy + arc_r]
        for _ in range(thickness):
            draw.arc(bbox, start=-55, end=55, fill=col, width=1)
            bbox = [bbox[0] - 1, bbox[1] - 1, bbox[2] + 1, bbox[3] + 1]

    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))

    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    for r in range(0, max(W, H), 8):
        a = min(255, int(r * 0.14))
        vd.ellipse([-r, -r, W + r, H + r], outline=a, width=8)
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=180))
    bg_layer = Image.new("RGB", (W, H), bg)
    img = Image.composite(bg_layer, img, vignette)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return out_path
