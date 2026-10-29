"""Sprites pixel-perfect pour le dashboard : pièce tournante + flèches.

Tout est dessiné en grille native (1 unité = 1 pixel logique) puis agrandi
en multiples ENTIERS via nearest-neighbor — jamais de scaling fractionnaire,
jamais d'anti-aliasing. Style : pièce type Mario/or, symbole par bitmap.

Palette pièce (5 tons) :
  OUT   contour/ombre externe    (120,  62, 12)
  SHADE ombre interne bas-droite (235, 145, 28)
  BASE  or de base               (250, 190, 44)
  HIGH  reflet haut-gauche       (255, 232, 130)
  SYM   glyphe                   (105,  55, 10)
"""

from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image

OUT = (120, 62, 12)
SHADE = (235, 145, 28)
BASE = (250, 190, 44)
HIGH = (255, 232, 130)
SYM = (105, 55, 10)

# ------------------------------------------------------------------ glyphes

# Bitcoin "B" barré — 7x11, '1' = pixel symbole, aligné en haut-gauche
BITCOIN_B = [
    ".11....",
    ".11....",
    ".1111..",
    ".1...1.",
    ".1...1.",
    ".1111..",
    ".1...1.",
    ".1...1.",
    ".1111..",
    ".11....",
    ".11....",
]

ETH_DIAMOND = [
    "....11....",
    "....11....",
    "...1111...",
    "..111111..",
    ".11111111.",
    "1111111111",
    ".11111111.",
    "..111111..",
    "...1111...",
    "....11....",
]

# Flèche haussière 9x11 (triangle + tige) ; baissière = miroir vertical
ARROW_UP = [
    "....1....",
    "...111...",
    "..11111..",
    ".1111111.",
    "111111111",
    "....1....",
    "....1....",
    "....1....",
    "....1....",
    "....1....",
    "....1....",
]


def _mirror_v(bitmap: list[str]) -> list[str]:
    return bitmap[::-1]


ARROW_DOWN = _mirror_v(ARROW_UP)


def bitmap_to_image(bitmap: list[str], color, size: int = 1) -> Image.Image:
    """Rasterise un bitmap en image, agrandie d'un facteur ENTIER.

    `color` : une couleur (pixels '1') ou un dict {caractère: couleur RGB}
    pour les bitmaps multi-couleurs (tous les autres caractères = transparent).
    """
    h, w = len(bitmap), max(len(r) for r in bitmap)
    tiny = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = tiny.load()
    multi = isinstance(color, dict)
    for y, row in enumerate(bitmap):
        for x, c in enumerate(row):
            if c == ".":
                continue
            col = color.get(c) if multi else (color if c == "1" else None)
            if col:
                px[x, y] = (*col, 255)
    return tiny.resize((w * size, h * size), Image.NEAREST) if size > 1 else tiny


# ------------------------------------------------------------ météo (12x12)

SUN = [
    ".....11.....",
    "............",
    "...111111...",
    "..11111111..",
    ".1111111111.",
    ".1111111111.",
    ".1111111111.",
    ".1111111111.",
    "..11111111..",
    "...111111...",
    "............",
    ".....11.....",
]
MOON = [
    "....1111....",
    "..111111....",
    ".111111.....",
    ".11111......",
    "11111.......",
    "11111.......",
    "11111.......",
    "11111.......",
    ".11111......",
    ".111111.....",
    "..111111....",
    "....1111....",
]
CLOUD = [
    "............",
    "............",
    "....1111....",
    "...111111...",
    "..11111111..",
    ".1111111111.",
    "111111111111",
    "111111111111",
    "111111111111",
    "............",
    "............",
    "............",
]
PARTLY = [
    "........11..",
    ".......1111.",
    ".......1111.",
    "....222.11..",
    "...22222211.",
    "..222222222.",
    ".2222222222.",
    "222222222222",
    "222222222222",
    "............",
    "............",
    "............",
]
RAIN = [
    "...111111...",
    "..11111111..",
    ".1111111111.",
    "111111111111",
    "111111111111",
    "............",
    ".1..1..1....",
    ".1..1..1....",
    "1..1..1..1..",
    "1..1..1..1..",
    "............",
    "............",
]
STORM = [
    "...111111...",
    "..11111111..",
    ".1111111111.",
    "111111111111",
    "111111111111",
    "....11......",
    "...11.......",
    "..11111.....",
    "...11.......",
    "....1.......",
    "............",
    "............",
]
SNOW = [
    "...111111...",
    "..11111111..",
    ".1111111111.",
    "111111111111",
    "111111111111",
    "............",
    "1..1..1..1..",
    ".1..1..1....",
    "1..1..1..1..",
    ".1..1..1....",
    "............",
    "............",
]
FOG = [
    "............",
    "111111111111",
    "111111111111",
    "............",
    ".1111111111.",
    ".1111111111.",
    "............",
    "..111111111.",
    "..111111111.",
    "............",
    "............",
    "............",
]

ICON_COLORS = {
    "SUN": (255, 214, 64), "MOON": (226, 232, 250), "CLOUD": (188, 196, 212),
    "PARTLY": {"1": (255, 214, 64), "2": (196, 204, 220)},
    "RAIN": (96, 160, 240), "STORM": (255, 224, 80), "SNOW": (235, 242, 255),
    "FOG": (170, 178, 195),
}
WEATHER_BITMAPS = {"SUN": SUN, "MOON": MOON, "CLOUD": CLOUD, "PARTLY": PARTLY,
                   "RAIN": RAIN, "STORM": STORM, "SNOW": SNOW, "FOG": FOG}


def weather_icon(name: str, size: int = 4) -> Image.Image:
    return bitmap_to_image(WEATHER_BITMAPS[name], ICON_COLORS[name], size)


# ------------------------------------------------- poule (personnage 12x12)
# W corps blanc, R crête, O bec/pattes, B oeil, G aile — 2 frames de marche.

CHICKEN_A = [
    "......RR....",
    ".....RR.....",
    "....WWWWW...",
    "...WWWWWWW..",
    "..WWBWWWWW..",
    ".OWWWWWWWW..",
    ".OWWWWWWGW..",
    "..WWWWWGG...",
    "..WWWWWWW...",
    "...WWWWW....",
    "....O.O.....",
    "...O...O....",
]
CHICKEN_B = [
    "............",
    "......RR....",
    ".....RR.....",
    "....WWWWW...",
    "...WWBWWWW..",
    "..WWWWWWWW..",
    ".OWWWWWWGW..",
    ".OWWWWWGG...",
    "..WWWWWWW...",
    "...WWWWW....",
    "...O...O....",
    "....O.O.....",
]

CHICKEN_COLORS = {"W": (246, 246, 240), "R": (255, 70, 64), "O": (255, 168, 40),
                  "B": (20, 20, 24), "G": (206, 206, 198)}


def chicken_frame(step: int, size: int = 4) -> Image.Image:
    """Poule en marche (2 frames alternées), facteur ENTIER."""
    return bitmap_to_image(CHICKEN_A if step % 2 == 0 else CHICKEN_B, CHICKEN_COLORS, size)


# Scènes kawaii : la poule réagit à la météo. Canvas 24x20, poule ancrée en
# (6, 6) ; accessoires dessinés par-dessus (pixel par pixel, pas de lissage).

_SCENE_W, _SCENE_H = 24, 20
_CHICK_X, _CHICK_Y = 6, 6          # ancre de la poule dans le canvas


def _scene_canvas() -> Image.Image:
    return Image.new("RGBA", (_SCENE_W, _SCENE_H), (0, 0, 0, 0))


def chicken_scene(situation: str, step: int, size: int = 5, season: str = "") -> Image.Image:
    """Poule chibi dans sa situation météo (canvas 24x20, facteur ENTIER).

    SUN lunettes / RAIN parapluie / STORM cachée+! / SNOW écharpe /
    WIND s'envole / NIGHT dort / MEAL picore / NEUTRAL marche.
    season : WINTER bonnet, AUTUMN feuilles, SPRRING fleur.
    """
    img = _scene_canvas()
    px = img.load()
    W, R, O, B, G = (246, 246, 240), (255, 70, 64), (255, 168, 40), (20, 20, 24), (206, 206, 198)
    bob = 1 if (situation in ("NEUTRAL", "SUN", "MEAL") and step % 2) else 0
    if situation == "WIND":
        cy = _CHICK_Y - 4 + (1 if step % 2 else 0)      # s'envole, oscille
    elif situation == "NIGHT":
        cy = _CHICK_Y + 1                                # assise, plus basse
    else:
        cy = _CHICK_Y + bob
    cx = _CHICK_X
    frame = CHICKEN_A if (situation != "NIGHT" and step % 2 == 0) or situation in ("NIGHT", "STORM") else (
        CHICKEN_B if step % 2 else CHICKEN_A)

    def put(x, y, col):
        px[x, y] = (*col, 255)

    # --- poule (copie du bitmap sur le canvas)
    for yy, row in enumerate(frame):
        for xx, ch in enumerate(row):
            if ch == ".":
                continue
            col = {"W": W, "R": R, "O": O, "B": B, "G": G}[ch]
            put(cx + xx, cy + yy, col)

    # --- accessoires par situation
    if situation == "SUN":
        for xx in range(cx + 1, cx + 8):                 # lunettes noires
            put(xx, cy + 4, B)
        put(cx + 8, cy + 5, B)                           # branche
    elif situation == "RAIN":
        for yy in range(cy - 3, cy + 12):                # manche du parapluie
            put(cx + 5, yy, W)
        for xx in range(cx - 5, cx + 12):                # canopy
            put(xx, cy - 4, R)
        for xx in range(cx - 4, cx + 11, 2):
            put(xx, cy - 5, R)
    elif situation == "STORM":
        for xx in range(cx - 1, cx + 9):                 # elle se couvre (aile levée)
            put(xx, cy + 6, G)
            put(xx, cy + 7, G)
        put(cx + 14, cy - 6, R)                          # "!" d'alerte
        put(cx + 14, cy - 5, R)
        put(cx + 14, cy - 3, R)
    elif situation == "SNOW":
        for xx in range(cx, cx + 9):                     # écharpe
            put(xx, cy + 8, R)
        put(cx + 9, cy + 9, R)
        put(cx + 9, cy + 10, R)                          # pan qui pend
    elif situation == "WIND":
        for xx in (cx - 3, cx - 4):                      # ailes déployées
            put(xx, cy + 5, W); put(xx, cy + 6, W)
            put(cx + 12, cy + 5, W); put(cx + 12, cy + 6, W)
        for xx in range(cx + 2, cx + 10, 3):             # traînées de vent
            put(xx, cy + 10, G); put(xx, cy + 12, G)
    elif situation == "NIGHT":
        put(cx + 4, cy + 4, W)                           # oeil fermé -> trait
        put(cx + 5, cy + 4, W)
        put(cx + 3, cy + 4, W)
        zx, zy = cx + 10, cy - 4                         # "Z" 3x3
        for i in range(3):
            put(zx + i, zy, (178, 190, 255))
            put(zx + i, zy + 2, (178, 190, 255))
        put(zx + 1, zy + 1, (178, 190, 255))
        put(zx + 2, zy + 1, (178, 190, 255))
        put(zx + 5, zy - 2, (140, 150, 210))             # petit "z"
        put(zx + 6, zy - 2, (140, 150, 210))
        put(zx + 5, zy - 1, (140, 150, 210))
    elif situation == "MEAL":
        for sx in (cx + 11, cx + 13, cx + 15):           # graines au sol
            put(sx, cy + 11, O)
            put(sx + 1, cy + 11, O)

    # --- touche saisonnière (subordonnée à la situation)
    if season == "WINTER" and situation not in ("RAIN",):
        for hx in range(cx + 3, cx + 9):                 # bonnet rouge + pompon
            put(hx, cy - 1, R)
        for hx in range(cx + 4, cx + 8):
            put(hx, cy - 2, R)
        put(cx + 5, cy - 3, W); put(cx + 6, cy - 3, W)
    elif season == "AUTUMN":
        for lx, ly in ((cx + 13, cy - 3), (cx + 15, cy + 1), (cx + 14, cy + 5)):
            put(lx, ly, (226, 140, 40)); put(lx + 1, ly, (196, 100, 30))
    elif season == "SPRING":
        put(cx + 16, cy + 10, (90, 190, 110))            # tige
        put(cx + 16, cy + 9, (255, 150, 200)); put(cx + 15, cy + 9, (255, 190, 220))
        put(cx + 17, cy + 9, (255, 190, 220))

    return img.resize((_SCENE_W * size, _SCENE_H * size), Image.NEAREST)


# --------------------------------------------------------------- chat (14x10)
# O corps roux, D rayures, W museau, B oeil, P nez — 2 frames de marche.

CAT_A = [
    ".O..O.......",
    ".OOOO.......",
    "OOOOOOODDO..",
    "OGWOOOODDO..",
    "OWWOOOOOOOO.",
    "OOOOOOOOOOO.",
    ".OOOOOOOOOOO",
    ".OOOOOOOOOO.",
    "..O..O..O.O.",
    "..O..O..O.O.",
]
CAT_B = [
    "............",
    ".O..O.......",
    ".OOOO.......",
    "OOOOOOODDO..",
    "OGWOOOODDO..",
    "OWWOOOOOOOO.",
    "OOOOOOOOOOO.",
    ".OOOOOOOOOOO",
    ".O..O..O..O.",
    ".O..O..O..O.",
]
# Chat noir kawaii : corps anthracite, rayures subtiles, grand oeil jaune-vert,
# museau blanc, nez rose.
CAT_COLORS = {"O": (38, 36, 46), "D": (58, 56, 70), "W": (240, 240, 240),
              "G": (190, 255, 120), "P": (255, 120, 130)}


def cat_frame(step: int, size: int = 4, facing: int = 1, sleep: bool = False) -> Image.Image:
    """Chat en marche (2 frames), `facing` = 1 droite / -1 gauche (miroir).

    sleep=True : oeil remplacé par la couleur du corps (il dort).
    """
    colors = dict(CAT_COLORS)
    if sleep:
        colors["G"] = CAT_COLORS["O"]          # oeil fermé
    img = bitmap_to_image(CAT_A if step % 2 == 0 else CAT_B, colors, size)
    if facing < 0:
        from PIL import ImageOps
        img = ImageOps.mirror(img)
    return img


UMBRELLA = [
    "..1111111..",
    ".111111111.",
    "11111111111",
    ".....W.....",
    ".....W.....",
    ".....W.....",
]



# ------------------------------------------------------------------- pièce

COIN_R = 14          # rayon sprite (grille 28x28)

# Barres Solana (3 barres horizontales décalées)
SOL_BARS = [
    "1111111",
    "1111111",
    "...111.",
    "...111.",
    "1111111",
    "1111111",
    "...111.",
]

# Thèmes par token : OUT contour, SHADE ombre, BASE face, HIGH reflet, SYM glyphe.
# "glyph" : bitmap dédié, ou une lettre rendue depuis la police pixel (seuillée).
COIN_THEMES = {
    "BTC":  {"colors": [(120, 62, 12), (235, 145, 28), (250, 190, 44), (255, 232, 130), (105, 55, 10)], "glyph": BITCOIN_B},
    "ETH":  {"colors": [(52, 56, 72), (132, 140, 160), (198, 204, 218), (240, 244, 250), (52, 56, 72)], "glyph": ETH_DIAMOND},
    "SOL":  {"colors": [(38, 14, 74), (86, 32, 168), (119, 69, 255), (20, 241, 149), (238, 238, 255)], "glyph": SOL_BARS},
    "AAVE": {"colors": [(40, 16, 64), (120, 40, 130), (181, 80, 158), (46, 186, 198), (240, 250, 255)], "glyph": "A"},
    "ONDO": {"colors": [(8, 20, 48), (16, 48, 104), (28, 76, 158), (120, 170, 235), (235, 245, 255)], "glyph": "O"},
    "ENA":  {"colors": [(24, 24, 30), (38, 38, 46), (66, 64, 76), (150, 150, 160), (255, 168, 54)], "glyph": "E"},
    "HYPE": {"colors": [(10, 16, 14), (18, 34, 28), (30, 58, 48), (94, 244, 196), (183, 252, 228)], "glyph": "H"},
}


def _letter_glyph(letter: str) -> Image.Image:
    """Lettre en police pixel rendue en bitmap net (seuil, pas d'anti-aliasing)."""
    from .render import font
    f = font(12)
    mask = f.getmask(letter, mode="L")
    w, h = mask.size
    return Image.frombytes("L", (w, h), bytes(mask)).point(lambda p: 255 if p > 128 else 0)


@lru_cache(maxsize=None)
def coin_sprite(symbol: str = "BTC") -> Image.Image:
    """Pièce face complète, grille native 28x28 (transparent hors pièce).

    Rendu : cerclage extérieur (OUT) avec reflet HIGH en haut-gauche,
    disque BASE ombré SHADE en bas-droite, glyphe SYM centré.
    """
    theme = COIN_THEMES.get(symbol, COIN_THEMES["BTC"])
    OUT, SHADE, BASE, HIGH, SYM = theme["colors"]

    n = COIN_R * 2
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    px = img.load()
    c = n / 2 - 0.5
    for y in range(n):
        for x in range(n):
            dx, dy = x - c, y - c
            r = math.hypot(dx, dy)
            if r > COIN_R:
                continue
            d = dx + dy  # direction lumière : haut-gauche clair
            if r > COIN_R - 2:                       # cerclage
                col = HIGH if d < -8 else OUT
            elif r > COIN_R - 5 and d > 8:           # ombre interne
                col = SHADE
            elif r > COIN_R - 5 and d < -10:         # reflet interne
                col = HIGH
            else:
                col = BASE
            px[x, y] = (*col, 255)

    glyph = theme["glyph"]
    if isinstance(glyph, str):                       # lettre -> bitmap seuillé
        gimg = _letter_glyph(glyph)
        gx = (n - gimg.width) // 2
        gy = (n - gimg.height) // 2
        for yy in range(gimg.height):
            for xx in range(gimg.width):
                if gimg.getpixel((xx, yy)):
                    px[gx + xx, gy + yy] = (*SYM, 255)
    else:                                            # bitmap explicite
        gh, gw = len(glyph), len(glyph[0])
        gx = (n - gw) // 2
        gy = (n - gh) // 2
        for yy, row in enumerate(glyph):
            for xx, ch in enumerate(row):
                if ch == "1":
                    px[gx + xx, gy + yy] = (*SYM, 255)
    return img


# Nombre de frames de l'animation de rotation (frame N = frame 0, boucle propre)
ROTATION_FRAMES = 12


@lru_cache(maxsize=None)
def coin_frame(symbol: str, step: int, scale: int = 3) -> Image.Image:
    """Frame `step` de la rotation 360° : squeeze horizontal |cos(theta)|.

    Largeur en pixels sprite ARRONDIE À L'ENTIER (jamais fractionnaire),
    rééchantillonnage par colonnes entières (nearest) — pixel perfect.
    Face cachée identique (pièce symétrique), boucle = ROTATION_FRAMES steps.
    """
    theta = 2 * math.pi * step / ROTATION_FRAMES
    src = coin_sprite(symbol)
    n = src.width

    width = round(n * abs(math.cos(theta)))
    width = max(width, 2)  # tranche minimale : 2 px de face + contour

    frame = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    if width >= n:
        frame = src.copy()
    elif width <= 3:
        # tranche : colonne de HIGH bordée d'OUT
        px = frame.load()
        x0 = (n - width) // 2
        for y in range(n):
            for i in range(width):
                px[x0 + i, y] = (*HIGH, 255) if 0 < i < width - 1 else (*OUT, 255)
    else:
        # squeeze : chaque colonne cible prend la colonne source la plus proche
        sp, fp = src.load(), frame.load()
        for x in range(width):
            sx = (x * n) // width
            sx = min(sx, n - 1)
            for y in range(n):
                fp[(n - width) // 2 + x, y] = sp[sx, y]
    return frame.resize((n * scale, n * scale), Image.NEAREST)
