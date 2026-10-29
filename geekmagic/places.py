"""Lieux de la card météo : ville, plage, lac (pêcheur), parc (grand-mère + chien).

Chaque lieu dessine, sur la couche scène RGBA, un décor en perspective (plans
lointain -> proche) et des acteurs animés. Le lieu change chaque jour
(rotation sur le jour de l'année) et la graine du jour varie couleurs,
silhouettes, nombre d'acteurs : plus de 30 jours tous différents.
"""

from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

from .scenes import (HAIRS, SKINS, TOPS, BOTS, H, HORIZON, N, W, Color, Ctx, P, R, car,
                     dog, gradient, mix, person, shade, tree, tri)

LIT = (255, 214, 112)
GLASS = (126, 168, 204)


# ------------------------------------------------------------------ utilitaires

def _pick(rng: random.Random, seq):
    return seq[rng.randrange(len(seq))]


def _person_kw(c: Ctx, rng: random.Random, umbrella_ok: bool = True) -> dict:
    kw = dict(skin=_pick(rng, SKINS), hair=_pick(rng, HAIRS),
              top=_pick(rng, TOPS), bot=_pick(rng, BOTS))
    if c.cold:
        kw["top"] = _pick(rng, [(70, 74, 96), (120, 52, 60), (60, 90, 70), (96, 80, 66)])
        kw["scarf"] = _pick(rng, [(230, 80, 70), (240, 200, 70), (240, 240, 244)])
    if c.rain and umbrella_ok:
        kw["umbrella"] = _pick(rng, [(230, 70, 80), (70, 120, 230), (250, 200, 60), (90, 190, 120), (170, 90, 210)])
    return kw


def _pace(c: Ctx, lo: float, hi: float, phase: float) -> tuple[float, int]:
    u = c.t + phase
    return lo + (hi - lo) * tri(u), (1 if (u % 1.0) < 0.5 else -1)


# ------------------------------------------------------------------ VILLE

def place_city(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    rng = c.rng
    haze = c.sky_bot
    facades = _pick(rng, [
        [(226, 186, 142), (196, 122, 108), (156, 176, 200), (236, 214, 168), (170, 150, 190)],
        [(204, 108, 92), (232, 200, 150), (120, 150, 170), (196, 176, 140), (150, 110, 100)],
        [(150, 180, 150), (236, 208, 160), (200, 130, 120), (170, 170, 200), (226, 190, 130)],
    ])
    # skyline lointaine (brume)
    far = mix((104, 118, 156), haze, 0.5)
    x = -6
    while x < W:
        w, top = rng.randint(12, 24), rng.randint(112, 128)
        R(d, x, top, x + w, 156, far)
        R(d, x, top, x + w, top, shade(far, 1.12))
        for wy in range(top + 4, 150, 6):
            for wx in range(x + 3, x + w - 2, 5):
                if rng.random() < 0.4:
                    P(d, wx, wy, mix(far, LIT if c.night else (190, 205, 230), 0.55))
        if rng.random() < 0.3:
            R(d, x + w // 2, top - 6, x + w // 2, top, shade(far, 0.8))
        x += w + rng.randint(0, 3)
    # immeubles du plan moyen
    base = 170
    x = -8
    shops = []
    while x < W:
        w, h = rng.randint(30, 46), rng.randint(40, 58)
        col = _pick(rng, facades)
        top = base - h
        R(d, x, top, x + w - 1, base, col)
        R(d, x + w - 5, top, x + w - 1, base, shade(col, 0.82))
        R(d, x, top - 3, x + w - 1, top, shade(col, 1.2))
        R(d, x, top, x + w - 1, top, shade(col, 0.7))
        if rng.random() < 0.5:                                     # souche de cheminée / clim
            R(d, x + 5, top - 7, x + 8, top - 3, shade(col, 0.7))
        for wy in range(top + 6, base - 16, 10):
            for wx in range(x + 4, x + w - 9, 8):
                lit = rng.random() < (0.62 if c.night or c.dusk else 0.1)
                if lit:
                    R(d, wx, wy, wx + 4, wy + 5, LIT)
                    c.glow(wx + 2, wy + 3, 7, (255, 200, 110), 28)
                else:
                    R(d, wx, wy, wx + 4, wy + 5, GLASS)
                    R(d, wx, wy, wx + 1, wy + 1, (214, 232, 248))
                R(d, wx - 1, wy + 6, wx + 5, wy + 6, shade(col, 0.7))      # appui
        shops.append((x, w, col))
        x += w
    # rez-de-chaussée : auvents, vitrines, portes
    for (x, w, col) in shops:
        aw = _pick(rng, [(220, 60, 60), (60, 140, 90), (60, 100, 190), (240, 170, 50)])
        R(d, x, 154, x + w - 1, base, shade(col, 0.9))
        for sx in range(x, x + w - 6, 4):
            R(d, sx, 154, sx + 1, 159, aw)
            R(d, sx + 2, 154, sx + 3, 159, (246, 242, 232))
        R(d, x, 160, x + w - 1, 160, shade(aw, 0.6))
        R(d, x + 3, 162, x + w // 2, base - 1, GLASS if not (c.night or c.dusk) else LIT)
        R(d, x + w // 2 + 3, 162, x + w // 2 + 8, base, (86, 60, 44))
        if c.night or c.dusk:
            c.glow(x + w // 4 + 3, 166, 14, (255, 210, 120), 40)
    # trottoir éloigné, bordure, chaussée
    R(d, 0, base, W, 177, (176, 176, 186))
    R(d, 0, base, W, base, (206, 206, 214))
    R(d, 0, 178, W, 179, (120, 120, 132))
    R(d, 0, 180, W, 216, (66, 68, 80))
    for dx in range(0, W, 24):
        R(d, dx + 4, 198, dx + 15, 199, (226, 224, 206))
    R(d, 0, 217, W, 218, (140, 140, 152))
    R(d, 0, 219, W, 239, (158, 158, 170))
    for dx in range(0, W, 20):
        R(d, dx, 219, dx, 239, (146, 146, 158))
    for dy in (228, 236):
        R(d, 0, dy, W, dy, (146, 146, 158))
    # réverbères
    for lx in (34, 118, 202):
        R(d, lx, 132, lx, 176, (58, 60, 72))
        R(d, lx - 4, 132, lx, 132, (58, 60, 72))
        R(d, lx - 7, 131, lx - 4, 134, LIT if (c.night or c.dusk) else (214, 214, 222))
        c.glow(lx - 5, 136, 18, (255, 226, 150), 70)
    # voitures (défilement modulo = boucle parfaite)
    palette = [(214, 60, 60), (60, 120, 220), (240, 200, 60), (236, 236, 240), (70, 70, 80), (60, 170, 110), (240, 140, 60)]
    span = W + 90
    for i in range(3):                       # voie éloignée -> droite
        x0 = rng.randint(0, span)
        cx = (x0 + c.step * span / N) % span - 50
        car(d, c, round(cx), 192, 22, _pick(rng, palette), 1)
    for i in range(3):                       # voie proche -> gauche
        x0 = rng.randint(0, span)
        cx = (x0 - c.step * span / N) % span - 50
        car(d, c, round(cx), 214, 32, _pick(rng, palette), -1)
    # piétons
    for (lo, hi, y, s, ph) in ((30, 90, 177, 0.8, 0.0), (130, 190, 177, 0.8, 0.45)):
        x, dirn = _pace(c, lo, hi, ph)
        person(d, round(x), y, c.step + int(ph * 8), s=s, dirn=dirn, **_person_kw(c, rng))
    x, dirn = _pace(c, 40, 110, 0.15)                     # couple au premier plan
    kw1, kw2 = _person_kw(c, rng), _person_kw(c, rng)
    person(d, round(x), 237, c.step, s=1.55, dirn=dirn, **kw1)
    person(d, round(x) - dirn * 12, 237, c.step + 1, s=1.45, dirn=dirn, **kw2)
    x, dirn = _pace(c, 150, 215, 0.6)
    person(d, round(x), 236, c.step, s=1.5, dirn=dirn, **_person_kw(c, rng))


# ------------------------------------------------------------------ PLAGE

def _lying(d, c: Ctx, x, y, towel, skin, suit, hair) -> None:
    R(d, x, y, x + 23, y + 8, towel)
    for sx in range(x, x + 23, 4):
        R(d, sx, y, sx + 1, y + 8, shade(towel, 1.12))
    rise = 1 if c.sin() > 0 else 0
    R(d, x + 2, y + 1, x + 6, y + 5, skin)
    R(d, x + 2, y + 1, x + 3, y + 5, hair)
    P(d, x + 5, y + 3, (26, 26, 32))
    R(d, x + 7, y + 1 - rise, x + 12, y + 5, suit)
    R(d, x + 13, y + 2, x + 21, y + 4, skin)
    R(d, x + 20, y + 2, x + 22, y + 4, shade(skin, 0.85))


def _parasol(d, x, y, h, c1, c2) -> None:
    R(d, x, y - h, x, y, (230, 230, 232))
    r = 17
    for i in range(-r, r + 1):
        top = y - h - round(math.sqrt(max(r * r - i * i, 0)) * 0.45)
        col = c1 if ((i + r) // 5) % 2 == 0 else c2
        R(d, x + i, top, x + i, y - h + 2, col)
    R(d, x - r, y - h + 2, x + r, y - h + 3, shade(c1, 0.7))


def place_beach(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    rng = c.rng
    sky = c.sky_bot
    # falaise lointaine sur l'horizon
    cliff = mix((98, 140, 128), sky, 0.45)
    pts = [(0, 126)] + [(x, 126 - round(11 * max(0, math.sin(x / 38.0 + rng.random() * 0.1)))) for x in range(0, 110, 6)] + [(110, 126)]
    d.polygon(pts, fill=cliff)
    # mer : dégradé horizon -> rivage
    gradient(d, 126, 166, mix((150, 206, 232), sky, 0.25), (28, 124, 196), bands=14)
    for row, y in enumerate(range(130, 164, 4)):
        for k in range(8):
            x = (k * 31 + row * 17 + round(6 * math.sin(2 * math.pi * (c.t + row / 11)))) % (W + 20) - 10
            R(d, x, y, x + 4 + row // 2, y, mix((100, 180, 226), (214, 240, 252), 0.4 + 0.1 * (row % 3)))
    # voilier + cargo lointain
    bx = rng.randint(120, 190) + round(4 * c.sin())
    by = 135 + round(c.sin(0.25))
    R(d, bx - 8, by, bx + 8, by + 2, (244, 244, 248))
    R(d, bx - 8, by + 2, bx + 6, by + 3, (200, 60, 60))
    d.polygon([(bx + 1, by - 17), (bx + 1, by - 1), (bx + 10, by - 1)], fill=(250, 250, 252))
    d.polygon([(bx - 1, by - 13), (bx - 1, by - 1), (bx - 8, by - 1)], fill=(226, 232, 244))
    R(d, bx, by - 18, bx, by, (140, 120, 100))
    sx = 36
    R(d, sx, 128, sx + 14, 130, (70, 78, 94)); R(d, sx + 8, 125, sx + 12, 128, (214, 214, 222))
    # nageurs
    for i in range(3):
        sx = rng.randint(30, 210)
        sy = 146 + (i * 6) % 14
        b = round(1.2 * math.sin(2 * math.pi * (c.t + i * 0.3)))
        R(d, sx, sy + b, sx + 2, sy + 2 + b, _pick(rng, SKINS))
        R(d, sx, sy + b - 1, sx + 2, sy + b - 1, _pick(rng, HAIRS))
        if (c.step + i * 4) % 12 < 4:
            R(d, sx + 3, sy + b - 3, sx + 3, sy + b, _pick(rng, SKINS))
        R(d, sx - 2, sy + 3 + b, sx + 4, sy + 3 + b, (170, 220, 244))
    # écume + sable mouillé + sable sec
    for x in range(0, W, 2):
        yy = 166 + round(2.2 * math.sin(2 * math.pi * c.t + x / 15.0))
        R(d, x, yy - 1, x + 1, yy + 1, (240, 250, 252))
    R(d, 0, 169, W, 178, mix((214, 188, 136), (140, 110, 78), 0.25))
    gradient(d, 179, 240, (238, 216, 162), (222, 192, 134), bands=8)
    for _ in range(90):
        P(d, rng.randint(0, 239), rng.randint(181, 239), (206, 176, 120))
    for _ in range(10):
        x, y = rng.randint(4, 236), rng.randint(182, 236)
        P(d, x, y, (250, 236, 232)); P(d, x + 1, y, (246, 160, 150))
    # parasols + serviettes + baigneurs allongés
    cols = [(230, 70, 70), (70, 130, 230), (250, 200, 60), (80, 190, 130), (240, 140, 200)]
    c1, c2 = _pick(rng, cols), (248, 248, 250)
    _parasol(d, 46, 202, 36, c1, c2)
    _lying(d, c, 32, 197, _pick(rng, cols), _pick(rng, SKINS), _pick(rng, cols), _pick(rng, HAIRS))
    c3 = _pick(rng, cols)
    _parasol(d, 180, 222, 40, c3, c2)
    _lying(d, c, 164, 216, _pick(rng, cols), _pick(rng, SKINS), _pick(rng, cols), _pick(rng, HAIRS))
    _lying(d, c, 192, 229, _pick(rng, cols), _pick(rng, SKINS), _pick(rng, cols), _pick(rng, HAIRS))
    # château de sable
    R(d, 104, 205, 118, 211, (214, 184, 124)); R(d, 106, 201, 110, 205, (214, 184, 124)); R(d, 113, 201, 117, 205, (214, 184, 124))
    R(d, 108, 198, 108, 201, (240, 80, 80)); R(d, 109, 198, 111, 199, (240, 80, 80))
    # enfants + ballon (trajectoire en arche, boucle parfaite)
    k1, k2 = _person_kw(c, rng, False), _person_kw(c, rng, False)
    person(d, 82, 232, 0, s=1.2, dirn=1, walk=False, arms_up=(c.step % 12 < 5), **k1)
    person(d, 138, 232, 0, s=1.2, dirn=-1, walk=False, arms_up=(c.step % 12 > 5), **k2)
    bx = 110 - 26 * math.cos(2 * math.pi * c.t)
    by = 224 - 26 * abs(math.sin(2 * math.pi * c.t))
    d.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill=(244, 244, 248))
    d.pieslice([bx - 3, by - 3, bx + 3, by + 3], 30, 120, fill=(236, 64, 64))
    d.pieslice([bx - 3, by - 3, bx + 3, by + 3], 210, 300, fill=(66, 120, 230))
    # promeneur sur le rivage
    x, dirn = _pace(c, 70, 130, 0.3)
    person(d, round(x), 187, c.step, s=1.0, dirn=dirn, **_person_kw(c, rng, False))


# ------------------------------------------------------------------ LAC

def _ridge(rng, peaks: int, hmax: int) -> list[int]:
    hs = [0.0] * W
    for _ in range(peaks):
        cx, wd, ph = rng.randint(-10, W + 10), rng.randint(50, 100), rng.randint(hmax // 2, hmax)
        for x in range(W):
            v = ph * max(0.0, 1 - abs(x - cx) / wd)
            v += 2.2 * math.sin(x * 0.31 + cx) * (v / max(ph, 1))
            hs[x] = max(hs[x], v)
    return [round(v) for v in hs]


def place_lake(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    rng = c.rng
    sky = c.sky_bot
    base = 148
    water_top = mix(sky, (46, 112, 160), 0.55)
    water_bot = (24, 74, 116) if not c.night else (10, 22, 50)
    gradient(d, base, 206, water_top, water_bot, bands=16)
    # montagnes lointaines puis proches, reflets dans l'eau
    for hmax, col, snow in ((46, mix((120, 140, 178), sky, 0.45), True), (30, mix((70, 100, 120), sky, 0.2), False)):
        hs = _ridge(rng, 4, hmax)
        for x in range(W):
            h = hs[x]
            if h <= 0:
                continue
            top = base - h
            slope = (hs[x] - hs[max(x - 1, 0)])
            cc = shade(col, 0.82) if slope < 0 else shade(col, 1.08)
            d.line([(x, top), (x, base)], fill=cc)
            if snow and h > hmax * 0.68:
                d.line([(x, top), (x, top + max(2, (h - round(hmax * 0.68)) // 1))], fill=(244, 248, 255))
            ref = round(h * 0.65)
            for k in range(0, ref, 1):
                a = 0.38 * (1 - k / max(ref, 1))
                dx = round(2 * math.sin(2 * math.pi * (c.t + k / 9.0)))
                P(d, x + dx, base + 1 + k, mix(water_top, cc, a))
    # forêt de sapins sur la berge lointaine
    rng2 = random.Random(c.seed + 5)
    for x in range(-4, W, 9):
        hh = rng2.randint(12, 22)
        tree(d, c, x, base + 3, hh, "pine", sway=1.2 * c.sin(x / 60.0), leaf=shade((40, 98, 70), 0.9 if (x // 9) % 2 else 1.1))
    # miroitement
    for row in range(10):
        y = base + 8 + row * 6
        for k in range(6):
            x = (k * 43 + row * 29 + round(8 * math.sin(2 * math.pi * (c.t + row / 9)))) % (W + 20) - 10
            R(d, x, y, x + 3 + row // 2, y, mix(water_top, (226, 244, 252), 0.4))
    # berge au premier plan
    gradient(d, 206, 240, (86, 150, 78) if c.season != "AUTUMN" else (150, 140, 70), (60, 118, 62), bands=6)
    if c.snow or (c.season == "WINTER" and c.temp < 2):
        R(d, 0, 206, W, 240, (232, 238, 248))
    R(d, 0, 205, W, 206, shade((86, 150, 78), 0.7))
    # ponton en bois
    R(d, 0, 194, 112, 199, (160, 116, 76))
    R(d, 0, 194, 112, 194, (190, 142, 96))
    R(d, 0, 200, 112, 203, (110, 76, 50))
    for px in range(8, 112, 14):
        R(d, px, 194, px, 199, (120, 84, 56))
    for px in (6, 42, 78, 108):
        R(d, px, 203, px + 3, 216, (84, 58, 40))
        for k in range(3):
            R(d, px - 1 + k, 214 + k, px + 4 - k, 214 + k, mix(water_top, (200, 230, 244), 0.4))
    # pêcheur assis (chapeau de paille), seau, canne et bouchon
    fx, fy = 92, 194
    skin = SKINS[1]
    R(d, fx - 3, fy - 9, fx + 2, fy - 3, TOPS[1] if not c.cold else (96, 80, 66))
    R(d, fx - 3, fy - 9, fx + 2, fy - 9, shade(TOPS[1], 1.2))
    R(d, fx - 2, fy - 13, fx + 1, fy - 10, skin)
    R(d, fx - 4, fy - 14, fx + 2, fy - 14, (226, 196, 110)); R(d, fx - 2, fy - 16, fx + 0, fy - 15, (226, 196, 110))
    P(d, fx + 1, fy - 11, (30, 24, 28))
    R(d, fx - 3, fy - 3, fx + 3, fy - 1, BOTS[0])
    R(d, fx + 3, fy - 3, fx + 9, fy - 2, BOTS[0]); R(d, fx + 8, fy - 3, fx + 9, fy + 4, BOTS[0]); R(d, fx + 8, fy + 4, fx + 10, fy + 5, (40, 34, 38))
    R(d, fx + 2, fy - 8, fx + 6, fy - 7, skin)
    wig = round(1.2 * c.sin(0.0, 2))
    tipx, tipy = fx + 34, fy - 30 + wig
    d.line([(fx + 6, fy - 8), (tipx, tipy)], fill=(120, 84, 52), width=1)
    flx, fly = fx + 40, 209 + round(1.1 * c.sin(0.2, 2))
    d.line([(tipx, tipy), (flx, fly)], fill=(240, 240, 240), width=1)
    R(d, flx - 1, fly - 1, flx + 1, fly, (240, 70, 70)); P(d, flx, fly + 1, (250, 250, 250))
    for k in range(2):
        rr = 3 + ((c.step + k * 6) % 12) // 2
        d.ellipse([flx - rr * 2, fly + 1 - rr // 2, flx + rr * 2, fly + 1 + rr // 2],
                  outline=mix(water_top, (210, 236, 248), 0.5 * (1 - rr / 9)))
    R(d, fx - 12, fy - 5, fx - 7, fy, (180, 180, 190)); R(d, fx - 12, fy - 5, fx - 7, fy - 5, (220, 220, 228))
    R(d, fx - 10, fy - 7, fx - 9, fy - 5, (240, 150, 70))
    # barque + rameur
    bx = 168 + round(5 * c.sin(0.1))
    by = 178 + round(1.2 * c.sin(0.3, 2))
    d.polygon([(bx - 15, by), (bx + 15, by), (bx + 10, by + 6), (bx - 10, by + 6)], fill=(150, 98, 64))
    R(d, bx - 15, by, bx + 15, by, (226, 226, 232))
    R(d, bx - 8, by - 9, bx - 4, by - 3, (240, 190, 70)); R(d, bx - 8, by - 13, bx - 5, by - 10, SKINS[0])
    R(d, bx - 8, by - 14, bx - 5, by - 14, HAIRS[0])
    sw = round(6 * c.sin(0.5))
    d.line([(bx - 6, by - 6), (bx - 6 + sw, by + 3)], fill=(120, 84, 52)); d.line([(bx - 6, by - 6), (bx - 6 - sw, by + 3)], fill=(120, 84, 52))
    for k in range(3):
        R(d, bx - 12 + k * 4, by + 7, bx - 9 + k * 4, by + 7, mix(water_top, (210, 236, 248), 0.5))
    # canards
    for i in range(3):
        u, dirn = _pace(c, 110 + i * 14, 150 + i * 22, i * 0.31)
        dy = 168 + i * 9
        R(d, u - 3, dy, u + 3, dy + 2, (246, 246, 240) if i else (110, 82, 56))
        R(d, u + 2 * dirn, dy - 3, u + 3 * dirn, dy - 1, (30, 120, 70))
        P(d, u + 4 * dirn, dy - 2, (250, 170, 40))
        R(d, u - 5, dy + 3, u + 5, dy + 3, mix(water_top, (210, 236, 248), 0.4))
    # poisson qui saute
    if 15 <= c.step <= 20:
        k = c.step - 15
        fx2, fy2 = 150 + k * 2, 188 - round(12 * math.sin(math.pi * k / 5))
        R(d, fx2 - 3, fy2, fx2 + 3, fy2 + 2, (190, 200, 214)); R(d, fx2 - 5, fy2 - 1, fx2 - 4, fy2 + 3, (170, 180, 196))
        P(d, fx2 + 3, fy2, (30, 30, 36))
    # roseaux, fleurs, grand arbre d'avant-plan
    tree(d, c, 220, 238, 66, "round", sway=1.5 * c.sin(0.2))
    for i in range(14):
        rx = (6 + i * 7) % 130 if i % 2 == 0 else 150 + (i * 9) % 70
        rh = rng.randint(12, 24)
        sw = round(2 * c.sin(i * 0.17))
        d.line([(rx, 238), (rx + sw, 238 - rh)], fill=(70, 130, 60) if i % 3 else (92, 150, 66), width=1)
        if i % 3 == 0:
            R(d, rx + sw - 1, 238 - rh - 4, rx + sw, 238 - rh, (112, 74, 44))
    for _ in range(18):
        px, py = rng.randint(4, 235), rng.randint(214, 238)
        P(d, px, py, _pick(rng, [(250, 230, 90), (250, 250, 250), (240, 140, 190)]))


# ------------------------------------------------------------------ PARC

def place_park(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    rng = c.rng
    sky = c.sky_bot
    hill = mix((92, 150, 110), sky, 0.45)
    pts = [(0, 142)] + [(x, 132 - round(8 * (1 + math.sin(x / 46.0 + c.seed % 7)))) for x in range(0, W + 8, 8)] + [(W, 142)]
    d.polygon(pts, fill=hill)
    # rideau d'arbres lointains
    for x in range(-6, W + 12, 14):
        rr = rng.randint(8, 13)
        lc = mix(shade({"SPRING": (112, 190, 92), "SUMMER": (54, 148, 70), "AUTUMN": (206, 120, 40),
                        "WINTER": (96, 112, 100)}[c.season], 1.0), sky, 0.42)
        d.ellipse([x - rr, 128 - rr // 2, x + rr, 128 + rr + 12], fill=lc)
    # pelouse en bandes de tonte (perspective)
    top, bot = ((126, 204, 98), (74, 150, 70)) if c.season != "AUTUMN" else ((176, 172, 84), (122, 120, 60))
    snowy = c.snow or (c.season == "WINTER" and c.temp < 2)
    if snowy:
        top, bot = (236, 242, 252), (206, 216, 234)
    y = 142
    i = 0
    while y < H:
        hgt = 3 + (y - 142) // 12
        t = (y - 142) / (H - 142)
        col = mix(top, bot, t)
        R(d, 0, y, W, min(y + hgt, H - 1), shade(col, 1.05 if i % 2 else 0.96))
        y += hgt + 1
        i += 1
    # allée en perspective
    path = (222, 204, 158) if not snowy else (214, 220, 232)
    d.polygon([(108, 142), (132, 142), (236, 240), (4, 240)], fill=path)
    d.line([(108, 142), (4, 240)], fill=shade(path, 0.78), width=2)
    d.line([(132, 142), (236, 240)], fill=shade(path, 0.78), width=2)
    for _ in range(70):
        py = rng.randint(146, 239)
        half = 12 + (py - 142) * 0.65
        P(d, 120 + rng.uniform(-half, half) * 0.92, py, shade(path, 0.88))
    # parterres de fleurs sur les pelouses
    fl = [(250, 90, 110), (250, 220, 80), (250, 250, 252), (180, 110, 230), (255, 150, 70)]
    for _ in range(46):
        py = rng.randint(150, 239)
        side = rng.random() < 0.5
        half = 12 + (py - 142) * 0.65
        px = (120 - half - rng.randint(4, 70)) if side else (120 + half + rng.randint(4, 70))
        if 0 <= px < W and not snowy and c.season != "WINTER":
            P(d, px, py, _pick(rng, fl)); P(d, px + 1, py, _pick(rng, fl))
    # arbres : moyenne distance puis grands arbres sur les bords
    for tx, tb, th in ((74, 154, 32), (168, 154, 34), (52, 164, 44), (190, 166, 46)):
        tree(d, c, tx, tb, th, "round", sway=1.5 * c.sin(tx / 77.0))
    tree(d, c, 22, 188, 74, "round", sway=1.8 * c.sin(0.1))
    tree(d, c, 218, 184, 70, "round", sway=1.8 * c.sin(0.4))
    # banc + réverbères
    bx, by = 150, 176
    R(d, bx, by - 5, bx + 15, by - 4, (140, 98, 62)); R(d, bx, by - 9, bx + 15, by - 7, (160, 114, 74))
    R(d, bx + 1, by - 4, bx + 1, by, (60, 60, 70)); R(d, bx + 14, by - 4, bx + 14, by, (60, 60, 70))
    for lx in (88, 176):
        R(d, lx, 140, lx, 188, (52, 54, 66)); R(d, lx - 2, 136, lx + 2, 139, LIT if (c.night or c.dusk) else (214, 218, 226))
        R(d, lx - 3, 139, lx + 3, 139, (52, 54, 66))
        c.glow(lx, 138, 20, (255, 226, 150), 76)
    # oiseaux qui picorent sur l'allée
    for i in range(3):
        px = 96 + i * 17
        py = 200 + (i * 11) % 26
        if (c.step // 3 + i) % 4 == 0:
            R(d, px, py - 2, px + 3, py - 1, (126, 130, 144)); P(d, px + 4, py - 3, (126, 130, 144)); P(d, px + 4, py - 2, (240, 170, 60))
        else:
            R(d, px, py - 2, px + 3, py - 1, (126, 130, 144)); P(d, px + 4, py - 1, (240, 170, 60))
    # joggeur sur la pelouse de droite
    x, dirn = _pace(c, 150, 214, 0.1)
    person(d, round(x), 196, c.step * 2, s=1.0, dirn=dirn, **_person_kw(c, rng))
    # couple main dans la main (plan éloigné)
    x, dirn = _pace(c, 100, 140, 0.55)
    k1, k2 = _person_kw(c, rng), _person_kw(c, rng)
    person(d, round(x), 172, c.step, s=0.78, dirn=dirn, **k1)
    person(d, round(x) - dirn * 6, 172, c.step + 2, s=0.74, dirn=dirn, skirt=True, long_hair=True, **{**k2, "umbrella": k1.get("umbrella")})
    P(d, round(x) - dirn * 3, 164, k1["skin"])
    # grand-mère + chien (premier plan, personnage héros)
    gx, dirn = _pace(c, 72, 136, 0.0)
    gx = round(gx)
    cardigan = _pick(rng, [(236, 150, 170), (150, 190, 226), (186, 220, 160), (246, 206, 130)])
    person(d, gx, 232, c.step, s=1.7, dirn=dirn, skin=SKINS[0], hair=(214, 214, 222), top=cardigan,
           bot=(110, 70, 120), skirt=True, bun=True,
           scarf=(240, 90, 80) if c.cold else None,
           umbrella=_pick(rng, [(230, 70, 80), (250, 200, 60)]) if c.rain else None)
    lead = 22 + round(7 * c.sin(0.0, 2))
    dgx = gx + dirn * lead
    dog(d, dgx, 232, c.step, s=1.5, dirn=dirn, col=_pick(rng, [(176, 120, 70), (236, 226, 206), (70, 62, 60)]))
    d.line([(gx + dirn * 5, 215), (dgx - dirn * 2, 225)], fill=(224, 70, 70), width=1)
    # feuilles / pétales qui tombent (boucle en tuile)
    if c.season in ("AUTUMN", "SPRING") and not c.rain and not c.snow:
        tile = N * 4
        lc = [(214, 110, 30), (186, 70, 28), (240, 180, 50)] if c.season == "AUTUMN" else [(255, 200, 220), (255, 230, 240)]
        for i in range(14):
            x0, y0 = rng.randint(0, 239), rng.randint(0, tile - 1)
            y = (y0 + c.step * 4) % tile + 40
            if y < 238:
                x = x0 + 5 * math.sin(2 * math.pi * (c.t + i * 0.17))
                R(d, x, y, x + 1, y + 1, lc[i % len(lc)])
    # lucioles la nuit
    if c.night:
        for i in range(12):
            fx = (i * 41 + 17) % 230 + 5
            fy = 150 + (i * 23) % 80 + round(4 * math.sin(2 * math.pi * (c.t + i * 0.2)))
            if (c.step + i * 3) % 6 < 4:
                P(d, fx, fy, (210, 255, 120)); c.glow(fx, fy, 6, (200, 255, 110), 50)


PLACES = {"city": place_city, "beach": place_beach, "lake": place_lake, "park": place_park}


ORDER = ["city", "lake", "park", "cafe", "mountains", "market", "bridge", "playground",
         "harbor", "farm", "picnic", "beach"]


def pick_place(w, allowed: list[str] | None = None) -> str:
    """Lieu du jour : rotation sur le jour de l'année parmi les lieux compatibles
    (et autorisés par la config si `allowed` est fourni)."""
    from .places_more import COMPAT
    fair_beach = w.phase != "NUIT" and w.icon in ("SUN", "PARTLY", "CLOUD") and w.temp >= 19
    options = [n for n in ORDER if (fair_beach if n == "beach" else COMPAT.get(n, lambda _w: True)(w))]
    if allowed:
        narrowed = [n for n in options if n in allowed]
        options = narrowed or [n for n in ORDER if n in allowed] or options
    return options[(w.doy + w.year) % len(options)]


from . import places_extra  # noqa: E402,F401  (enregistre montagnes + pont)
from . import places_more  # noqa: E402,F401  (6 scènes du quotidien)
