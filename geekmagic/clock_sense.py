"""Card horloge style HTC Sense (240x240).

Tuiles à volets (flip) noires brillantes, chiffres fins blancs, date dessous,
météo animée au centre du bas (ciel du moment + température), comme le
widget « Horloge et météo » de HTC Sense.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .render import BG, CONDITION_FR, _font_cache, _gradient_bg

WIN_FONTS = Path("C:/Windows/Fonts")

TILE_W, TILE_H = 44, 84
TILE_X = [10, 62, 134, 186]
TILE_Y = 8
FLIP_FRAMES = 6

FR_DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
FR_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
             "septembre", "octobre", "novembre", "décembre"]


def sense_font(size: int, weight: str = "light") -> ImageFont.FreeTypeFont:
    names = {"light": "segoeuil.ttf", "semi": "segoeuisl.ttf", "reg": "segoeui.ttf"}
    key = ("sense-" + weight, size)
    if key not in _font_cache:
        try:
            _font_cache[key] = ImageFont.truetype(str(WIN_FONTS / names[weight]), size)
        except OSError:
            _font_cache[key] = ImageFont.truetype(str(WIN_FONTS / "arial.ttf"), size)
    return _font_cache[key]


def _tile_image(digit: str, night: bool) -> Image.Image:
    """Tuile noire brillante avec chiffre fin ; charnière au milieu."""
    t = Image.new("RGBA", (TILE_W, TILE_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    half = TILE_H // 2
    for y in range(TILE_H):
        if y < half:
            k = y / half
            col = tuple(round(a + (b - a) * k) for a, b in zip((56, 60, 72), (30, 32, 40)))
        else:
            k = (y - half) / half
            col = tuple(round(a + (b - a) * k) for a, b in zip((28, 30, 36), (12, 13, 17)))
        d.line([(0, y), (TILE_W - 1, y)], fill=col)
    mask = Image.new("L", t.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, TILE_W - 1, TILE_H - 1], radius=7, fill=255)
    t.putalpha(mask)
    d = ImageDraw.Draw(t)
    f = sense_font(68)
    dc = (176, 180, 190) if night else (248, 250, 252)
    tw = d.textlength(digit, font=f)
    d.text((TILE_W / 2 - tw / 2, TILE_H / 2 - 49), digit, font=f, fill=dc)
    d.line([(0, half - 1), (TILE_W - 1, half - 1)], fill=(4, 4, 6))
    d.line([(0, half), (TILE_W - 1, half)], fill=(70, 74, 86))
    d.line([(2, 1), (TILE_W - 3, 1)], fill=(74, 79, 92))
    d.rounded_rectangle([0, 0, TILE_W - 1, TILE_H - 1], radius=7, outline=(10, 11, 14), width=1)
    return t


_tile_cache: dict[tuple[str, bool], Image.Image] = {}


def _tile(digit: str, night: bool) -> Image.Image:
    key = (digit, night)
    if key not in _tile_cache:
        _tile_cache[key] = _tile_image(digit, night)
    return _tile_cache[key]


def _paste_tile(img: Image.Image, i: int, new: str, old: str, step: int, night: bool) -> None:
    x, y = TILE_X[i], TILE_Y
    half = TILE_H // 2
    tn, to = _tile(new, night), _tile(old, night)
    if new == old or step >= FLIP_FRAMES:
        img.paste(tn, (x, y), tn)
        return
    top_new = tn.crop((0, 0, TILE_W, half))
    bot_old = to.crop((0, half, TILE_W, TILE_H))
    img.paste(top_new, (x, y), top_new)
    img.paste(bot_old, (x, y + half), bot_old)
    which, k = {0: ("old", 1.0), 1: ("old", 0.62), 2: ("old", 0.24),
                3: ("new", 0.24), 4: ("new", 0.62), 5: ("new", 1.0)}[step]
    h = max(1, round(half * k))
    if which == "old":                          # volet haut ancien qui se rabat
        flap = to.crop((0, 0, TILE_W, half)).resize((TILE_W, h), Image.BILINEAR)
        pos = (x, y + half - h)
    else:                                       # volet bas nouveau qui se déplie
        flap = tn.crop((0, half, TILE_W, TILE_H)).resize((TILE_W, h), Image.BILINEAR)
        pos = (x, y + half)
    img.paste(flap, pos, flap)
    dim = round(100 * (1 - k))
    img.paste((0, 0, 0), pos, flap.getchannel("A").point(lambda v: v * dim // 255))


def _sweep(img: Image.Image, step: int) -> Image.Image:
    """Reflet glossy diagonal qui balaie les tuiles (frames 9-17)."""
    sx = -30 + (step - 9) * 32
    sweep = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sweep).polygon(
        [(sx, TILE_Y), (sx + 18, TILE_Y), (sx + 2, TILE_Y + TILE_H), (sx - 16, TILE_Y + TILE_H)],
        fill=(255, 255, 255, 13))
    clip = Image.new("L", img.size, 0)
    cd = ImageDraw.Draw(clip)
    for tx in TILE_X:
        cd.rounded_rectangle([tx, TILE_Y, tx + TILE_W - 1, TILE_Y + TILE_H - 1], radius=7, fill=255)
    a = sweep.getchannel("A")
    sweep.putalpha(Image.composite(a, Image.new("L", img.size, 0), clip))
    return Image.alpha_composite(img.convert("RGBA"), sweep).convert("RGB")


def _weather_panel(w, step: int, size: tuple[int, int], box_x: int) -> Image.Image:
    pw, ph = size
    if w is None:
        panel = Image.new("RGB", size, (24, 32, 52))
        ImageDraw.Draw(panel).text((16, 8), "--°", font=sense_font(58), fill=(140, 150, 170))
        return panel
    from . import scenes as sc
    c = sc.Ctx(w, step % sc.N)
    full = Image.new("RGB", (240, 240), BG)
    sc.draw_sky(full, c)
    sc.draw_sun(full, c)
    sc.draw_moon_stars(full, c)
    sc.draw_clouds(full, c)
    sc.draw_fog(full, c)
    sc.draw_rain(full, c)
    sc.draw_snow(full, c)
    sc.draw_lightning(full, c)
    panel = full.crop((box_x, 4, box_x + pw, 4 + ph))
    for k in range(30):                          # ancre les textes du bas
        a = round(160 * (k / 29) ** 1.6)
        ov = Image.new("RGBA", (pw, 1), (6, 10, 22, a))
        panel.paste(ov, (0, ph - 30 + k), ov)
    pd = ImageDraw.Draw(panel)
    outline = (12, 20, 44)
    pd.text((16, 6), f"{w.temp:.0f}°", font=sense_font(58), fill=(255, 255, 255),
            stroke_width=2, stroke_fill=outline)
    cond = CONDITION_FR.get(w.icon, w.icon).capitalize()
    pd.text((18, ph - 28), cond, font=sense_font(17, "semi"), fill=(255, 255, 255),
            stroke_width=2, stroke_fill=outline)
    fcity = sense_font(13, "semi")
    pd.text((pw - 14 - pd.textlength(w.city, font=fcity), ph - 24), w.city, font=fcity,
            fill=(224, 232, 246), stroke_width=2, stroke_fill=outline)
    return panel


def draw_clock_card(img: Image.Image, hh: int, mm: int, step: int = 0, now=None,
                    prev=None, night: bool = False, w=None) -> None:
    """Horloge HTC Sense : tuiles flip, date, météo animée en bas.

    prev = (hh, mm) de la minute précédente (les chiffres qui changent se retournent).
    w = WeatherSnapshot, ou None (panneau sans données).
    """
    _gradient_bg(img, (0, 0, 239, 239), (22, 30, 48) if not night else (10, 13, 24),
                 (6, 8, 14), bands=24)
    new = f"{hh:02d}{mm:02d}"
    old = f"{prev[0]:02d}{prev[1]:02d}" if prev else new
    for i in range(4):
        _paste_tile(img, i, new[i], old[i], step, night)
    if 9 <= step <= 17:
        img.paste(_sweep(img, step))
    d = ImageDraw.Draw(img)

    pulse = 0.55 + 0.45 * math.sin(2 * math.pi * step / 24)
    dot = tuple(round(v * pulse) for v in (255, 140, 40))
    for cy in (TILE_Y + 28, TILE_Y + 56):
        d.rectangle([115, cy - 1, 124, cy + 8], outline=tuple(round(v * 0.35) for v in dot))
        d.rectangle([116, cy, 123, cy + 7], fill=dot)

    if now is not None:
        label = f"{FR_DAYS[now.weekday()]} {now.day} {FR_MONTHS[now.month - 1]}"
        f = sense_font(17, "semi")
        d.text((120 - d.textlength(label, font=f) / 2, 98), label, font=f, fill=(196, 204, 220))
    d.line([(14, 123), (226, 123)], fill=(40, 48, 70))

    box = (10, 130, 230, 232)
    pw, ph = box[2] - box[0], box[3] - box[1]
    panel = _weather_panel(w, step, (pw, ph), box[0])
    mask = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=12, fill=255)
    img.paste(panel, (box[0], box[1]), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([box[0], box[1], box[2] - 1, box[3] - 1], radius=12, outline=(70, 82, 112), width=1)
    d.line([(box[0] + 12, box[1] + 1), (box[2] - 13, box[1] + 1)], fill=(150, 168, 206))
