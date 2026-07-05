#!/usr/bin/env python3
"""Render the Google Play feature graphic — a REAL, committed store asset (ACCEPTANCE_AUDIT G7).

Google Play REQUIRES a 1024x500, 24-bit PNG with NO alpha channel to publish. A feature graphic
is a MARKETING BANNER (not a device screenshot), so it does not need a running app build — it is
deterministically generated here from the brand system and committed as
``docs/store/assets/feature-graphic.png``. Re-run to regenerate byte-identically:

    python3 scripts/generate_feature_graphic.py

Design follows the product's own surfaces (VISION.md): a dark slate canvas with the single
indigo ``#6366F1`` accent and white type — deliberately NOT flat-bright-indigo or centered
blandness. Left-aligned wordmark + tagline with a real fit-score ring on the right (the app's
signature feature), so the banner shows what the product DOES, not decoration.
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1024, 500
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "store", "assets", "feature-graphic.png")

# Brand system (matches the web/mobile UI: dark slate + one indigo accent + white type).
INDIGO = (99, 102, 241)          # #6366F1 — the single accent
INDIGO_DEEP = (79, 70, 229)      # #4F46E5 — accent gradient partner
SLATE_TOP = (11, 16, 32)         # near-black slate (canvas top)
SLATE_BOTTOM = (19, 26, 46)      # slightly lighter slate (canvas bottom)
WHITE = (245, 247, 252)
SLATE_300 = (176, 185, 204)      # muted tagline text

_FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(_FONT_DIR, name), size)


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _vertical_gradient(size: tuple[int, int], top, bottom) -> Image.Image:
    """A smooth top->bottom gradient as an RGB image (no alpha — Play forbids it)."""
    w, h = size
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        grad.putpixel((0, y), _lerp(top, bottom, y / max(h - 1, 1)))
    return grad.resize((w, h))


def _indigo_glow(size: tuple[int, int], center, radius: int, strength: float) -> Image.Image:
    """A soft radial indigo glow, composited over the canvas for depth (bounded, not noise)."""
    w, h = size
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    px = glow.load()
    cx, cy = center
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            t = max(0.0, 1.0 - d / radius)
            f = (t * t) * strength  # quadratic falloff
            if f > 0:
                px[x, y] = (round(INDIGO[0] * f), round(INDIGO[1] * f), round(INDIGO[2] * f))
    return glow


def _score_ring(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, pct: float) -> None:
    """The app's signature fit-score gauge: a faint full track + an indigo arc to ``pct``."""
    track = _lerp(SLATE_BOTTOM, WHITE, 0.16)
    stroke = 16
    box = [cx - r, cy - r, cx + r, cy + r]
    draw.ellipse(box, outline=track, width=stroke)
    draw.arc(box, -90, -90 + int(360 * pct), fill=INDIGO, width=stroke)


def build() -> Image.Image:
    img = _vertical_gradient((WIDTH, HEIGHT), SLATE_TOP, SLATE_BOTTOM)
    # Depth: a soft indigo glow behind the right-side score ring.
    img = Image.blend(img, _indigo_glow((WIDTH, HEIGHT), (812, 250), 360, 0.55), 0.5)
    draw = ImageDraw.Draw(img)

    left = 76
    # Brand mark: an indigo rounded tile with a white upward chevron (momentum / rising fit).
    tile = 60
    ty = 92
    draw.rounded_rectangle([left, ty, left + tile, ty + tile], radius=16, fill=INDIGO)
    cx0 = left + tile / 2
    draw.line(
        [(cx0 - 14, ty + 38), (cx0, ty + 22), (cx0 + 14, ty + 38)],
        fill=WHITE, width=6, joint="curve",
    )
    draw.line([(cx0, ty + 22), (cx0, ty + 42)], fill=WHITE, width=6)

    # Wordmark + tagline (left-aligned column, kept clear of the ring's left edge at x~784).
    draw.text((left, 188), "Career Operator", font=_font("DejaVuSans-Bold.ttf", 60), fill=WHITE)
    tag_font = _font("DejaVuSans.ttf", 26)
    draw.text((left, 296), "AI fit scores, interview prep,", font=tag_font, fill=SLATE_300)
    draw.text((left, 334), "and an AI career coach — one pipeline.", font=tag_font, fill=SLATE_300)

    # Signature fit-score ring on the right (shows what the product does), vertically centred.
    ring_cx, ring_cy, ring_r = 884, 250, 100
    _score_ring(draw, ring_cx, ring_cy, ring_r, pct=0.92)
    num_font = _font("DejaVuSans-Bold.ttf", 62)
    num = "92"
    nb = draw.textbbox((0, 0), num, font=num_font)
    draw.text(
        (ring_cx - (nb[2] + nb[0]) / 2, ring_cy - (nb[3] + nb[1]) / 2 - 10),
        num, font=num_font, fill=WHITE,
    )
    lab_font = _font("DejaVuSans.ttf", 20)
    lab = "fit score"
    lb = draw.textbbox((0, 0), lab, font=lab_font)
    draw.text((ring_cx - (lb[2] + lb[0]) / 2, ring_cy + 30), lab, font=lab_font, fill=SLATE_300)

    return img


def main() -> None:
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    img = build()
    assert img.size == (WIDTH, HEIGHT)
    assert img.mode == "RGB"  # 24-bit, NO alpha — Play requirement
    img.save(OUT_PATH, "PNG", optimize=True)
    print(f"Wrote {os.path.normpath(OUT_PATH)} ({WIDTH}x{HEIGHT}, mode={img.mode})")


if __name__ == "__main__":
    main()
