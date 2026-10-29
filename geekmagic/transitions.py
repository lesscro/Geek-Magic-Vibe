"""Transitions d'entrée « cuites » dans le GIF (le firmware ne propose que son fondu).

intro_frames() renvoie quelques frames qui amènent la première image du GIF à
l'écran avec un effet (fondu, glissement, zoom, rideau, dissolution, iris),
choisi au hasard à chaque génération ou imposé via `effect`.
"""

from __future__ import annotations

import random

from PIL import Image, ImageDraw

EFFECTS = ["fade", "slide_left", "slide_right", "slide_up", "slide_down",
           "zoom", "wipe", "dissolve", "iris"]


def _ease(p: float) -> float:
    return 1 - (1 - p) ** 2


def _frame(first: Image.Image, effect: str, p: float, rng: random.Random, noise: list[float]) -> Image.Image:
    w, h = first.size
    e = _ease(p)
    black = Image.new("RGB", first.size, (0, 0, 0))
    if effect == "fade":
        return Image.blend(black, first, e)
    if effect.startswith("slide"):
        out = black.copy()
        dx = {"slide_left": 1, "slide_right": -1}.get(effect, 0)
        dy = {"slide_up": 1, "slide_down": -1}.get(effect, 0)
        out.paste(first, (round(dx * w * (1 - e)), round(dy * h * (1 - e))))
        return out
    if effect == "zoom":
        s = 0.55 + 0.45 * e
        sz = (max(1, round(w * s)), max(1, round(h * s)))
        small = first.resize(sz, Image.BILINEAR)
        out = Image.blend(black, first, e * 0.35)
        out.paste(small, ((w - sz[0]) // 2, (h - sz[1]) // 2))
        return Image.blend(black, out, min(1.0, 0.4 + e))
    mask = Image.new("L", first.size, 0)
    md = ImageDraw.Draw(mask)
    if effect == "wipe":
        md.rectangle([0, 0, round(w * e), h], fill=255)
    elif effect == "dissolve":
        bs = 8
        cols = w // bs
        for by in range(h // bs):
            for bx in range(cols):
                if noise[by * cols + bx] <= e:
                    md.rectangle([bx * bs, by * bs, bx * bs + bs - 1, by * bs + bs - 1], fill=255)
    else:  # iris
        r = round(e * (w * 0.75))
        md.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r], fill=255)
    return Image.composite(first, black, mask)


def intro_frames(first: Image.Image, n: int = 6, effect: str | None = None,
                 seed: int | None = None) -> tuple[list[Image.Image], str]:
    """(frames, nom de l'effet) — n frames avant `first`."""
    rng = random.Random(seed)
    effect = effect or rng.choice(EFFECTS)
    noise = [rng.random() for _ in range((first.width // 8) * (first.height // 8))]
    frames = [_frame(first, effect, (i + 1) / (n + 1), rng, noise) for i in range(n)]
    return frames, effect
