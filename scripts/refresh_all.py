"""Rafraîchit les cards données (cryptos + météo) selon la config du backoffice.

Conçu pour la tâche planifiée GeekMagicDashRefresh (silencieux sous pythonw,
log dans logs/refresh.log). Respecte la cadence `device.refresh_minutes` et les
créneaux de chaque card ; l'horloge a sa propre tâche (send_clock.py, 1 min).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from geekmagic import pipeline, settings  # noqa: E402

LOG = ROOT / "logs" / "refresh.log"
STAMP = ROOT / "logs" / "last_refresh.txt"


def _log(line: str) -> None:
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def main() -> int:
    cfg = settings.load()
    every = cfg["device"]["refresh_minutes"] * 60
    if STAMP.exists() and time.time() - float(STAMP.read_text() or 0) < every - 90:
        return 0                                  # trop tôt : la cadence choisie n'est pas atteinte
    _log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] refresh")
    try:
        done = pipeline.run(cfg, ["crypto", "weather"], log=_log)
        STAMP.write_text(str(time.time()))
        _log(f"    OK {done}")
        return 0
    except Exception as exc:  # noqa: BLE001 — la tâche planifiée ne doit jamais lever
        _log(f"    ECHEC {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
