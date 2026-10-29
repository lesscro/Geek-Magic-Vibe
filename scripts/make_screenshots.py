"""Génère les captures des cards (x2, pixel perfect) pour le README -> docs/screenshots/.

Données neutres : météo d'exemple (Paris), cours réels Binance (repli : aucun
snapshot crypto si le réseau manque). Aucune donnée personnelle.

Usage : python scripts/make_screenshots.py          # captures PNG des cards
        python scripts/make_screenshots.py --gifs   # mini écrans animés
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from geekmagic import data, i18n, render, weather  # noqa: E402

i18n.use("en")

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


def gifs() -> None:
    """Mini écrans animés (GIF 240x240, boucle) pour le README -> docs/screenshots/anim/."""
    from geekmagic import scenes, sprites, transitions

    anim = OUT / "anim"
    anim.mkdir(parents=True, exist_ok=True)

    def write(name: str, frames: list[Image.Image], ms, colors: int, loop: bool = True) -> None:
        q = [f.quantize(colors=colors, method=Image.MEDIANCUT) for f in frames]
        kw = {"loop": 0} if loop else {}
        q[0].save(anim / name, save_all=True, append_images=q[1:], duration=ms, optimize=False, **kw)
        print(f"[+] anim/{name} ({(anim / name).stat().st_size // 1024} Ko)")

    try:
        snap = data.get_market("BTC/USDT")
        write("crypto-btc.gif", [card(render.draw_token_card, snap, st) for st in range(sprites.ROTATION_FRAMES)], 90, 64)
    except Exception as exc:  # noqa: BLE001
        print(f"[!] crypto : {exc}")

    cases = {
        "weather-city.gif": ("city", {}),
        "weather-cafe-night.gif": ("cafe", dict(icon="MOON", phase="NUIT", hour=22.5, is_day=False, temp=11)),
        "weather-park-snow.gif": ("park", dict(icon="SNOW", code=73, temp=-1, season="WINTER", phase="JOURNEE", hour=11)),
        "weather-harbor-rain.gif": ("harbor", dict(icon="RAIN", code=63, temp=12, season="AUTUMN", phase="MATIN", hour=9)),
        "weather-beach.gif": ("beach", dict(icon="SUN", temp=27)),
        "weather-bridge-dusk.gif": ("bridge", dict(phase="CREPUSCULE", hour=19.8, season="AUTUMN", temp=16)),
    }
    for name, (place, kw) in cases.items():
        w = sample(**kw)
        write(name, [card(render.draw_weather_card, w, st, place=place) for st in range(scenes.N)], 110, 112)

    now = datetime(2026, 6, 15, 14, 32)
    frames = [card(render.draw_clock_card, 14, 32, st, now=now, prev=(14, 31), w=sample()) for st in range(scenes.N)]
    intro, _ = transitions.intro_frames(frames[0], n=6, effect="slide_up")
    seq = intro + frames
    write("clock.gif", seq, [60] * 6 + [100] * (len(frames) - 1) + [1800], 96)


def main() -> int:
    if "--gifs" in sys.argv:
        gifs()
        return 0
    crypto = []
    for pair in ("BTC/USDT", "ETH/USDT", "SOL/USDT"):
        try:
            crypto.append(card(render.draw_token_card, data.get_market(pair), 0))
        except Exception as exc:  # noqa: BLE001
            print(f"[!] {pair} : {exc}")
    if crypto:
        save(strip(crypto), "cards-crypto.png")

    scenes_day = [("city", {}), ("lake", {}), ("beach", {}), ("mountains", {})]
    save(strip([card(render.draw_weather_card, sample(**k), 6, place=p) for p, k in scenes_day]), "cards-weather-day.png")
    mixed = [("cafe", dict(icon="MOON", phase="NUIT", hour=22.5, is_day=False, temp=11)),
             ("park", dict(icon="SNOW", code=73, temp=-1, season="WINTER", phase="JOURNEE", hour=11)),
             ("harbor", dict(icon="RAIN", code=63, temp=12, season="AUTUMN", phase="MATIN", hour=9)),
             ("bridge", dict(icon="PARTLY", phase="CREPUSCULE", hour=19.8, season="AUTUMN", temp=16))]
    save(strip([card(render.draw_weather_card, sample(**k), 6, place=p) for p, k in mixed]), "cards-weather-moments.png")

    now = datetime(2026, 6, 15, 14, 32)
    clocks = [card(render.draw_clock_card, 14, 32, step, now=now, prev=(14, 31), w=sample()) for step in (2, 4, 20)]
    save(strip(clocks), "card-clock.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
