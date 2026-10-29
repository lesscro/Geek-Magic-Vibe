"""Rendu des cards du dashboard (240x240) avec Pillow.

Layout (config.json) : horloge/météo 240x80, crypto 240x90, agenda 240x70.
Polices pixel : Press Start 2P (titres/prix) + Silkscreen (petites valeurs).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .data import MarketSnapshot
from . import i18n, sprites

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"

BG = (12, 12, 20)
TEXT = (230, 230, 230)
DIM = (90, 90, 110)
GREEN = (0, 255, 170)
RED = (255, 80, 80)

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(size: int, name: str = "PressStart2P-Regular.ttf") -> ImageFont.FreeTypeFont:
    key = (name, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONTS / name), size)
    return _font_cache[key]


def fmt_price(v: float) -> str:
    if v >= 1000:
        return f"{v:,.0f}".replace(",", " ")
    if v >= 1:
        return f"{v:.2f}"
    return f"{v:.4f}"


def fmt_compact(v: float) -> str:
    if v >= 1_000_000:
        return f"{v / 1e6:.1f}M"
    if v >= 1_000:
        return f"{v / 1e3:.1f}K"
    if v >= 1:
        return f"{v:.1f}"
    return f"{v:.4f}"


def _sparkline(d: ImageDraw.ImageDraw, closes: list[float], box, color) -> None:
    """Courbe 1 px dans box — mise à l'échelle min/max de la fenêtre."""
    x0, y0, x1, y1 = box
    if len(closes) < 2:
        return
    lo, hi = min(closes), max(closes)
    span = (hi - lo) or 1.0
    n = len(closes)
    pts = []
    for i, v in enumerate(closes):
        px = x0 + int((x1 - x0) * i / (n - 1))
        py = y1 - int((y1 - y0) * (v - lo) / span)
        pts.append((px, py))
    d.line(pts, fill=color, width=1)


ROCKET = [
    "..1..",
    "..1..",
    ".111.",
    "..1..",
    ".1.1.",
]


def new_frame() -> Image.Image:
    return Image.new("RGB", (240, 240), BG)


def draw_placeholder(img: Image.Image, box: tuple[int, int, int, int], title: str) -> None:
    d = ImageDraw.Draw(img)
    d.rectangle([box[0] + 2, box[1] + 2, box[2] - 3, box[3] - 3], outline=DIM, width=1)
    d.text((box[0] + 8, box[1] + 8), title, font=font(8), fill=DIM)


# ------------------------------------------------------- card token 240x240
# Design inspiré des cards PnL des exchanges : hero % en couleur tendance,
# hiérarchie typo claire, fond dégradé + motif discret, cadre arrondi fin.

ORANGE_ACCENT = (255, 140, 0)

BULL = {
    "trend": GREEN,
    "border": (30, 104, 82),
    "bg_top": (8, 26, 22),
    "bg_bot": (14, 13, 24),
    "motif": (20, 58, 48),
}
BEAR = {
    "trend": RED,
    "border": (112, 38, 44),
    "bg_top": (34, 10, 14),
    "bg_bot": (14, 13, 24),
    "motif": (66, 24, 30),
}


def _center_text(d: ImageDraw.ImageDraw, cx: int, y: int, text: str, f, fill) -> None:
    d.text((cx - d.textlength(text, font=f) / 2, y), text, font=f, fill=fill)


def _gradient_bg(img: Image.Image, box: tuple[int, int, int, int], top, bot, bands: int = 28) -> None:
    """Dégradé vertical quantifié en bandes nettes (pixel art, pas de lissage)."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    h = y1 - y0
    for i in range(bands):
        t = i / (bands - 1)
        col = tuple(round(a + (b - a) * t) for a, b in zip(top, bot))
        ya = y0 + round(h * i / bands)
        yb = y0 + round(h * (i + 1) / bands)
        d.rectangle([x0, ya, x1, yb - 1], fill=col)


def _motif(d: ImageDraw.ImageDraw, up: bool, color) -> None:
    """Motif fond : escalade haussière/baissière + étincelles, très discret."""
    if up:
        pts = [(30, 210), (62, 178), (94, 190), (126, 150), (158, 162), (190, 122), (214, 132)]
    else:
        pts = [(30, 122), (62, 162), (94, 150), (126, 190), (158, 178), (190, 210), (214, 196)]
    d.line(pts, fill=color, width=2)
    for (x, y) in ((44, 96), (150, 70), (206, 88), (100, 212), (28, 150)):
        d.point((x, y), fill=color)
        d.point((x + 2, y - 2), fill=color)


def _txt(d: ImageDraw.ImageDraw, xy, text: str, f, fill, stroke: int = 2,
         stroke_fill=(6, 8, 14)) -> None:
    """Texte avec contour sombre : lisible sur n'importe quel fond (sparkline)."""
    d.text(xy, text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def _chart_columns(closes: list[float], x0: int, x1: int, y0: int, y1: int) -> list[int]:
    """Y de la courbe pour chaque colonne x0..x1 (interpolation linéaire)."""
    lo, hi = min(closes), max(closes)
    span = (hi - lo) or 1.0
    n = len(closes)
    ys = []
    for x in range(x0, x1 + 1):
        pos = (x - x0) / (x1 - x0) * (n - 1)
        i = min(int(pos), n - 2)
        v = closes[i] + (closes[i + 1] - closes[i]) * (pos - i)
        ys.append(y1 - round((y1 - y0) * (v - lo) / span))
    return ys


def _bg_chart(img: Image.Image, closes: list[float], trend, bottom: int = 230) -> None:
    """Sparkline réelle en habillage de fond : aire dégradée + courbe + extrêmes."""
    x0, x1, y0, y1 = 11, 228, 126, 192
    ys = _chart_columns(closes, x0, x1, y0, y1)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i, ly in enumerate(ys):
        x = x0 + i
        depth = bottom - ly
        for yy in range(ly, bottom + 1, 2):
            a = int(78 * (1 - (yy - ly) / max(depth, 1)) ** 1.4) + 8
            od.line([(x, yy), (x, yy + 1)], fill=(*trend, a))
        od.point((x, ly), fill=(*trend, 230))
        od.point((x, ly + 1), fill=(*trend, 150))
    img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"))
    d = ImageDraw.Draw(img)
    for idx, col in ((closes.index(max(closes)), (255, 255, 255)),
                     (closes.index(min(closes)), (255, 255, 255))):
        px = x0 + round((x1 - x0) * idx / (len(closes) - 1))
        d.rectangle([px - 1, ys[px - x0] - 1, px + 1, ys[px - x0] + 1], fill=col)


def draw_token_card(img: Image.Image, snap: MarketSnapshot, step: int = 0) -> None:
    """Card token 240x240 orientée lecture : pièce+nom (haut centré), % héro,
    prix juste dessous, sparkline réelle en fond, L/H du jour lisibles en bas.
    """
    d = ImageDraw.Draw(img)
    base = snap.pair.split("/")[0]
    up = snap.change_24h >= 0
    pal = BULL if up else BEAR
    trend = pal["trend"]

    card = (8, 8, 231, 231)
    _gradient_bg(img, card, pal["bg_top"], pal["bg_bot"])
    if snap.closes and len(snap.closes) >= 2:
        _bg_chart(img, snap.closes, trend)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(card, radius=12, outline=pal["border"], width=2)

    # --- header centré : petite pièce + nom à hauteur égale
    name = base if len(base) <= 5 else base[:5]
    f_name = font(20)
    coin = sprites.coin_frame(base, step, scale=1)                 # 28x28
    total = coin.width + 10 + d.textlength(name, font=f_name)
    hx = 120 - total / 2
    img.paste(coin, (int(hx), 18), coin)
    _txt(d, (hx + coin.width + 10, 22), name, f_name, TEXT, stroke=2)
    if snap.volume_spike:
        r = sprites.bitmap_to_image(ROCKET, (255, 130, 60), size=2)
        img.paste(r, (int(hx + total + 6), 24), r)

    # --- badge extrême 24h
    if snap.at_high or snap.at_low:
        label = "HIGH 24H" if snap.at_high else "LOW 24H"
        tw = d.textlength(label, font=font(8))
        d.rounded_rectangle([120 - tw / 2 - 7, 50, 120 + tw / 2 + 7, 63], radius=6, fill=ORANGE_ACCENT)
        d.text((120 - tw / 2, 53), label, font=font(8), fill=(30, 18, 6))

    # --- hero : flèche + % 24h (inchangé)
    arrow = sprites.bitmap_to_image(
        sprites.ARROW_UP if up else sprites.ARROW_DOWN, trend, size=2)
    pct = f"{abs(snap.change_24h):.2f}%"
    f_pct = font(24)
    aw, ah = arrow.size
    total = aw + 10 + d.textlength(pct, font=f_pct)
    ax = 120 - total / 2
    img.paste(arrow, (int(ax), 72), arrow)
    _txt(d, (ax + aw + 10, 72 + ah // 2 - 12), pct, f_pct, trend)

    # --- prix directement sous le %, taille confortable
    price = fmt_price(snap.price)
    size = 20
    while d.textlength(price, font=font(size)) > 196 and size > 12:
        size -= 2
    f_price = font(size)
    _txt(d, (120 - d.textlength(price, font=f_price) / 2, 108), price, f_price, TEXT)

    # --- L / H du jour : gros, couleurs franches, contour sombre
    if snap.low_24h is not None and snap.high_24h is not None:
        f_lh = font(10)
        _txt(d, (20, 208), f"L {fmt_price(snap.low_24h)}", f_lh, (255, 120, 120))
        h_txt = f"H {fmt_price(snap.high_24h)}"
        _txt(d, (220 - d.textlength(h_txt, font=f_lh), 208), h_txt, f_lh, (110, 255, 200))


# ------------------------------------------------------- card météo 240x240
# Scène pixel art plein cadre (lieu du jour x moment x météo), infos lisibles
# au premier plan : icône + condition, température géante.

def _rounded_clip(img: Image.Image, radius: int = 14, border=(40, 46, 70)) -> None:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=radius, fill=255)
    bg = Image.new("RGB", img.size, BG)
    img.paste(bg, (0, 0), Image.eval(mask, lambda v: 255 - v))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=radius,
                                          outline=border, width=2)


def draw_weather_card(img: Image.Image, w, step: int = 0, place: str | None = None,
                      allowed: list[str] | None = None, info: bool = True) -> None:
    """Scène du jour en fond, météo du moment au centre (icône + condition + température)."""
    from . import places, scenes as sc
    c = sc.Ctx(w, step)
    sc.draw_sky(img, c)
    sc.draw_sun(img, c)
    sc.draw_moon_stars(img, c)
    sc.draw_clouds(img, c)
    sc.draw_birds(img, c)

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    places.PLACES[place or places.pick_place(w, allowed)](c, ImageDraw.Draw(layer, "RGBA"))
    layer = sc.tint_layer(layer, c)
    img.paste(layer, (0, 0), layer)

    sc.draw_fog(img, c)
    sc.draw_rain(img, c)
    sc.draw_snow(img, c)
    sc.draw_glows(img, c)
    sc.draw_lightning(img, c)
    if not info:                       # vignette de galerie : scène seule
        _rounded_clip(img)
        return

    d = ImageDraw.Draw(img)
    outline = (10, 14, 30)
    _txt(d, (120 - d.textlength(w.city.upper(), font=font(8)) / 2, 7), w.city.upper(), font(8),
         (236, 240, 250), stroke=1, stroke_fill=outline)
    icon = sprites.weather_icon(w.icon, size=3)                      # 36x36
    shadow = sprites.weather_icon(w.icon, size=3)
    img.paste(Image.new("RGBA", icon.size, (0, 0, 0, 90)), (120 - icon.width // 2 + 2, 20 + 2), shadow)
    img.paste(icon, (120 - icon.width // 2, 20), icon)
    cond = i18n.condition(w.icon)
    _txt(d, (120 - d.textlength(cond, font=font(10)) / 2, 62), cond, font(10), (255, 255, 255),
         stroke=2, stroke_fill=outline)
    temp = f"{w.temp:.0f}°"
    ft = font(40)
    _txt(d, (120 - d.textlength(temp, font=ft) / 2, 78), temp, ft, (255, 255, 255), stroke=3,
         stroke_fill=outline)
    _rounded_clip(img)


# Horloge HTC Sense : voir clock_sense.py
from .clock_sense import draw_clock_card  # noqa: E402,F401
