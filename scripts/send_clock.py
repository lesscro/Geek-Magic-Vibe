"""Génère la card horloge HTC Sense (flip + météo animée) et la pousse.

Contrairement aux autres cards, celle-ci doit être TOUJOURS à l'heure :
tâche planifiée dédiée (1 min), séparée du refresh 9 min tokens/météo.
GIF non bouclé : effet d'entrée aléatoire, le chiffre qui vient de changer se
« retourne », un reflet passe, puis l'image finale reste affichée.

Usage : python scripts/send_clock.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from geekmagic import GeekMagicClient, GeekMagicError  # noqa: E402
from geekmagic import render, scenes, transitions, weather  # noqa: E402
from scripts.send_tokens import push_gif_alternating  # noqa: E402

OUTPUT = ROOT / "output" / "horloge.gif"
FRAME_MS = 100
INTRO_FRAMES = 6
INTRO_MS = 60
HOLD_MS = 30000
CLOCK_FRAMES = scenes.N


def build_clock_gif(now: datetime, w: weather.WeatherSnapshot | None,
                    effect: str | None = None, out: Path | None = None,
                    night_hours: tuple[int, int] = (22, 7)) -> tuple[Path, str]:
    """GIF NON bouclé : effet d'entrée aléatoire, flip, reflet, puis image finale tenue."""
    out = out or OUTPUT
    prev = now - timedelta(minutes=1)
    ns, ne = night_hours
    night = (now.hour >= ns or now.hour < ne) if ns > ne else (ns <= now.hour < ne)
    raw = []
    for step in range(CLOCK_FRAMES):
        f = render.new_frame()
        render.draw_clock_card(f, now.hour, now.minute, step, now=now,
                               prev=(prev.hour, prev.minute), night=night, w=w)
        raw.append(f)
    intro, used = transitions.intro_frames(raw[0], n=INTRO_FRAMES, effect=effect)
    seq = intro + raw
    durations = [INTRO_MS] * len(intro) + [FRAME_MS] * len(raw)
    durations[-1] = HOLD_MS                      # dernière image tenue à l'écran
    frames = [f.quantize(colors=96, method=Image.MEDIANCUT) for f in seq]
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=durations, optimize=False)      # pas de `loop` : lecture unique
    return out, used


def main() -> int:
    from geekmagic import pipeline, settings
    cfg = settings.load()
    try:
        pipeline.run(cfg, ["clock"])
    except GeekMagicError as exc:
        print(f"[!] Push failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
