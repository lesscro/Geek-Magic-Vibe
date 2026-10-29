"""Génère une card GIF animée 240x240 par token (pièce qui tourne) et les pousse.

L'album du firmware cycle les GIF : chaque token reste affiché i_i secondes,
la rotation entre tokens = le cycle album. Rafraîchir les prix = relancer le
script (les GIF sont régénérés et écrasés sur le device).

Usage : python scripts/send_tokens.py [--pairs BTC/USDT,ETH/USDT] [--cycle 15]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from geekmagic import GeekMagicClient, GeekMagicError  # noqa: E402
from geekmagic import data, render, sprites  # noqa: E402

OUTPUT_DIR = ROOT / "output"
FRAME_MS = 90  # durée d'une frame de rotation


def push_gif_alternating(client: GeekMagicClient, gif: Path) -> str:
    """Pousse le GIF sous un nom ALTERNÉ puis purge l'ancienne version.

    Le firmware n'écrase pas un GIF existant de même nom (l'ancien continue
    d'être joué) : on bascule entre <base>1.gif et <base>2.gif.
    """
    import re
    stem = gif.stem  # ex. "btc"
    html = client.list_images()
    names = {m.rsplit("/", 1)[-1] for m in re.findall(r"href='(/image/[^']+)'", html)}
    new = f"{stem}1.gif" if f"{stem}1.gif" not in names else f"{stem}2.gif"
    old = f"{stem}2.gif" if new == f"{stem}1.gif" else f"{stem}1.gif"
    client.upload(str(gif), "/image", new)
    if old in names:
        client.delete(old)
    return new


def build_token_gif(snap: data.MarketSnapshot, out: Path | None = None) -> Path:
    """Card 240x240 animée pour un token -> output/<base>.gif (ou `out`)."""
    frames = []
    for step in range(sprites.ROTATION_FRAMES):
        f = render.new_frame()
        render.draw_token_card(f, snap, step)
        frames.append(f.quantize(colors=64, method=Image.MEDIANCUT))
    base = snap.pair.split("/")[0].lower()
    out = out or OUTPUT_DIR / f"{base}.gif"
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=FRAME_MS, loop=0, optimize=False)
    return out


def main() -> int:
    from geekmagic import pipeline, settings
    cfg = settings.load()
    try:
        pipeline.run(cfg, ["crypto"])
    except GeekMagicError as exc:
        print(f"[!] Push failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
