"""Moteur de scènes pixel art pour la card météo (240x240, boucle N frames).

Rendu par couches : ciel (phase du jour x météo) -> astres/nuages -> scène
(lieu du jour, acteurs animés) -> teinte lumière -> particules (pluie, neige,
brouillard) -> lueurs nocturnes -> éclair.

Toutes les animations bouclent proprement sur N frames (sinus, ping-pong,
défilement modulo), sans à-coup au redémarrage du GIF.
"""

from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

N = 24                 # frames par boucle
W = H = 240
HORIZON = 128

Color = tuple[int, int, int]


# ------------------------------------------------------------------ outils

def mix(a: Color, b: Color, t: float) -> Color:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))  # type: ignore[return-value]


def shade(c: Color, f: float) -> Color:
    return tuple(max(0, min(255, round(v * f))) for v in c)  # type: ignore[return-value]


def tri(u: float) -> float:
    """Onde triangulaire 0..1..0 sur une période de 1 (ping-pong)."""
    u %= 1.0
    return 1 - abs(2 * u - 1)


def R(d: ImageDraw.ImageDraw, x0, y0, x1, y1, c) -> None:
    x0, x1 = sorted((round(x0), round(x1)))
    y0, y1 = sorted((round(y0), round(y1)))
    d.rectangle([x0, y0, x1, y1], fill=c)


def P(d: ImageDraw.ImageDraw, x, y, c) -> None:
    d.point((round(x), round(y)), fill=c)


def gradient(d: ImageDraw.ImageDraw, y0: int, y1: int, top: Color, bot: Color,
             bands: int = 24, x0: int = 0, x1: int = W - 1) -> None:
    h = y1 - y0
    for i in range(bands):
        c = mix(top, bot, i / max(bands - 1, 1))
        ya = y0 + round(h * i / bands)
        yb = y0 + round(h * (i + 1) / bands)
        d.rectangle([x0, ya, x1, max(ya, yb - 1)], fill=c)


# ----------------------------------------------------------------- contexte

class Ctx:
    """État partagé d'un rendu de frame."""

    def __init__(self, w, step: int) -> None:
        self.w = w
        self.step = step
        self.t = step / N                       # 0..1 sur la boucle
        self.phase = w.phase
        self.icon = w.icon
        self.hour = w.hour
        self.season = w.season
        self.temp = w.temp
        self.night = w.phase == "NUIT"
        self.dusk = w.phase in ("CREPUSCULE", "AURORE")
        self.rain = w.icon in ("RAIN", "STORM")
        self.snow = w.icon == "SNOW"
        self.fog = w.icon == "FOG"
        self.cold = w.temp < 10
        self.hot = w.temp >= 24
        self.glows: list[tuple[int, int, int, Color, int]] = []
        self.sky_bot = SKY_TOP_BOT[w.phase][1]
        self.seed = w.year * 400 + w.doy
        self.rng = random.Random(self.seed)

    def sin(self, phase: float = 0.0, k: int = 1) -> float:
        return math.sin(2 * math.pi * (self.t * k + phase))

    def glow(self, x, y, r, col: Color, a: int = 60) -> None:
        self.glows.append((round(x), round(y), r, col, a))


# --------------------------------------------------------------------- ciel

SKY_TOP_BOT = {
    "AURORE":     ((74, 76, 140), (255, 176, 124)),
    "MATIN":      ((72, 152, 228), (196, 228, 250)),
    "JOURNEE":    ((72, 152, 228), (196, 228, 250)),
    "APRES-MIDI": ((52, 132, 222), (176, 218, 248)),
    "CREPUSCULE": ((70, 54, 128), (255, 132, 98)),
    "NUIT":       ((8, 12, 38), (34, 46, 96)),
}
# teinte appliquée à la scène (couleur, force)
SCENE_TINT = {
    "AURORE": ((255, 150, 110), 0.18),
    "MATIN": ((255, 236, 200), 0.06),
    "JOURNEE": ((255, 255, 255), 0.0),
    "APRES-MIDI": ((255, 244, 214), 0.05),
    "CREPUSCULE": ((255, 96, 90), 0.24),
    "NUIT": ((14, 20, 62), 0.58),
}


def sky_colors(c: Ctx) -> tuple[Color, Color]:
    top, bot = SKY_TOP_BOT[c.phase]
    grey = {"CLOUD": ((120, 128, 144), 0.45), "RAIN": ((78, 86, 102), 0.62),
            "STORM": ((46, 50, 66), 0.72), "SNOW": ((176, 184, 198), 0.5),
            "FOG": ((170, 176, 184), 0.62), "PARTLY": ((130, 140, 156), 0.14)}.get(c.icon)
    if grey:
        g, k = grey
        if c.night:
            g = shade(g, 0.25)
        top, bot = mix(top, g, k), mix(bot, g, k)
    return top, bot


def draw_sky(img: Image.Image, c: Ctx) -> None:
    d = ImageDraw.Draw(img)
    top, bot = sky_colors(c)
    c.sky_bot = bot
    gradient(d, 0, 170, top, bot, bands=34)


def _disc(d, cx, cy, r, col: Color) -> None:
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)


def draw_sun(img: Image.Image, c: Ctx) -> None:
    if c.night or c.icon in ("CLOUD", "RAIN", "STORM", "SNOW", "FOG"):
        return
    t = min(max((c.hour - 6) / 14, 0), 1)
    cx = round(24 + t * 192)
    cy = round(112 - math.sin(math.pi * t) * 84)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    low = c.dusk
    core = (255, 232, 150) if not low else (255, 190, 110)
    for r, a in ((34, 26), (26, 40), (20, 64)):
        _disc(od, cx, cy, r, (*core, a))
    img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"))
    d = ImageDraw.Draw(img)
    pulse = 1 if c.step % 12 < 6 else 0
    _disc(d, cx, cy, 12 + pulse // 1 * 0, mix(core, (255, 255, 255), 0.15))
    _disc(d, cx, cy, 9, mix(core, (255, 255, 255), 0.45))
    # rayons qui tournent doucement
    for k in range(12):
        ang = 2 * math.pi * (k / 12 + c.t / 12)
        r0, r1 = 16, 22 if k % 2 else 19
        d.line([(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0),
                (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1)], fill=core, width=1)


def draw_moon_stars(img: Image.Image, c: Ctx) -> None:
    if not c.night:
        return
    d = ImageDraw.Draw(img)
    overcast = c.icon in ("CLOUD", "RAIN", "STORM", "SNOW", "FOG")
    if not overcast:
        rng = random.Random(7)
        for i in range(34):
            x, y = rng.randint(4, 235), rng.randint(2, 110)
            tw = (c.step + i * 5) % 12
            col = (235, 238, 255) if tw > 2 else (110, 120, 170)
            P(d, x, y, col)
            if i % 7 == 0 and tw > 6:
                P(d, x + 1, y, (150, 160, 215)); P(d, x - 1, y, (150, 160, 215))
                P(d, x, y + 1, (150, 160, 215)); P(d, x, y - 1, (150, 160, 215))
        h = c.hour if c.hour >= 20 else c.hour + 24
        t = min(max((h - 20) / 10, 0), 1)
        cx = round(30 + t * 180)
        cy = round(100 - math.sin(math.pi * t) * 66)
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for r, a in ((28, 22), (20, 38)):
            _disc(od, cx, cy, r, (200, 214, 255, a))
        img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"))
        d = ImageDraw.Draw(img)
        _disc(d, cx, cy, 11, (232, 236, 250))
        _disc(d, cx + 5, cy - 3, 9, mix(sky_colors(c)[0], (8, 12, 38), 0.2))   # croissant
        _disc(d, cx - 3, cy + 3, 2, (206, 212, 232))


def _cloud(d, x, y, w, col: Color, sh: Color) -> None:
    """Nuage en grappe de disques ; ombre dessous."""
    h = max(6, w // 3)
    lumps = [(0.25, 0.62, 0.20), (0.45, 0.42, 0.27), (0.68, 0.55, 0.22), (0.85, 0.68, 0.15), (0.12, 0.74, 0.12)]
    for fx, fy, fr in lumps:
        r = max(3, round(w * fr))
        _disc(d, round(x + w * fx), round(y + h * fy) + 2, r, sh)
    for fx, fy, fr in lumps:
        r = max(3, round(w * fr))
        _disc(d, round(x + w * fx), round(y + h * fy), r, col)
    R(d, x + w * 0.1, y + h * 0.82, x + w * 0.92, y + h * 1.1, col)


def draw_clouds(img: Image.Image, c: Ctx) -> None:
    count = {"SUN": 1, "MOON": 1, "PARTLY": 4, "CLOUD": 7, "RAIN": 7, "STORM": 7,
             "SNOW": 7, "FOG": 3}.get(c.icon, 2)
    d = ImageDraw.Draw(img)
    if c.icon in ("STORM",):
        col, sh = (96, 100, 118), (66, 70, 88)
    elif c.icon == "RAIN":
        col, sh = (150, 158, 174), (112, 120, 140)
    elif c.icon == "SNOW":
        col, sh = (226, 232, 244), (182, 190, 208)
    else:
        col, sh = (252, 253, 255), (206, 216, 234)
    if c.night:
        col, sh = shade(col, 0.34), shade(sh, 0.3)
    col = mix(col, c.sky_bot, 0.28 if c.dusk else 0.0)
    sh = mix(sh, c.sky_bot, 0.28 if c.dusk else 0.0)
    rng = random.Random(c.seed % 997 + 3)
    for i in range(count):
        w = rng.randint(44, 84) if c.icon in ("CLOUD", "RAIN", "STORM", "SNOW") else rng.randint(34, 62)
        x0 = rng.randint(-10, 200)
        y0 = rng.randint(2, 82)
        x = x0 + 5 * math.sin(2 * math.pi * (c.t + i * 0.23))
        _cloud(d, x, y0, w, col, sh)


def draw_birds(img: Image.Image, c: Ctx) -> None:
    if c.night or c.rain or c.snow or c.fog:
        return
    d = ImageDraw.Draw(img)
    rng = random.Random(c.seed % 313)
    for i in range(rng.randint(2, 4)):
        span = W + 60
        x = (rng.randint(0, span) + c.step * span / N) % span - 30
        y = rng.randint(70, 118) + 3 * math.sin(2 * math.pi * (c.t * 2 + i * 0.3))
        up = (c.step // 2 + i) % 2
        col = (50, 56, 76)
        for k in (-1, 1):
            P(d, x + k, y - up, col); P(d, x + 2 * k, y - up * 2 + 1 if up else y, col)
        P(d, x, y + 1, col)


# ------------------------------------------------------------- particules

def draw_rain(img: Image.Image, c: Ctx) -> None:
    if not c.rain:
        return
    d = ImageDraw.Draw(img)
    rng = random.Random(21)
    tile = N * 8
    heavy = c.icon == "STORM" or c.w.code in (65, 82)
    drops = 70 if heavy else 46
    col = (176, 200, 236) if not c.night else (120, 140, 190)
    for _ in range(drops):
        x0, y0 = rng.randint(-20, 255), rng.randint(0, tile - 1)
        for j in range(-1, 3):
            y = (y0 + c.step * 8) % tile + tile * j
            if 0 <= y < 232:
                xx = x0 - round(y * 0.18)
                d.line([(xx, y), (xx - 1, y + 4)], fill=col, width=1)
        # éclaboussure au sol
    for k in range(10):
        gx = rng.randint(6, 234)
        gy = rng.randint(198, 236)
        if (c.step + k * 3) % 8 < 2:
            P(d, gx - 1, gy, (200, 216, 240)); P(d, gx + 1, gy, (200, 216, 240)); P(d, gx, gy - 1, (225, 235, 250))


def draw_snow(img: Image.Image, c: Ctx) -> None:
    if not c.snow:
        return
    d = ImageDraw.Draw(img)
    rng = random.Random(33)
    tile = N * 3
    for i in range(60):
        x0, y0 = rng.randint(0, 239), rng.randint(0, tile - 1)
        big = i % 5 == 0
        for j in range(0, 4):
            y = (y0 + c.step * 3) % tile + tile * (j - 1)
            if 0 <= y < 236:
                x = x0 + 2 * math.sin(2 * math.pi * (c.t + i * 0.13))
                col = (255, 255, 255) if big else (226, 234, 248)
                P(d, x, y, col)
                if big:
                    P(d, x + 1, y, col); P(d, x, y + 1, col)


def draw_fog(img: Image.Image, c: Ctx) -> None:
    if not c.fog:
        return
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    base = (214, 218, 226) if not c.night else (70, 78, 104)
    for i, y in enumerate(range(96, 232, 17)):
        off = 12 * math.sin(2 * math.pi * (c.t + i * 0.19))
        for x in range(-30, 270, 38):
            od.ellipse([x + off, y, x + off + 70, y + 20], fill=(*base, 46))
    img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"))


def draw_lightning(img: Image.Image, c: Ctx) -> None:
    if c.icon != "STORM" or c.step not in (7, 8, 15):
        return
    d = ImageDraw.Draw(img)
    if c.step in (7, 15):
        ov = Image.new("RGBA", img.size, (235, 240, 255, 60))
        img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"))
        d = ImageDraw.Draw(img)
    x = 176 if c.step != 15 else 54
    pts = [(x, 60), (x - 6, 92), (x + 2, 94), (x - 10, 132), (x - 2, 134), (x - 14, 170)]
    d.line(pts, fill=(255, 250, 200), width=2)
    d.line(pts, fill=(255, 255, 255), width=1)


def draw_glows(img: Image.Image, c: Ctx) -> None:
    if not c.glows or not (c.night or c.dusk or c.rain or c.fog):
        return
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    strength = 1.0 if c.night else 0.55
    for x, y, r, col, a in c.glows:
        for k in range(4):
            rr = round(r * (1 - k * 0.22))
            od.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(*col, round(a * strength * (0.5 + k * 0.28))))
    img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"))


# ----------------------------------------------------------- sprites vivants

SKINS = [(246, 208, 170), (232, 184, 140), (200, 146, 106), (150, 100, 70), (255, 224, 196)]
HAIRS = [(46, 34, 28), (92, 58, 34), (200, 160, 70), (30, 28, 34), (170, 74, 44), (206, 206, 214)]
TOPS = [(220, 70, 70), (70, 130, 220), (240, 190, 60), (90, 180, 110), (236, 236, 242),
        (180, 90, 200), (255, 140, 60), (60, 170, 180)]
BOTS = [(52, 64, 110), (60, 56, 70), (120, 100, 78), (40, 80, 90), (150, 70, 70)]


def _rmap(d, x, y, s, dirn):
    def r(x0, y0, x1, y1, col):
        if dirn < 0:
            x0, x1 = -x1, -x0
        ax = x + round(x0 * s)
        ay = y + round(y0 * s)
        bx = ax + max(1, round((x1 - x0 + 1) * s)) - 1
        by = ay + max(1, round((y1 - y0 + 1) * s)) - 1
        d.rectangle([ax, ay, bx, by], fill=col)
    return r


def person(d, x, y, step, *, s=1.0, dirn=1, skin=SKINS[0], hair=HAIRS[0], top=TOPS[0],
           bot=BOTS[0], walk=True, umbrella=None, skirt=False, scarf=None, long_hair=False,
           hat=None, arms_up=False, bun=False) -> None:
    """Personnage ~14 px (s=1) : 4 frames de marche, ombre portée, accessoires."""
    r = _rmap(d, x, y, s, dirn)
    ph = (step // 2) % 4 if walk else 1
    swing = (-1, 0, 1, 0)[ph]
    bob = 1 if (walk and ph in (0, 2)) else 0
    # ombre portée
    d.ellipse([x - round(4 * s), y - 1, x + round(4 * s), y + 1], fill=(0, 0, 0, 70))
    # jambes
    legc = bot
    if skirt:
        r(-3, -6 - bob, 3, -3 - bob, bot)
        r(-1, -2 - bob, 0, 0, skin); r(1, -2 - bob, 2, 0, skin)
    else:
        r(-2 + swing, -5, -1 + swing, -1, legc)
        r(1 - swing, -5, 2 - swing, -1, shade(legc, 0.82))
    r(-2 + swing, 0, -1 + swing + 1, 0, (32, 30, 36)); r(1 - swing, 0, 2 - swing + 1, 0, (32, 30, 36))
    # torse
    r(-2, -10 - bob, 2, -5 - bob, top)
    r(-2, -10 - bob, 2, -10 - bob, shade(top, 1.18))
    r(2, -9 - bob, 2, -6 - bob, shade(top, 0.8))
    # bras
    if arms_up:
        r(3, -13 - bob, 3, -9 - bob, skin); r(-3, -13 - bob, -3, -9 - bob, skin)
    else:
        r(3 + (swing > 0), -9 - bob, 3 + (swing > 0), -6 - bob, shade(top, 0.9))
        r(-3 - (swing < 0), -9 - bob, -3 - (swing < 0), -6 - bob, shade(top, 0.9))
        r(3, -5 - bob, 3, -5 - bob, skin); r(-3, -5 - bob, -3, -5 - bob, skin)
    if scarf:
        r(-2, -11 - bob, 2, -11 - bob, scarf); r(-3, -10 - bob, -3, -8 - bob, scarf)
    # tête
    r(-2, -14 - bob, 1, -11 - bob, skin)
    r(-2, -15 - bob, 1, -14 - bob, hair)
    r(-2, -13 - bob, -2, -12 - bob, hair)
    if long_hair:
        r(-3, -14 - bob, -2, -9 - bob, hair)
    if bun:
        r(-3, -16 - bob, -1, -15 - bob, hair)
    r(1, -12 - bob, 1, -12 - bob, (30, 24, 28))
    if hat:
        r(-3, -15 - bob, 2, -14 - bob, hat); r(-2, -17 - bob, 1, -16 - bob, hat)
    if umbrella:
        dome = umbrella
        r(-6, -21 - bob, 6, -19 - bob, dome)
        r(-4, -23 - bob, 4, -22 - bob, dome)
        r(-6, -18 - bob, -5, -18 - bob, dome); r(5, -18 - bob, 6, -18 - bob, dome)
        r(-1, -21 - bob, 0, -21 - bob, shade(dome, 1.3))
        r(0, -19 - bob, 0, -11 - bob, (60, 52, 50))


def dog(d, x, y, step, *, s=1.0, dirn=1, col=(176, 120, 70), ear=(110, 70, 40)) -> None:
    r = _rmap(d, x, y, s, dirn)
    ph = (step // 2) % 2
    d.ellipse([x - round(5 * s), y - 1, x + round(5 * s), y + 1], fill=(0, 0, 0, 70))
    r(-4, -5, 2, -3, col)
    r(-4, -5, 2, -5, shade(col, 1.2))
    r(3, -7, 5, -4, col)
    r(5, -5, 6, -4, shade(col, 0.75))
    r(4, -8, 4, -6, ear)
    r(4, -6, 4, -6, (24, 20, 22))
    r(-5, -7 + ph, -5, -5 + ph, shade(col, 0.9))
    for lx, sw in ((-4, ph), (-3, 1 - ph), (1, 1 - ph), (2, ph)):
        r(lx + sw, -2, lx + sw, -1, shade(col, 0.8))


def car(d, c: Ctx, x, yb, w, col: Color, dirn=1) -> None:
    h = max(6, round(w * 0.30))
    ch = max(3, round(w * 0.20))
    d.ellipse([x + 1, yb - 1, x + w - 2, yb + 2], fill=(0, 0, 0, 80))
    R(d, x, yb - h, x + w - 1, yb - 2, col)
    R(d, x, yb - h, x + w - 1, yb - h, shade(col, 1.25))
    R(d, x, yb - 3, x + w - 1, yb - 2, shade(col, 0.72))
    cx0, cx1 = x + round(w * 0.22), x + w - 1 - round(w * 0.2)
    R(d, cx0, yb - h - ch, cx1, yb - h, shade(col, 0.95))
    R(d, cx0 + 1, yb - h - ch + 1, cx1 - 1, yb - h - 1, (150, 200, 228))
    mid = (cx0 + cx1) // 2
    R(d, mid, yb - h - ch + 1, mid, yb - h - 1, shade(col, 0.9))
    R(d, cx0 + 1, yb - h - ch + 1, cx0 + 2, yb - h - ch + 1, (225, 242, 252))
    wr = max(2, round(w * 0.075))
    for wx in (x + round(w * 0.24), x + round(w * 0.78)):
        d.ellipse([wx - wr, yb - wr * 2, wx + wr, yb], fill=(24, 24, 30))
        P(d, wx, yb - wr, (140, 142, 152))
    front = x + w - 1 if dirn > 0 else x
    rear = x if dirn > 0 else x + w - 1
    R(d, front - (1 if dirn > 0 else 0), yb - h + 2, front - (0 if dirn > 0 else -1), yb - h + 3, (255, 240, 170))
    R(d, rear, yb - h + 2, rear, yb - h + 3, (220, 50, 50))
    if c.night or c.rain or c.dusk:
        c.glow(front + dirn * 6, yb - h + 3, 9, (255, 236, 160), 70)


def tree(d, c: Ctx, x, base, h, kind="round", sway=0.0, leaf: Color | None = None) -> None:
    """Arbre : feuillu (saison) ou sapin."""
    sx = round(sway)
    if kind == "pine":
        col = leaf or (36, 92, 66)
        R(d, x - 1, base - 4, x + 1, base, (84, 58, 38))
        tiers = max(3, h // 7)
        for i in range(tiers):
            ty = base - 4 - round(i * (h - 8) / tiers)
            wdt = round((h * 0.34) * (1 - i / (tiers + 0.6)))
            d.polygon([(x - wdt + sx * i // max(tiers, 1), ty), (x + wdt + sx * i // max(tiers, 1), ty),
                       (x + sx * (i + 1) // max(tiers, 1), ty - round(h / tiers) - 3)],
                      fill=shade(col, 1.0 + 0.1 * (i % 2)))
            d.line([(x - wdt + sx * i // max(tiers, 1), ty), (x + sx * (i + 1) // max(tiers, 1), ty - round(h / tiers) - 3)],
                   fill=shade(col, 1.3))
            if c.snow or (c.season == "WINTER" and c.temp < 3):
                d.line([(x - wdt + 2 + sx * i // max(tiers, 1), ty - 1), (x + wdt - 2 + sx * i // max(tiers, 1), ty - 1)],
                       fill=(240, 246, 255))
        return
    base_leaf = leaf or {"SPRING": (112, 190, 92), "SUMMER": (54, 148, 70), "AUTUMN": (214, 124, 40),
                         "WINTER": (92, 108, 92)}[c.season]
    trunk = (96, 66, 42)
    R(d, x - 1, base - round(h * 0.5), x + 1, base, trunk)
    R(d, x + 1, base - round(h * 0.5), x + 1, base, shade(trunk, 0.7))
    ty = base - round(h * 0.55)
    if c.season == "WINTER" and not c.snow:
        for dx, dy in ((-5, -9), (5, -10), (0, -14), (-8, -4), (8, -5)):
            d.line([(x, ty), (x + dx + sx, ty + dy)], fill=trunk, width=1)
        return
    r0 = round(h * 0.34)
    for dx, dy, rr in ((-r0 // 2, 0, r0 * 0.8), (r0 // 2, 1, r0 * 0.8), (0, -r0 * 0.55, r0 * 0.9), (0, 2, r0 * 0.7)):
        rr = round(rr)
        d.ellipse([x + dx - rr + sx, ty + dy - rr, x + dx + rr + sx, ty + dy + rr], fill=shade(base_leaf, 0.82))
    for dx, dy, rr in ((-r0 // 2, -1, r0 * 0.62), (r0 // 2, 0, r0 * 0.62), (0, -r0 * 0.6, r0 * 0.7)):
        rr = round(rr)
        d.ellipse([x + dx - rr + sx, ty + dy - rr - 1, x + dx + rr + sx, ty + dy + rr - 1], fill=base_leaf)
    rng = random.Random(x * 31 + base)
    for _ in range(max(4, r0)):
        px = x + rng.randint(-r0, r0) + sx
        py = ty + rng.randint(-r0, r0 // 2)
        P(d, px, py, shade(base_leaf, 1.28))
    if c.season == "SPRING":
        for _ in range(r0):
            P(d, x + rng.randint(-r0, r0) + sx, ty + rng.randint(-r0, r0 // 2), (255, 190, 214))
    if c.snow:
        for dx in range(-r0, r0 + 1, 2):
            P(d, x + dx + sx, ty - r0 + abs(dx) // 3 - 1, (244, 248, 255))


def tint_layer(layer: Image.Image, c: Ctx) -> Image.Image:
    """Teinte lumière/météo appliquée à la couche scène (alpha préservé)."""
    alpha = layer.getchannel("A")
    rgb = layer.convert("RGB")
    col, k = SCENE_TINT[c.phase]
    if k:
        rgb = Image.blend(rgb, Image.new("RGB", rgb.size, col), k)
    if c.rain or c.icon == "CLOUD":
        g = (96, 104, 120) if c.icon != "CLOUD" else (140, 146, 158)
        rgb = Image.blend(rgb, Image.new("RGB", rgb.size, g), 0.26 if c.rain else 0.14)
    if c.icon == "STORM":
        rgb = Image.blend(rgb, Image.new("RGB", rgb.size, (40, 44, 60)), 0.2)
    if c.snow:
        rgb = Image.blend(rgb, Image.new("RGB", rgb.size, (232, 238, 250)), 0.3)
    if c.fog:
        rgb = Image.blend(rgb, Image.new("RGB", rgb.size, (190, 196, 206)), 0.4)
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out
