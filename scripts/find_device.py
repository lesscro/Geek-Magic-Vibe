"""Scanne le réseau local pour retrouver le GeekMagic (réponse caractéristique /spaces.json).

Usage : python scripts/find_device.py [--subnet 192.168.1] [--port 80]
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subnet", default="192.168.1", help="3 premiers octets (défaut 192.168.1)")
    ap.add_argument("--port", type=int, default=80)
    args = ap.parse_args()

    print(f"Scan de {args.subnet}.1-254 sur le port {args.port}...")
    hits = scan(args.subnet, args.port)
    if not hits:
        print("[!] Aucun serveur JSON trouvé. L'écran est-il bien connecté à ce réseau ?")
        return 1

    print(f"[+] Candidats GeekMagic : {', '.join(hits)}")
    if len(hits) == 1:
        ip = hits[0]
        print(f"[+] Écran trouvé : {ip}")
        cfg_path = ROOT / "config.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["device_ip"] = ip
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[+] config.json mis à jour (device_ip = {ip}). Lancez scripts/send_test.py.")
    else:
        print("→ Plusieurs candidats : ouvrez http://<IP>/spaces.json dans un navigateur")
        print("  pour identifier l'écran, puis mettez à jour config.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
