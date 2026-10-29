"""Installation guidée de Geek Magic Vibe : un seul script après `git clone`.

    python setup.py              # installation interactive
    python setup.py --yes        # accepte tout (tâches planifiées incluses sous Windows)
    python setup.py --no-scan    # ne cherche pas l'écran sur le réseau

Étapes : environnement virtuel (.venv) -> dépendances -> polices pixel ->
config.json -> recherche de l'écran -> (Windows) tâches planifiées -> test.
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
    suffix = "[O/n]" if default_yes else "[o/N]"
    answer = input(f"{question} {suffix} ").strip().lower()
    return default_yes if not answer else answer in ("o", "oui", "y", "yes")


def install_tasks() -> None:
    """Deux tâches Windows : cryptos+météo toutes les 9 min, horloge chaque minute."""
    jobs = [("GeekMagicDashRefresh", 9, "refresh_all.py"), ("GeekMagicClock", 1, "send_clock.py")]
    for name, every, script in jobs:
        tr = f'"{PYW}" "{ROOT / "scripts" / script}"'
        rc = subprocess.run(["schtasks", "/Create", "/F", "/SC", "MINUTE", "/MO", str(every), "/TN", name, "/TR", tr],
                            cwd=ROOT, capture_output=True, text=True)
        print(f"    {'OK ' if rc.returncode == 0 else 'ECHEC'} {name} (toutes les {every} min)"
              + ("" if rc.returncode == 0 else f" : {rc.stderr.strip()}"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--yes", action="store_true", help="répond oui à toutes les questions")
    ap.add_argument("--no-scan", action="store_true", help="ne cherche pas l'écran sur le réseau")
    args = ap.parse_args()
    total = 6

    if sys.version_info < (3, 11):
        print(f"[!] Python 3.11 ou plus requis (version actuelle : {sys.version.split()[0]}).")
        return 1
    print("Geek Magic Vibe : installation")
    for d in ("output", "logs"):
        (ROOT / d).mkdir(exist_ok=True)

    step(1, total, "Environnement virtuel (.venv)")
    if not PY.exists():
        run(sys.executable, "-m", "venv", VENV)
    print("    ok")

    step(2, total, "Dépendances (Pillow, requests, FastAPI, uvicorn)")
    run(PY, "-m", "pip", "install", "--quiet", "--upgrade", "pip")
    run(PY, "-m", "pip", "install", "--quiet", "-r", ROOT / "requirements.txt")
    print("    ok")

    step(3, total, "Polices pixel (Press Start 2P, Silkscreen : licence OFL)")
    if not (ROOT / "fonts" / "PressStart2P-Regular.ttf").exists():
        if run(PY, ROOT / "scripts" / "setup_fonts.py", check=False) != 0:
            print("[!] Téléchargement impossible : relancez setup.py avec une connexion Internet.")
            return 1
    else:
        print("    déjà présentes")

    step(4, total, "Configuration (config.json)")
    cfg = ROOT / "config.json"
    if not cfg.exists():
        cfg.write_text((ROOT / "config.example.json").read_text(encoding="utf-8"), encoding="utf-8")
        print("    config.json créé à partir de config.example.json")
    else:
        print("    config.json existe déjà, conservé")

    step(5, total, "Recherche de l'écran sur le réseau")
    if args.no_scan:
        print("    ignorée (--no-scan) : renseignez l'IP dans le backoffice")
    elif run(PY, ROOT / "scripts" / "find_device.py", check=False) != 0:
        print("    écran non trouvé : vous pourrez saisir son IP dans le backoffice (Écran et planning)")

    step(6, total, "Mise à jour automatique (tâches planifiées Windows)")
    if WIN and ask("Installer les tâches planifiées (cryptos et météo toutes les 9 min, horloge chaque minute) ?", True, args.yes):
        install_tasks()
    else:
        print("    ignorée")

    print("\nTerminé. Lancez le backoffice :")
    print("    Windows : double-clic sur 'Lancer le backoffice.bat'" if WIN else f"    {PY} backoffice/server.py")
    print("    puis ouvrez http://localhost:8780")
    if ask("Lancer le backoffice maintenant ?", True, False):
        if WIN:
            os.startfile(ROOT / "Lancer le backoffice.bat")  # type: ignore[attr-defined]
        else:
            run(PY, ROOT / "backoffice" / "server.py", check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
