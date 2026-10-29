"""Lieux supplémentaires : horizon de montagnes (randonneur, vaches) et pont (couple)."""

from __future__ import annotations

import math

from PIL import ImageDraw

from .places import GLASS, LIT, PLACES, _pace, _person_kw, _pick, _ridge
from .scenes import (HAIRS, SKINS, BOTS, N, W, Ctx, P, R, dog, gradient, mix, person, shade,
                     tree)


# ------------------------------------------------------------------ MONTAGNES

def place_mountains(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    rng = c.rng
    sky = c.sky_bot
    snowy = c.snow or c.season == "WINTER" or c.temp < 3
    for hmax, col, cap, bs in ((58, mix((132, 150, 190), sky, 0.5), 0.62, 152),
                               (44, mix((96, 120, 150), sky, 0.3), 0.7, 156),
                               (28, mix((64, 98, 88), sky, 0.12), 2.0, 160)):
        hs = _ridge(rng, 5, hmax)
        for x in range(W):
            h = hs[x]
            if h <= 0:
                continue
            top = bs - h
            sl = hs[x] - hs[max(x - 1, 0)]
            cc = shade(col, 0.8) if sl < 0 else shade(col, 1.1)
            d.line([(x, top), (x, bs)], fill=cc)
            if h > hmax * cap:
                d.line([(x, top), (x, top + 2 + (h - round(hmax * cap)) // 2)],
                       fill=(246, 250, 255) if sl >= 0 else (200, 212, 232))
    # chalets au fond de la vallée
    for i in range(5):
        cx = 18 + i * 44 + rng.randint(-8, 8)
        cy = 168
        wall = _pick(rng, [(176, 120, 76), (150, 100, 66), (196, 150, 100)])
        R(d, cx, cy - 8, cx + 11, cy, wall)
        d.polygon([(cx - 2, cy - 8), (cx + 13, cy - 8), (cx + 5, cy - 15)],
                  fill=(236, 240, 248) if snowy else (120, 54, 44))
        lit = c.night or c.dusk
        R(d, cx + 3, cy - 6, cx + 5, cy - 4, LIT if lit else (190, 214, 232))
        if lit:
            c.glow(cx + 4, cy - 5, 8, (255, 200, 110), 40)
        if i % 2 == 0:
            for k in range(3):
                P(d, cx + 9 + (c.step // 4 + k) % 3, cy - 18 - k * 3, (220, 224, 232))
    for x in range(-4, W, 11):
        tree(d, c, x, 172 + (x // 11) % 3 * 2, rng.randint(16, 28), "pine", sway=1.0 * c.sin(x / 50.0))
    gtop, gbot = ((140, 206, 100), (84, 156, 70)) if c.season != "AUTUMN" else ((190, 170, 80), (130, 116, 60))
    if snowy:
        gtop, gbot = (240, 244, 252), (212, 222, 238)
    gradient(d, 176, 240, gtop, gbot, bands=10)
    # rivière en lacets
    for i in range(17):
        rx, ry = 120 + round(26 * math.sin(i / 3.2)), 176 + i * 4
        wdt = 4 + i
        R(d, rx - wdt, ry, rx + wdt, ry + 3, (130, 176, 214) if snowy else (60, 150, 206))
        gl = (c.step + i * 2) % 8
        R(d, rx - wdt + gl, ry + 1, rx - wdt + gl + 2, ry + 1, (210, 238, 250))
    if not snowy:
        for _ in range(60):
            P(d, rng.randint(2, 237), rng.randint(180, 238),
              _pick(rng, [(250, 90, 110), (250, 230, 80), (250, 250, 252), (170, 110, 230)]))
    # sentier + randonneur (monte puis redescend)
    d.polygon([(24, 238), (46, 238), (96, 190), (88, 190)], fill=(214, 220, 232) if snowy else (196, 170, 124))
    x, dirn = _pace(c, 38, 70, 0.0)
    y = 232 - (x - 38) * 1.4
    kw = _person_kw(c, rng, False)
    person(d, round(x), round(y), c.step, s=1.5, dirn=dirn, top=(220, 70, 70), bot=(70, 78, 100),
           hat=(240, 210, 90), skin=kw["skin"], hair=kw["hair"])
    R(d, round(x) - dirn * 5, round(y) - 22, round(x) - dirn * 4, round(y) - 12, (230, 150, 50))
    # vaches qui broutent
    for i, (vx, vy) in enumerate(((176, 204), (206, 224), (150, 232))):
        pat = (246, 246, 244)
        R(d, vx, vy - 8, vx + 12, vy - 3, pat)
        R(d, vx + 3, vy - 7, vx + 5, vy - 5, (50, 46, 46))
        R(d, vx + 8, vy - 6, vx + 9, vy - 4, (50, 46, 46))
        hd = 1 if (c.step // 6 + i) % 2 else 0
        R(d, vx + 13, vy - 8 + hd * 3, vx + 16, vy - 5 + hd * 3, pat)
        P(d, vx + 16, vy - 4 + hd * 3, (240, 150, 150))
        R(d, vx + 1, vy - 2, vx + 1, vy, (60, 56, 56))
        R(d, vx + 10, vy - 2, vx + 10, vy, (60, 56, 56))
        P(d, vx + 14, vy - 3 + hd * 3, (250, 200, 60))
    # aigle qui plane
    if not (c.night or c.rain or c.snow):
        ex = (c.step * (W + 60) / N + 60) % (W + 60) - 30
        ey = 92 + 8 * math.sin(2 * math.pi * c.t * 2)
        for k in range(-5, 6):
            P(d, ex + k, ey + abs(k) // 3, (40, 38, 46))


# ------------------------------------------------------------------ PONT

def place_bridge(c: Ctx, d: ImageDraw.ImageDraw) -> None:
    rng = c.rng
    sky = c.sky_bot
    haze = mix((120, 126, 160), sky, 0.5)
    x = -6
    while x < W:                                                    # vieille ville
        w, top = rng.randint(14, 26), rng.randint(116, 132)
        col = mix(_pick(rng, [(214, 178, 140), (190, 120, 104), (170, 176, 190), (224, 208, 160)]), haze, 0.35)
        R(d, x, top, x + w, 162, col)
        d.polygon([(x - 1, top), (x + w + 1, top), (x + w // 2, top - 7)], fill=mix((130, 64, 56), haze, 0.35))
        for wy in range(top + 5, 156, 7):
            for wx in range(x + 3, x + w - 3, 6):
                lit = (c.night or c.dusk) and rng.random() < 0.6
                R(d, wx, wy, wx + 2, wy + 3, LIT if lit else mix(GLASS, haze, 0.3))
        x += w + rng.randint(0, 2)
    R(d, 0, 160, W, 166, (150, 142, 132))
    wtop = mix(sky, (52, 110, 150), 0.6)
    gradient(d, 167, 240, wtop, (8, 18, 40) if c.night else (22, 62, 98), bands=16)
    for row in range(14):
        for k in range(6):
            xx = (k * 47 + row * 31 + round(7 * math.sin(2 * math.pi * (c.t + row / 10)))) % (W + 20) - 10
            R(d, xx, 170 + row * 5, xx + 3 + row // 3, 170 + row * 5, mix(wtop, (214, 238, 250), 0.35))
    # arches
    R(d, 0, 176, W, 188, (176, 164, 148))
    for ax in (30, 120, 210):
        d.pieslice([ax - 38, 176, ax + 38, 232], 180, 360, fill=(10, 18, 36) if c.night else (36, 54, 84))
        d.arc([ax - 38, 176, ax + 38, 232], 180, 360, fill=(120, 110, 98), width=3)
    for px in (-4, 75, 165, 245):
        R(d, px - 6, 176, px + 6, 226, (150, 138, 124))
        R(d, px + 3, 176, px + 6, 226, (124, 114, 102))
    for yy in range(180, 188, 3):
        R(d, 0, yy, W, yy, (160, 148, 132))
    # tablier, parapet, lampadaires, guirlande
    R(d, 0, 170, W, 175, (200, 188, 168))
    R(d, 0, 169, W, 169, (230, 220, 200))
    R(d, 0, 152, W, 154, (176, 164, 148))
    for bx in range(2, W, 12):
        R(d, bx, 154, bx + 2, 169, (176, 164, 148))
        R(d, bx, 154, bx, 169, (206, 194, 174))
    for lx in (24, 100, 176, 232):
        R(d, lx, 128, lx, 169, (36, 40, 52))
        R(d, lx - 2, 124, lx + 2, 128, LIT if (c.night or c.dusk) else (226, 230, 238))
        c.glow(lx, 127, 22, (255, 226, 150), 80)
    for k in range(0, 76, 6):
        gx, gy = 24 + k, 130 + round(5 * math.sin(math.pi * k / 76))
        P(d, gx, gy, (255, 230, 130) if (c.step // 3 + k // 6) % 2 else (255, 190, 90))
        if c.night or c.dusk:
            c.glow(gx, gy, 5, (255, 220, 120), 50)
    # bateau qui descend la rivière
    span = W + 90
    bx = (c.step * span / N) % span - 50
    R(d, bx, 214, bx + 30, 218, (170, 60, 60))
    R(d, bx + 4, 208, bx + 18, 213, (240, 238, 232))
    R(d, bx + 6, 209, bx + 8, 211, GLASS)
    R(d, bx + 11, 209, bx + 13, 211, GLASS)
    R(d, bx - 4, 220, bx + 36, 220, mix(wtop, (214, 238, 250), 0.5))
    # le couple main dans la main
    x, dirn = _pace(c, 70, 160, 0.0)
    x = round(x)
    k1, k2 = _person_kw(c, rng), _person_kw(c, rng)
    person(d, x, 172, c.step, s=1.9, dirn=dirn, skin=SKINS[0], hair=HAIRS[0], bot=BOTS[0], top=k1["top"],
           scarf=k1.get("scarf"), umbrella=k1.get("umbrella"))
    person(d, x - dirn * 16, 172, c.step + 2, s=1.8, dirn=dirn, skirt=True, long_hair=True,
           skin=SKINS[4], hair=HAIRS[4], top=k2["top"], bot=k2["bot"], scarf=k2.get("scarf"),
           umbrella=k1.get("umbrella"))
    R(d, x - dirn * 8 - 1, 156, x - dirn * 8 + 1, 157, SKINS[0])
    if (c.step // 4) % 3 == 0 and not c.rain:
        hx, hy = x - dirn * 8, 134 - (c.step % 4)
        for dx, dy in ((-2, 0), (-1, -1), (1, -1), (2, 0), (-1, 0), (0, 0), (1, 0), (0, 1)):
            P(d, hx + dx, hy + dy, (250, 80, 110))
    x2, d2 = _pace(c, 178, 214, 0.5)
    person(d, round(x2), 172, c.step, s=1.0, dirn=d2, **_person_kw(c, rng))
    dog(d, round(x2) + d2 * 12, 172, c.step, s=0.9, dirn=d2)
    R(d, 0, 232, W, 239, (226, 232, 244) if c.season == "WINTER" else (74, 112, 70))
    tree(d, c, 20, 239, 58, "round", sway=1.5 * c.sin(0.2))


PLACES.update({"mountains": place_mountains, "bridge": place_bridge})
