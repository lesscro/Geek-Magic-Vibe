"""Génère la card météo GIF 240x240 (scène pixel art du jour) et la pousse.

Usage : python scripts/send_weather.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from geekmagic import GeekMagicClient, GeekMagicError  # noqa: E402
from geekmagic import render, scenes, weather  # noqa: E402
from scripts.send_tokens import push_gif_alternating  # noqa: E402

OUTPUT = ROOT / "output" / "meteo.gif"
FRAME_MS = 110  # boucle de scène (scenes.N frames)


def build_weather_gif(w: weather.WeatherSnapshot, out: Path | None = None,
                      place: str | None = None, allowed: list[str] | None = None) -> Path:
    out = out or OUTPUT
    frames = []
    for step in range(scenes.N):
        f = render.new_frame()
        render.draw_weather_card(f, w, step, place=place, allowed=allowed)
        frames.append(f.quantize(colors=128, method=Image.MEDIANCUT))
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=FRAME_MS, loop=0, optimize=False)
    return out


def main() -> int:
    from geekmagic import pipeline, settings
    cfg = settings.load()
    try:
        pipeline.run(cfg, ["weather"])
    except GeekMagicError as exc:
        print(f"[!] Échec push : {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
