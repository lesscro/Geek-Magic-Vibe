"""Génère les captures des cards (x2, pixel perfect) pour le README -> docs/screenshots/.

Données neutres : météo d'exemple (Paris), cours réels Binance (repli : aucun
snapshot crypto si le réseau manque). Aucune donnée personnelle.

Usage : python scripts/make_screenshots.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from geekmagic import data, render, weather  # noqa: E402

OUT = ROOT / "docs" / "screenshots"
SCALE = 2


def save(img: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST).save(OUT / name, optimize=True)
    print(f"[+] {name}")


def sample(**kw) -> weather.WeatherSnapshot:
    base = dict(city="Paris", temp=21, feels=21, code=0, is_day=True, icon="PARTLY", phase="APRES-MIDI",
                meal=None, wind=8, season="SUMMER", hour=15.0, doy=120, year=2026)
    base.update(kw)
    return weather.WeatherSnapshot(**base)


def card(draw, *args, **kw) -> Image.Image:
    f = render.new_frame()
    draw(f, *args, **kw)
    return f


def strip(images: list[Image.Image]) -> Image.Image:
    sheet = Image.new("RGB", (240 * len(images) + 12 * (len(images) - 1), 240), (8, 10, 17))
    for i, im in enumerate(images):
        sheet.paste(im, (i * 252, 0))
    return sheet


def main() -> int:
    crypto = []
    for pair in ("BTC/USDT", "ETH/USDT", "SOL/USDT"):
        try:
            crypto.append(card(render.draw_token_card, data.get_market(pair), 0))
        except Exception as exc:  # noqa: BLE001
            print(f"[!] {pair} : {exc}")
    if crypto:
        save(strip(crypto), "cards-crypto.png")

    scenes_day = [("city", {}), ("lake", {}), ("beach", {}), ("mountains", {})]
    save(strip([card(render.draw_weather_card, sample(**k), 6, place=p) for p, k in scenes_day]), "cards-meteo-jour.png")
    mixed = [("cafe", dict(icon="MOON", phase="NUIT", hour=22.5, is_day=False, temp=11)),
             ("park", dict(icon="SNOW", code=73, temp=-1, season="WINTER", phase="JOURNEE", hour=11)),
             ("harbor", dict(icon="RAIN", code=63, temp=12, season="AUTUMN", phase="MATIN", hour=9)),
             ("bridge", dict(icon="PARTLY", phase="CREPUSCULE", hour=19.8, season="AUTUMN", temp=16))]
    save(strip([card(render.draw_weather_card, sample(**k), 6, place=p) for p, k in mixed]), "cards-meteo-moments.png")

    now = datetime(2026, 6, 15, 14, 32)
    clocks = [card(render.draw_clock_card, 14, 32, step, now=now, prev=(14, 31), w=sample()) for step in (2, 4, 20)]
    save(strip(clocks), "card-horloge.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
