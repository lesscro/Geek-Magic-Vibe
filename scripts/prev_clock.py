"""Aperçu de l'horloge HTC Sense (montage de 4 frames) -> output/clock_new.png."""

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from geekmagic import render, weather  # noqa: E402


def snap(**kw):
    base = dict(city="Paris", temp=21, feels=21, code=0, is_day=True, icon="PARTLY",
                phase="APRES-MIDI", meal=None, wind=5, season="SUMMER", hour=15, doy=100, year=2026)
    base.update(kw)
    return weather.WeatherSnapshot(**base)


w = snap()
w2 = snap(temp=12, code=63, icon="RAIN", phase="NUIT", season="AUTUMN", hour=23)
now = datetime(2026, 10, 29, 13, 40)
m = Image.new("RGB", (960, 240))
for i, (st, ww, night) in enumerate([(2, w, False), (4, w, False), (12, w, False), (10, w2, True)]):
    f = render.new_frame()
    render.draw_clock_card(f, 13, 40, st, now=now, prev=(13, 39), night=night, w=ww)
    m.paste(f, (240 * i, 0))
m.save(ROOT / "output" / "clock_new.png")
