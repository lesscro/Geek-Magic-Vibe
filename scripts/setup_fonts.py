"""Télécharge les polices pixel art (OFL / libres de droits) dans fonts/."""

from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"

# Press Start 2P (OFL) — la référence pixel art, lisible en petit.
PRESS_START_2P = "https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf"
# Silkscreen (OFL) — alternative plus fine pour les petits corps.
SILKSCREEN = "https://github.com/google/fonts/raw/main/ofl/silkscreen/Silkscreen-Regular.ttf"


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "python"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        dest.write_bytes(resp.read())
    print(f"[+] {dest.name} ({dest.stat().st_size} octets)")


def main() -> int:
    FONTS_DIR.mkdir(exist_ok=True)
    try:
        download(PRESS_START_2P, FONTS_DIR / "PressStart2P-Regular.ttf")
        download(SILKSCREEN, FONTS_DIR / "Silkscreen-Regular.ttf")
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Téléchargement échoué : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
