"""Scènes du quotidien supplémentaires : terrasse de café, marché, aire de jeux,
port, ferme, pique-nique. Même moteur par couches que places.py."""

from __future__ import annotations

import math

from PIL import ImageDraw

from .places import GLASS, LIT, PLACES, _pace, _person_kw, _pick
from .scenes import (HAIRS, SKINS, W, Ctx, P, R, _rmap, dog, gradient, mix,
                     person, shade, tree, tri)


def sit(d, x, y, kw: dict, dirn: int = 1, ground: bool = False, s: float = 1.0) -> None:
    """Personnage assis (chaise ou sol), vu de profil."""
    r = _rmap(d, x, y, s, dirn)
    skin, hair, top, bot = kw["skin"], kw["hair"], kw["top"], kw["bot"]
    r(-2, -9, 2, -4, top)
    r(-2, -9, 2, -9, shade(top, 1.2))
    r(-2, -13, 1, -10, skin)
    r(-2, -14, 1, -13, hair)
    r(-2, -12, -2, -11, hair)
    r(1, -11, 1, -11, (30, 24, 28))
    if ground:
        r(-2, -4, 7, -2, bot)
        r(7, -4, 8, -2, (36, 32, 40))
    else:
        r(-2, -4, 3, -3, bot)
        r(2, -3, 3, 0, bot)
        r(2, 0, 4, 0, (36, 32, 40))
    r(2, -8, 4, -7, skin)


# ------------------------------------------------------------------ CAFÉ

def place_cafe(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    from .render import font
    rng = c.rng
    wall = _pick(rng, [(238, 214, 170), (214, 150, 120), (170, 196, 200), (226, 196, 206)])
    haze = c.sky_bot
    x = -6
    while x < W:                                              # toits lointains
        w, top = rng.randint(16, 28), rng.randint(112, 126)
        R(d, x, top, x + w, 140, mix(_pick(rng, [(200, 170, 150), (170, 176, 196), (210, 190, 150)]), haze, 0.45))
        x += w + 1
    R(d, 0, 128, W, 177, wall)
    R(d, 0, 128, W, 131, shade(wall, 1.2))
    R(d, 0, 132, W, 132, shade(wall, 0.75))
    lit = c.night or c.dusk
    for wx in range(12, W - 24, 46):                          # fenêtres à volets
        R(d, wx - 5, 138, wx - 1, 154, (60, 120, 100)); R(d, wx + 17, 138, wx + 21, 154, (60, 120, 100))
        R(d, wx, 138, wx + 16, 154, shade(wall, 0.6))
        R(d, wx + 1, 139, wx + 15, 153, LIT if lit else GLASS)
        R(d, wx + 8, 139, wx + 8, 153, shade(wall, 0.6)); R(d, wx + 1, 146, wx + 15, 146, shade(wall, 0.6))
        if lit:
            c.glow(wx + 8, 146, 14, (255, 200, 110), 40)
    R(d, 88, 146, 152, 156, (36, 74, 56))                      # enseigne
    R(d, 88, 146, 152, 146, (250, 220, 120))
    d.text((101, 148), "CAFE", font=font(8), fill=(250, 230, 150))
    for sx in range(4, 236, 10):                               # auvent festonné
        R(d, sx, 157, sx + 4, 168, (214, 56, 56)); R(d, sx + 5, 157, sx + 9, 168, (248, 244, 234))
        R(d, sx, 169, sx + 4, 170, (214, 56, 56)); R(d, sx + 5, 169, sx + 9, 170, (248, 244, 234))
    R(d, 6, 171, 234, 177, (70, 46, 34))
    for wx in (14, 70, 160, 204):
        R(d, wx, 172, wx + 28, 177, LIT if lit else (150, 126, 96))
    if lit:
        c.glow(120, 176, 40, (255, 190, 100), 40)
    for y in range(178, 240, 8):                                # terrasse carrelée
        for xx in range(0, W, 8):
            R(d, xx, y, xx + 7, y + 7, (214, 196, 168) if ((xx // 8 + y // 8) % 2) else (194, 174, 144))
    for px in (6, 226):                                         # plantes en pot
        R(d, px, 168, px + 8, 177, (170, 84, 60))
        d.ellipse([px - 4, 154, px + 12, 170], fill=(52, 130, 66))
    tables = [(44, 212, 1), (124, 206, 1), (200, 218, 1)]
    for (tx, ty, _) in tables:
        k1, k2 = _person_kw(c, rng, False), _person_kw(c, rng, False)
        if tx != 124 or c.step % 2 == 0 or True:
            sit(d, tx - 14, ty + 6, k1, 1)
            sit(d, tx + 14, ty + 6, k2, -1)
        for chx in (tx - 20, tx + 20):                          # dossiers de chaise
            R(d, chx - 1, ty - 8, chx, ty + 6, (110, 76, 50))
        R(d, tx, ty, tx, ty + 12, (60, 60, 70)); R(d, tx - 4, ty + 12, tx + 4, ty + 12, (60, 60, 70))
        d.ellipse([tx - 10, ty - 3, tx + 10, ty + 3], fill=(236, 232, 224))
        d.ellipse([tx - 10, ty - 3, tx + 10, ty + 1], fill=(250, 248, 242))
        R(d, tx - 5, ty - 5, tx - 3, ty - 2, (250, 250, 250)); R(d, tx + 3, ty - 5, tx + 5, ty - 2, (250, 250, 250))
        for q in range(2):                                      # vapeur des tasses
            P(d, tx - 4 + q * 8 + round(1.2 * math.sin(2 * math.pi * (c.t + q * 0.4))), ty - 7 - (c.step + q * 3) % 5, (240, 244, 250))
    # parasol sur la table du centre si soleil
    if not (c.rain or c.night):
        R(d, 124, 176, 124, 206, (226, 226, 230))
        for i in range(-22, 23):
            R(d, 124 + i, 172 - round(math.sqrt(max(484 - i * i, 0)) * 0.3), 124 + i, 177,
              (236, 170, 60) if ((i + 22) // 6) % 2 == 0 else (250, 246, 236))
    # serveur avec plateau
    x, dirn = _pace(c, 70, 170, 0.0)
    x = round(x)
    person(d, x, 238, c.step, s=1.5, dirn=dirn, skin=SKINS[1], hair=HAIRS[0], top=(248, 248, 250), bot=(30, 30, 38))
    R(d, x + dirn * 4 - 6, 238 - 26, x + dirn * 4 + 6, 238 - 25, (190, 196, 206))
    R(d, x + dirn * 4 - 3, 238 - 30, x + dirn * 4 - 2, 238 - 27, (250, 250, 250))
    R(d, x + dirn * 4 + 2, 238 - 30, x + dirn * 4 + 3, 238 - 27, (200, 120, 70))
    # pigeon qui picore
    px = 18 + ((c.step // 3) % 4) * 3
    R(d, px, 230, px + 4, 232, (130, 134, 150)); R(d, px + 4, 228 + (c.step // 3) % 2, px + 5, 229 + (c.step // 3) % 2, (130, 134, 150))
    P(d, px + 6, 229 + (c.step // 3) % 2, (240, 170, 60))


# ------------------------------------------------------------------ MARCHÉ

def place_market(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    rng = c.rng
    haze = c.sky_bot
    x = -4
    while x < W:
        w, top = rng.randint(18, 30), rng.randint(118, 132)
        col = mix(_pick(rng, [(214, 178, 140), (190, 130, 110), (170, 180, 196), (226, 206, 160)]), haze, 0.35)
        R(d, x, top, x + w, 150, col)
        d.polygon([(x - 1, top), (x + w + 1, top), (x + w // 2, top - 8)], fill=mix((140, 70, 58), haze, 0.35))
        x += w + 1
    cx = 190                                                    # clocher
    R(d, cx, 92, cx + 14, 150, mix((214, 200, 176), haze, 0.3)); R(d, cx + 10, 92, cx + 14, 150, mix((180, 166, 144), haze, 0.3))
    d.polygon([(cx - 2, 92), (cx + 16, 92), (cx + 7, 72)], fill=mix((100, 110, 130), haze, 0.3))
    d.ellipse([cx + 3, 100, cx + 11, 108], fill=(246, 244, 236)); R(d, cx + 7, 101, cx + 7, 104, (40, 40, 50)); R(d, cx + 7, 104, cx + 9, 104, (40, 40, 50))
    for y in range(150, 240, 6):                                # pavés
        for xx in range(0, W, 8):
            off = 4 if (y // 6) % 2 else 0
            R(d, xx + off, y, xx + off + 6, y + 4, mix((178, 172, 164), (150, 144, 138), ((xx + y) // 7) % 3 / 3))
    stalls = [(8, (214, 56, 56), "fruit"), (86, (60, 140, 200), "veg"), (164, (240, 180, 50), "flower")]
    for sx, col, kind in stalls:
        vk = _person_kw(c, rng, False)
        person(d, sx + 30, 190, 0, s=1.5, dirn=1 if sx < 100 else -1, walk=False, arms_up=(c.step // 6) % 2 == 0, **vk)
        for px in (sx, sx + 64):                                # poteaux
            R(d, px, 152, px + 1, 192, (110, 80, 56))
        for i in range(0, 66, 11):
            R(d, sx + i, 150, sx + i + 5, 164, col); R(d, sx + i + 6, 150, sx + i + 10, 164, (248, 244, 234))
        for i in range(0, 66, 11):
            R(d, sx + i, 165, sx + i + 5, 166, col); R(d, sx + i + 6, 165, sx + i + 10, 166, (248, 244, 234))
        R(d, sx - 2, 184, sx + 66, 200, (150, 104, 66)); R(d, sx - 2, 184, sx + 66, 185, (186, 136, 90))
        for i in range(0, 62, 6):
            gc = {"fruit": [(230, 60, 50), (250, 160, 40), (120, 190, 70)],
                  "veg": [(70, 160, 70), (240, 120, 40), (150, 90, 160)],
                  "flower": [(250, 90, 140), (250, 220, 70), (250, 250, 252)]}[kind][(i // 6) % 3]
            d.ellipse([sx + i + 1, 178, sx + i + 6, 184], fill=gc)
    # fanions qui flottent
    for i in range(0, 220, 10):
        fy = 146 + round(6 * math.sin(math.pi * i / 220)) + round(1.2 * math.sin(2 * math.pi * (c.t + i / 90)))
        R(d, 10 + i, fy, 14 + i, fy + 3, [(230, 70, 70), (250, 210, 60), (70, 150, 220), (90, 190, 120)][(i // 10) % 4])
    # clients qui flânent
    for lo, hi, ph, s in ((20, 90, 0.0, 1.5), (110, 190, 0.5, 1.6)):
        x, dirn = _pace(c, lo, hi, ph)
        kw = _person_kw(c, rng)
        person(d, round(x), 236, c.step, s=s, dirn=dirn, **kw)
        R(d, round(x) + dirn * 5, 236 - 12, round(x) + dirn * 9, 236 - 8, (176, 128, 80))        # panier
        R(d, round(x) + dirn * 6, 236 - 14, round(x) + dirn * 8, 236 - 13, (60, 160, 70))
    bx = 60 + round(5 * c.sin(0.2))                                         # enfant + ballon
    person(d, 150, 218, c.step, s=1.0, dirn=-1, **_person_kw(c, rng, False))
    d.line([(148, 206), (bx + 90, 180)], fill=(230, 230, 236))
    d.ellipse([bx + 86, 170, bx + 94, 182], fill=(240, 70, 110))


# ------------------------------------------------------------------ AIRE DE JEUX

def place_playground(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    rng = c.rng
    sky = c.sky_bot
    snowy = c.snow or (c.season == "WINTER" and c.temp < 2)
    for x in range(-6, W + 12, 15):
        rr = rng.randint(8, 13)
        d.ellipse([x - rr, 126 - rr // 2, x + rr, 126 + rr + 14],
                  fill=mix({"SPRING": (112, 190, 92), "SUMMER": (54, 148, 70), "AUTUMN": (206, 120, 40), "WINTER": (96, 112, 100)}[c.season], sky, 0.4))
    top, bot = ((126, 204, 98), (74, 150, 70)) if c.season != "AUTUMN" else ((176, 172, 84), (122, 120, 60))
    if snowy:
        top, bot = (236, 242, 252), (206, 216, 234)
    gradient(d, 140, 240, top, bot, bands=10)
    R(d, 14, 186, 226, 238, (224, 204, 150) if not snowy else (214, 220, 232))              # sol de sable
    R(d, 14, 186, 226, 187, shade((224, 204, 150), 0.8))
    tree(d, c, 18, 176, 64, "round", sway=1.5 * c.sin(0.1))
    tree(d, c, 224, 172, 60, "round", sway=1.5 * c.sin(0.4))
    # toboggan
    R(d, 34, 150, 52, 154, (230, 70, 70))
    R(d, 36, 154, 37, 196, (80, 120, 220)); R(d, 49, 154, 50, 196, (80, 120, 220))
    for ly in range(160, 196, 6):
        R(d, 36, ly, 50, ly, (240, 230, 190))
    d.polygon([(52, 154), (58, 154), (92, 196), (86, 196)], fill=(250, 200, 60))
    d.line([(52, 154), (86, 196)], fill=(220, 150, 30))
    u = (c.t * 2) % 1.0
    kx, ky = 56 + u * 32, 152 + u * 42
    person(d, round(kx), round(ky), 0, s=0.85, dirn=1, walk=False, arms_up=True, **_person_kw(c, rng, False))
    # balançoires
    R(d, 138, 150, 202, 152, (150, 150, 160))
    for ax in (140, 200):
        d.line([(ax, 152), (ax - 8, 196)], fill=(130, 130, 144), width=2); d.line([(ax, 152), (ax + 8, 196)], fill=(130, 130, 144), width=2)
    for i, sx in enumerate((158, 182)):
        th = 0.55 * math.sin(2 * math.pi * (c.t + i * 0.37))
        ex, ey = sx + 34 * math.sin(th), 152 + 34 * math.cos(th)
        d.line([(sx - 4, 152), (ex - 4, ey)], fill=(200, 200, 210)); d.line([(sx + 4, 152), (ex + 4, ey)], fill=(200, 200, 210))
        R(d, ex - 6, ey, ex + 6, ey + 1, (160, 100, 60))
        sit(d, round(ex), round(ey), _person_kw(c, rng, False), 1 if th > 0 else -1)
    # bascule
    ang = 0.28 * math.sin(2 * math.pi * c.t)
    px, py = 110, 214
    dx, dy = 22 * math.cos(ang), 22 * math.sin(ang)
    d.polygon([(px - 5, py + 12), (px + 5, py + 12), (px, py)], fill=(120, 120, 134))
    d.line([(px - dx, py - dy), (px + dx, py + dy)], fill=(240, 190, 60), width=3)
    sit(d, round(px - dx), round(py - dy) - 2, _person_kw(c, rng, False), 1, s=0.9)
    sit(d, round(px + dx), round(py + dy) - 2, _person_kw(c, rng, False), -1, s=0.9)
    # parents sur le banc, enfant avec seau
    bx, by = 86, 178
    R(d, bx, by - 5, bx + 22, by - 4, (140, 98, 62)); R(d, bx, by - 10, bx + 22, by - 8, (160, 114, 74))
    sit(d, bx + 6, by - 4, _person_kw(c, rng), 1); sit(d, bx + 16, by - 4, _person_kw(c, rng), -1)
    x, dirn = _pace(c, 30, 90, 0.3)
    person(d, round(x), 228, c.step, s=1.2, dirn=dirn, **_person_kw(c, rng))
    R(d, round(x) + 6 * dirn, 228 - 4, round(x) + 8 * dirn, 228 - 2, (240, 90, 80))


# ------------------------------------------------------------------ PORT

def place_harbor(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    rng = c.rng
    sky = c.sky_bot
    gradient(d, 126, 178, mix((150, 206, 232), sky, 0.3), (30, 112, 170) if not c.night else (10, 24, 54), bands=12)
    for row in range(10):
        for k in range(6):
            xx = (k * 41 + row * 23 + round(6 * math.sin(2 * math.pi * (c.t + row / 9)))) % (W + 20) - 10
            R(d, xx, 130 + row * 5, xx + 4 + row // 2, 130 + row * 5, mix((110, 180, 224), (220, 240, 252), 0.4))
    # phare
    lx = 214
    R(d, lx - 7, 100, lx + 7, 152, (246, 244, 238))
    for yy in range(106, 150, 14):
        R(d, lx - 7, yy, lx + 7, yy + 6, (214, 56, 56))
    R(d, lx - 9, 96, lx + 9, 99, (60, 64, 76)); R(d, lx - 5, 86, lx + 5, 95, (255, 240, 170) if (c.night or c.dusk) else (200, 220, 236))
    d.polygon([(lx - 6, 86), (lx + 6, 86), (lx, 78)], fill=(60, 64, 76))
    if c.night or c.dusk:
        th = 2 * math.pi * c.t
        for k in range(1, 9):
            c.glow(lx + math.cos(th) * k * 15, 90 + k * 1.5, max(5, 14 - k), (255, 240, 170), 60)
    # bateaux amarrés
    for bx, col, mast in ((28, (214, 60, 60), True), (96, (60, 120, 210), False), (160, (240, 200, 60), True)):
        by = 168 + round(1.6 * math.sin(2 * math.pi * (c.t + bx / 90)))
        d.polygon([(bx - 18, by - 6), (bx + 20, by - 6), (bx + 14, by + 4), (bx - 12, by + 4)], fill=col)
        R(d, bx - 18, by - 6, bx + 20, by - 5, (246, 246, 250))
        R(d, bx - 4, by - 14, bx + 8, by - 7, (240, 238, 232)); R(d, bx - 2, by - 12, bx + 2, by - 9, GLASS)
        if mast:
            R(d, bx + 12, by - 30, bx + 12, by - 6, (130, 100, 70))
            w = 1 if (c.step // 3) % 2 else 2
            R(d, bx + 13, by - 30, bx + 13 + w * 3, by - 28, (250, 200, 60))
        R(d, bx - 20, by + 5, bx + 22, by + 5, mix((30, 112, 170), (220, 240, 252), 0.4))
    # quai
    R(d, 0, 176, W, 240, (150, 142, 132))
    for y in range(178, 240, 9):
        R(d, 0, y, W, y, (126, 118, 108))
        for xx in range((y // 9 % 2) * 6, W, 18):
            R(d, xx, y, xx, y + 8, (126, 118, 108))
    R(d, 0, 176, W, 178, (186, 178, 166))
    for bx in (30, 100, 170):                                  # bollards
        R(d, bx, 186, bx + 5, 194, (50, 52, 64)); R(d, bx - 1, 185, bx + 6, 186, (80, 82, 96))
    # mouettes sur les bollards
    for bx in (31, 171):
        R(d, bx, 180, bx + 4, 184, (250, 250, 252)); R(d, bx + 3, 177, bx + 5, 180, (250, 250, 252)); P(d, bx + 6, 178, (240, 170, 50))
        R(d, bx - 1, 181, bx + 1, 183, (150, 156, 168))
    # caisses de poissons + chat
    for i, cx in enumerate((60, 140)):
        R(d, cx, 206, cx + 22, 222, (176, 130, 84)); R(d, cx, 206, cx + 22, 208, (206, 160, 108))
        for k in range(0, 20, 5):
            R(d, cx + 1 + k, 202 + (k // 5) % 2, cx + 4 + k, 205, (170, 190, 210))
    R(d, 145, 196, 154, 204, (230, 140, 60)); R(d, 153, 192, 157, 196, (230, 140, 60)); R(d, 143, 199 + (c.step // 4) % 2, 144, 203, (230, 140, 60))
    # pêcheurs qui déchargent
    for sx, ph in ((40, 0.0), (112, 0.4)):
        x, dirn = _pace(c, sx, sx + 36, ph)
        kw = _person_kw(c, rng)
        kw["top"] = _pick(rng, [(236, 190, 40), (60, 100, 170)])
        person(d, round(x), 234, c.step, s=1.6, dirn=dirn, hat=(40, 50, 90), **kw)
    # filets qui sèchent
    for i in range(0, 40, 4):
        R(d, 184 + i, 196, 184 + i, 214 + (i % 8), (166, 150, 110))
    for j in range(198, 216, 4):
        R(d, 184, j, 222, j, (166, 150, 110))
    R(d, 182, 192, 183, 218, (110, 80, 56)); R(d, 223, 192, 224, 218, (110, 80, 56))


# ------------------------------------------------------------------ FERME

def place_farm(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    rng = c.rng
    sky = c.sky_bot
    snowy = c.snow or (c.season == "WINTER" and c.temp < 2)
    hill = mix((98, 150, 110), sky, 0.4)
    d.polygon([(0, 150)] + [(x, 138 - round(8 * (1 + math.sin(x / 58.0 + 1)))) for x in range(0, W + 8, 8)] + [(W, 150)], fill=hill)
    gradient(d, 146, 240, (150, 204, 100) if not snowy else (238, 244, 252), (96, 160, 74) if not snowy else (212, 222, 238), bands=10)
    # champ de blé en rangs convergents (à gauche) + prairie (à droite)
    wheat = (230, 196, 88) if not snowy else (226, 232, 244)
    d.polygon([(0, 150), (112, 150), (24, 240), (0, 240)], fill=wheat)
    for k in range(-6, 8):
        d.line([(112 + k * 1.5, 150), (24 + k * 20, 240)], fill=shade(wheat, 0.82), width=1)
    d.polygon([(128, 150), (240, 150), (240, 240), (216, 240)], fill=(110, 178, 80) if not snowy else (226, 234, 246))
    for k in range(-2, 8):
        d.line([(128 + k * 1.5, 150), (216 + k * 12, 240)], fill=(90, 150, 66) if not snowy else (200, 210, 230), width=1)
    d.polygon([(112, 150), (128, 150), (216, 240), (24, 240)], fill=(176, 140, 98) if not snowy else (214, 218, 228))      # chemin de terre
    # grange + silo
    bx, by = 170, 176
    R(d, bx, by - 26, bx + 40, by, (176, 52, 48)); R(d, bx, by - 26, bx + 40, by - 25, (210, 90, 80))
    d.polygon([(bx - 3, by - 26), (bx + 43, by - 26), (bx + 20, by - 42)], fill=(98, 52, 48) if not snowy else (236, 240, 248))
    R(d, bx + 12, by - 16, bx + 28, by, (120, 36, 36)); d.line([(bx + 12, by - 16), (bx + 28, by)], fill=(246, 240, 230)); d.line([(bx + 28, by - 16), (bx + 12, by)], fill=(246, 240, 230))
    R(d, bx + 44, by - 34, bx + 54, by, (190, 196, 206)); d.ellipse([bx + 44, by - 40, bx + 54, by - 30], fill=(170, 176, 190))
    if c.night or c.dusk:
        c.glow(bx + 20, by - 8, 18, (255, 200, 110), 40)
    # éolienne lointaine
    wx, wy = 70, 118
    R(d, wx, wy, wx + 1, 150, (236, 238, 244))
    for k in range(3):
        a = 2 * math.pi * (c.t + k / 3)
        d.line([(wx, wy), (wx + 20 * math.cos(a), wy + 20 * math.sin(a))], fill=(244, 246, 250), width=1)
    # clôture + épouvantail + moutons
    for fx in range(130, 236, 14):
        R(d, fx, 186, fx + 1, 196, (130, 96, 66))
    R(d, 130, 189, 236, 189, (150, 112, 78)); R(d, 130, 193, 236, 193, (150, 112, 78))
    R(d, 36, 188, 37, 214, (120, 90, 60)); R(d, 28, 194, 45, 195, (120, 90, 60))
    R(d, 33, 183, 40, 188, (240, 210, 150)); R(d, 30, 180, 43, 182, (140, 100, 60)); R(d, 33, 175, 40, 180, (140, 100, 60))
    for i, (sx, sy) in enumerate(((150, 214), (192, 224), (214, 208))):
        hd = (c.step // 5 + i) % 2
        d.ellipse([sx, sy - 10, sx + 16, sy], fill=(244, 242, 236)); R(d, sx + 14, sy - 8 + hd * 3, sx + 18, sy - 4 + hd * 3, (60, 54, 56))
        R(d, sx + 2, sy, sx + 3, sy + 3, (60, 54, 56)); R(d, sx + 12, sy, sx + 13, sy + 3, (60, 54, 56))
    # tracteur + fermier
    tx, dirn = _pace(c, 70, 150, 0.0)
    tx, ty = round(tx), 226
    f = 1 if dirn > 0 else -1
    r = _rmap(d, tx, ty, 1.0, f)
    d.ellipse([tx - 18, ty - 1, tx + 18, ty + 2], fill=(0, 0, 0, 70))
    r(-12, -16, 6, -8, (60, 160, 70)); r(4, -12, 14, -9, (60, 160, 70)); r(-8, -26, 0, -16, (80, 180, 90))
    r(-7, -25, -1, -19, (170, 210, 232)); r(12, -18, 13, -12, (50, 50, 60))
    for wxo, rad in ((-8, 8), (11, 5)):
        cx = tx + wxo * f
        d.ellipse([cx - rad, ty - rad * 2, cx + rad, ty], fill=(34, 34, 40)); d.ellipse([cx - rad // 2, ty - rad - rad // 2, cx + rad // 2, ty - rad // 2], fill=(220, 190, 60))
        a = 2 * math.pi * c.t * 2 * (1 if dirn > 0 else -1)
        P(d, cx + (rad - 2) * math.cos(a), ty - rad + (rad - 2) * math.sin(a), (110, 110, 120))
    for k in range(3):
        P(d, tx + 13 * f + (c.step + k * 2) % 4 * 0, ty - 24 - (c.step + k * 3) % 8, (200, 204, 212))
    person(d, 120, 196, c.step, s=1.2, dirn=-1, walk=False, arms_up=(c.step // 5) % 2 == 0, hat=(230, 200, 100), top=(70, 110, 190), bot=(70, 80, 110), skin=SKINS[1], hair=HAIRS[0])


# ------------------------------------------------------------------ PIQUE-NIQUE

def place_picnic(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    rng = c.rng
    sky = c.sky_bot
    for x in range(-6, W + 12, 14):
        rr = rng.randint(8, 13)
        d.ellipse([x - rr, 128 - rr // 2, x + rr, 128 + rr + 12],
                  fill=mix({"SPRING": (112, 190, 92), "SUMMER": (54, 148, 70), "AUTUMN": (206, 120, 40), "WINTER": (96, 112, 100)}[c.season], sky, 0.42))
    gradient(d, 138, 240, (136, 208, 104), (72, 148, 68), bands=10)
    tree(d, c, 214, 186, 78, "round", sway=1.6 * c.sin(0.3))
    d.ellipse([150, 196, 240, 226], fill=(58, 120, 56))                                        # ombre portée
    tree(d, c, 40, 160, 40, "round", sway=1.2 * c.sin(0.6))
    # plaid à carreaux en perspective
    d.polygon([(66, 196), (170, 196), (186, 232), (50, 232)], fill=(222, 70, 70))
    for k in range(0, 10, 2):
        yy = 196 + k * 3.6
        d.line([(66 - k * 1.6, yy), (170 + k * 1.6, yy)], fill=(248, 244, 236), width=2)
    for k in range(0, 9, 2):
        d.line([(66 + k * 13, 196), (50 + k * 17, 232)], fill=(248, 244, 236), width=2)
    # panier, sandwichs, boissons
    R(d, 124, 206, 140, 216, (176, 128, 80)); R(d, 124, 206, 140, 207, (210, 164, 110)); d.arc([126, 198, 138, 212], 180, 360, fill=(140, 100, 62))
    d.ellipse([100, 210, 110, 214], fill=(250, 250, 252)); R(d, 102, 207, 108, 210, (246, 200, 120))
    R(d, 144, 204, 147, 214, (60, 160, 100)); R(d, 150, 206, 153, 214, (230, 90, 70))
    # famille assise
    k1, k2, k3 = _person_kw(c, rng, False), _person_kw(c, rng, False), _person_kw(c, rng, False)
    sit(d, 84, 218, k1, 1, ground=True, s=1.3)
    sit(d, 152, 224, k2, -1, ground=True, s=1.3)
    sit(d, 116, 226, k3, 1, ground=True, s=1.0)
    # cerf-volant tenu par l'enfant debout
    kx, ky = 40, 232
    kidp = _person_kw(c, rng, False)
    person(d, kx, ky, c.step, s=1.2, dirn=1, walk=False, arms_up=True, **kidp)
    ax, ay = 78 + 6 * math.sin(2 * math.pi * c.t), 74 + 4 * math.sin(2 * math.pi * (c.t + 0.3))
    d.line([(kx + 4, ky - 16), (ax, ay + 6)], fill=(240, 240, 244))
    d.polygon([(ax, ay - 8), (ax + 7, ay), (ax, ay + 8), (ax - 7, ay)], fill=(240, 70, 100))
    d.polygon([(ax, ay - 8), (ax + 7, ay), (ax, ay)], fill=(250, 210, 60))
    for k in range(1, 6):
        P(d, ax - 2 * k + round(2 * math.sin(2 * math.pi * (c.t + k * 0.12))), ay + 8 + k * 3, (240, 70, 100) if k % 2 else (90, 190, 120))
    # chien et balle
    bx = 180 - 36 * tri(c.t * 1.0)
    by = 232 - 14 * abs(math.sin(2 * math.pi * c.t * 2))
    d.ellipse([bx - 2, by - 2, bx + 2, by + 2], fill=(250, 210, 60))
    dog(d, round(bx + 14), 236, c.step, s=1.3, dirn=-1 if (c.t % 1.0) < 0.5 else 1, col=(176, 120, 70))
    # papillons
    for i in range(3):
        px = 30 + i * 70 + 12 * math.sin(2 * math.pi * (c.t + i * 0.3))
        py = 168 + i * 6 + 6 * math.sin(2 * math.pi * (c.t * 2 + i * 0.2))
        wc = [(250, 200, 60), (250, 250, 252), (240, 130, 190)][i]
        if (c.step + i) % 2:
            R(d, px - 2, py - 1, px + 2, py, wc)
        else:
            R(d, px - 1, py - 2, px + 1, py + 1, wc)


COMPAT = {
    "cafe": lambda w: True,
    "market": lambda w: w.phase != "NUIT" and w.icon != "STORM",
    "playground": lambda w: w.phase != "NUIT" and w.icon != "STORM",
    "harbor": lambda w: True,
    "farm": lambda w: True,
    "picnic": lambda w: w.phase != "NUIT" and w.icon in ("SUN", "PARTLY", "CLOUD") and w.temp >= 14,
}

PLACES.update({"cafe": place_cafe, "market": place_market, "playground": place_playground,
               "harbor": place_harbor, "farm": place_farm, "picnic": place_picnic})
