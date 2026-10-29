"""Test de communication Étape 1 : génère une image fixe 240x240 (layout 3 cards)
et la pousse sur l'écran GeekMagic.

Usage : python scripts/send_test.py [--ip X.X.X.X] [--keep]
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from geekmagic import GeekMagicClient, GeekMagicError  # noqa: E402

FONT_PATH = ROOT / "fonts" / "PressStart2P-Regular.ttf"
OUTPUT = ROOT / "output" / "test_frame.jpg"  # PNG non supporté par le firmware

# Palette sombre lisible sur LED
BG = (12, 12, 20)
ACCENT = (0, 255, 170)
ACCENT_2 = (255, 80, 80)
TEXT = (230, 230, 230)
DIM = (90, 90, 110)

LAYOUT = [(0, 0, 240, 80), (0, 80, 240, 170), (0, 170, 240, 240)]  # x0,y0,x1,y1


def local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "?"


def draw_test_frame() -> Image.Image:
    from PIL import ImageFont

    img = Image.new("RGB", (240, 240), BG)
    d = ImageDraw.Draw(img)
    f_big = ImageFont.truetype(str(FONT_PATH), 16)
    f_mid = ImageFont.truetype(str(FONT_PATH), 10)
    f_small = ImageFont.truetype(str(FONT_PATH), 8)

    titles = ["HORLOGE/METEO", "CRYPTO", "AGENDA"]
    colors = [ACCENT, ACCENT_2, DIM]
    for (x0, y0, x1, y1), title, color in zip(LAYOUT, titles, colors):
        d.rectangle([x0 + 2, y0 + 2, x1 - 3, y1 - 3], outline=color, width=1)
        d.text((x0 + 8, y0 + 8), title, font=f_small, fill=color)

    d.text((10, 40), datetime.now().strftime("%H:%M"), font=f_big, fill=TEXT)
    d.text((130, 40), "14 C", font=f_mid, fill=TEXT)  # "°" absent de Press Start 2P
    d.text((10, 105), "BTC/USDT", font=f_mid, fill=TEXT)
    d.text((10, 125), "+4.2%", font=f_big, fill=ACCENT)
    d.text((10, 185), "TEST OK", font=f_big, fill=TEXT)
    d.text((10, 215), datetime.now().strftime("%d/%m %H:%M:%S"), font=f_small, fill=DIM)
    return img


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip", default=None, help="IP de l'écran (défaut : config.json)")
    args = ap.parse_args()

    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    ip = args.ip or cfg["device_ip"]

    if not FONT_PATH.exists():
        print(f"[!] Police manquante : {FONT_PATH}")
        print("    Lancez : python scripts/setup_fonts.py")
        return 2

    OUTPUT.parent.mkdir(exist_ok=True)
    draw_test_frame().convert("RGB").save(OUTPUT, quality=90)
    print(f"[+] Image de test générée : {OUTPUT}")

    client = GeekMagicClient(ip, timeout=8)
    if not client.reachable():
        print(f"[!] Écran injoignable sur {ip}")
        print(f"    IP locale du PC : {local_ip()}")
        print("    -> Vérifiez que le PC et l'écran sont sur le MÊME réseau"
              " (même sous-réseau requis).")
        return 1

    try:
        # Thème Photo Album obligatoire : pas de /set?img= sur ce firmware,
        # l'affichage passe par le cycle automatique de l'album.
        client.set_theme(3)
        client.set_album(autoplay=True, interval_s=60)  # fondu seulement à chaque refresh
        client.push_image(str(OUTPUT), name="dashboard_test.jpg")
    except GeekMagicError as exc:
        print(f"[!] Échec : {exc}")
        return 1

    print(f"[+] Envoyé sur {ip} — visible à l'écran d'ici ~5 s (cycle album).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
