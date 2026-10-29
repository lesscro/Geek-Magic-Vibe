"""Scanne le réseau local pour retrouver le GeekMagic (réponse caractéristique /spaces.json).

Usage : python scripts/find_device.py [--subnet 192.168.1] [--port 80]
(sans --subnet : sous-réseau du PC détecté automatiquement)
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import socket
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def probe(ip: str, port: int, timeout: float) -> str | None:
    """Retourne l'IP si un serveur HTTP répond avec du JSON sur /config.json.

    /spaces.json renvoie 404 sur notre firmware (HelloCubic-Lite) ;
    /config.json contient {"a": "<SSID>", "p": "****"} — caractéristique.
    """
    url = f"http://{ip}:{port}/config.json"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read(300)
            if resp.headers.get("Content-Type", "").startswith("text/json") or body.strip().startswith(b"{"):
                if b'"a"' in body and b'"p"' in body:
                    return ip
    except urllib.error.HTTPError:
        return None
    except (urllib.error.URLError, socket.timeout, ConnectionError, ValueError):
        return None
    return None


def scan(subnet: str, port: int, timeout: float = 1.5) -> list[str]:
    hosts = [f"{subnet}.{i}" for i in range(1, 255)]
    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as pool:
        futures = {pool.submit(probe, ip, port, timeout): ip for ip in hosts}
        for fut in concurrent.futures.as_completed(futures):
            if fut.result():
                found.append(fut.result())
    return sorted(found, key=lambda ip: int(ip.rsplit(".", 1)[1]))


def local_subnet() -> str | None:
    """3 premiers octets de l'IP locale du PC (sous-réseau probable de l'écran)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))            # aucun paquet envoyé : sert à choisir l'interface
            return sock.getsockname()[0].rsplit(".", 1)[0]
    except OSError:
        return None


def find(subnet: str | None = None, port: int = 80) -> list[str]:
    subnet = subnet or local_subnet() or "192.168.1"
    print(f"Scan de {subnet}.1-254 sur le port {port}...")
    return scan(subnet, port)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subnet", default=None, help="3 premiers octets (défaut : sous-réseau du PC)")
    ap.add_argument("--port", type=int, default=80)
    args = ap.parse_args()

    hits = find(args.subnet, args.port)
    if not hits:
        print("[!] Aucun écran trouvé. Est-il allumé et sur le même réseau que ce PC ?")
        return 1

    print(f"[+] Candidats GeekMagic : {', '.join(hits)}")
    if len(hits) == 1:
        sys.path.insert(0, str(ROOT))
        from geekmagic import settings
        cfg = settings.load()
        cfg["device"]["ip"] = hits[0]
        settings.save(cfg)
        print(f"[+] Écran trouvé : {hits[0]} (enregistré dans config.json)")
    else:
        print("-> Plusieurs candidats : renseignez la bonne adresse dans le backoffice (Écran et planning).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
