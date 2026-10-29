"""Guided installation of Geek Magic Vibe: one script after `git clone`.

    python setup.py              # interactive install
    python setup.py --yes        # accept everything (scheduled tasks included on Windows)
    python setup.py --no-scan    # do not look for the screen on the network

Steps: virtual environment (.venv) -> dependencies -> pixel fonts ->
config.json -> screen discovery -> (Windows) scheduled tasks.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
WIN = os.name == "nt"
PY = VENV / ("Scripts/python.exe" if WIN else "bin/python")
PYW = VENV / "Scripts/pythonw.exe"


def step(n: int, total: int, text: str) -> None:
    print(f"\n[{n}/{total}] {text}")


def run(*cmd: str | Path, check: bool = True) -> int:
    return subprocess.run([str(c) for c in cmd], cwd=ROOT, check=check).returncode


def ask(question: str, default_yes: bool, yes: bool) -> bool:
    if yes:
        return True
    suffix = "[Y/n]" if default_yes else "[y/N]"
    answer = input(f"{question} {suffix} ").strip().lower()
    return default_yes if not answer else answer in ("o", "oui", "y", "yes")


def install_tasks() -> None:
    """Two Windows tasks: crypto + weather every 9 min, clock every minute."""
    jobs = [("GeekMagicDashRefresh", 9, "refresh_all.py"), ("GeekMagicClock", 1, "send_clock.py")]
    for name, every, script in jobs:
        tr = f'"{PYW}" "{ROOT / "scripts" / script}"'
        rc = subprocess.run(["schtasks", "/Create", "/F", "/SC", "MINUTE", "/MO", str(every), "/TN", name, "/TR", tr],
                            cwd=ROOT, capture_output=True, text=True)
        print(f"    {'OK ' if rc.returncode == 0 else 'ECHEC'} {name} (every {every} min)"
              + ("" if rc.returncode == 0 else f" : {rc.stderr.strip()}"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--yes", action="store_true", help="answer yes to every question")
    ap.add_argument("--no-scan", action="store_true", help="do not look for the screen on the network")
    args = ap.parse_args()
    total = 6

    if sys.version_info < (3, 11):
        print(f"[!] Python 3.11 or newer is required (current version: {sys.version.split()[0]}).")
        return 1
    print("Geek Magic Vibe: installation")
    for d in ("output", "logs"):
        (ROOT / d).mkdir(exist_ok=True)

    step(1, total, "Virtual environment (.venv)")
    if not PY.exists():
        run(sys.executable, "-m", "venv", VENV)
    print("    ok")

    step(2, total, "Dependencies (Pillow, requests, FastAPI, uvicorn)")
    run(PY, "-m", "pip", "install", "--quiet", "--upgrade", "pip")
    run(PY, "-m", "pip", "install", "--quiet", "-r", ROOT / "requirements.txt")
    print("    ok")

    step(3, total, "Pixel fonts (Press Start 2P, Silkscreen: OFL license)")
    if not (ROOT / "fonts" / "PressStart2P-Regular.ttf").exists():
        if run(PY, ROOT / "scripts" / "setup_fonts.py", check=False) != 0:
            print("[!] Download failed: rerun setup.py with an Internet connection.")
            return 1
    else:
        print("    already present")

    step(4, total, "Configuration (config.json)")
    cfg = ROOT / "config.json"
    if not cfg.exists():
        cfg.write_text((ROOT / "config.example.json").read_text(encoding="utf-8"), encoding="utf-8")
        print("    config.json created from config.example.json")
    else:
        print("    config.json already exists, kept")

    step(5, total, "Looking for the screen on the network")
    if args.no_scan:
        print("    skipped (--no-scan): enter the IP in the backoffice")
    elif run(PY, ROOT / "scripts" / "find_device.py", check=False) != 0:
        print("    screen not found: you can enter its IP in the backoffice (Screen and schedule)")

    step(6, total, "Automatic updates (Windows scheduled tasks)")
    if WIN and ask("Install the scheduled tasks (crypto and weather every 9 min, clock every minute)?", True, args.yes):
        install_tasks()
    else:
        print("    skipped")

    print("\nDone. Start the backoffice:")
    print("    Windows: double-click 'Lancer le backoffice.bat'" if WIN else f"    {PY} backoffice/server.py")
    print("    then open http://localhost:8780")
    if ask("Start the backoffice now?", True, False):
        if WIN:
            os.startfile(ROOT / "Lancer le backoffice.bat")  # type: ignore[attr-defined]
        else:
            run(PY, ROOT / "backoffice" / "server.py", check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
