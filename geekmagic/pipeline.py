"""Orchestration : config -> GIF des cards actives -> écran (avec nettoyage).

Nom des fichiers sur l'écran : `<NN><code>_<clé>` + 1/2 alterné, avec NN la
position dans la rotation (ordre choisi dans le backoffice) et code tk (token),
wx (météo), ck (horloge). Le firmware lit l'album par nom : le préfixe NN fixe l'ordre.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from . import data, i18n, settings, weather  # noqa: E402
from .client import GeekMagicClient, GeekMagicError  # noqa: E402

OUTPUT = ROOT / "output"
CODES = {"crypto": "tk", "weather": "wx", "clock": "ck"}
MANAGED = re.compile(r"^(\d{2})(tk|wx|ck)_([a-z0-9]+)([12])\.gif$")
LEGACY = {"crypto": ["btc", "eth", "sol", "aave", "ondo", "ena", "hype", "bnb", "xrp", "doge"],
          "weather": ["meteo"], "clock": ["horloge"]}

Log = Callable[[str], None]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())[:10] or "x"


def plan(cfg: dict) -> list[dict]:
    """Entrées de rotation dans l'ordre choisi (items activés, cards activées)."""
    entries, pos = [], 1
    for kind in cfg["schedule"]["order"]:
        if not cfg["schedule"][kind]["enabled"]:
            continue
        if kind == "clock":
            items = [("clock", "Horloge", "")]
        elif kind == "weather":
            items = [(l["id"], l["city"], l["id"]) for l in cfg["weather"]["locations"] if l["enabled"]]
        else:
            items = [(t["pair"], t["pair"].split("/")[0], t["pair"].split("/")[0])
                     for t in cfg["crypto"]["tokens"] if t["enabled"]]
        for key, label, slug in items:
            stem = f"{pos:02d}{CODES[kind]}_{_slug(slug or key)}"
            entries.append({"kind": kind, "key": key, "label": label, "stem": stem, "pos": pos})
            pos += 1
    return entries


def _device_names(client: GeekMagicClient) -> set[str]:
    html = client.list_images()
    return {m.rsplit("/", 1)[-1] for m in re.findall(r"href='(/image/[^']+)'", html)}


def _cleanup(client: GeekMagicClient, kind: str, keep_stems: set[str], log: Log) -> None:
    """Supprime de l'écran les fichiers de cette card qui ne sont plus voulus."""
    code = CODES[kind]
    legacy = {f"{s}{n}.gif" for s in LEGACY[kind] for n in (1, 2)}
    for name in sorted(_device_names(client)):
        m = MANAGED.match(name)
        stale = False
        if m and m.group(2) == code:
            stale = f"{m.group(1)}{m.group(2)}_{m.group(3)}" not in keep_stems
        elif name in legacy:
            stale = True
        if stale:
            client.delete(name)
            log(f"    removed from the screen: {name}")


LOCK = ROOT / "logs" / "device.lock"


class _DeviceLock:
    """Verrou inter-processus : l'écran est mono-tâche, deux envois simultanés
    (tâche planifiée + backoffice) se font échouer mutuellement."""

    def __enter__(self):
        import os
        import time
        LOCK.parent.mkdir(exist_ok=True)
        deadline = time.time() + 240
        while True:
            try:
                self.fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                if time.time() - LOCK.stat().st_mtime > 300:      # verrou périmé (crash)
                    LOCK.unlink(missing_ok=True)
                elif time.time() > deadline:
                    raise GeekMagicError("Another send to the screen is in progress")
                else:
                    time.sleep(1.5)

    def __exit__(self, *exc):
        import os
        os.close(self.fd)
        LOCK.unlink(missing_ok=True)


def run(cfg: dict, kinds: list[str] | None = None, log: Log = print,
        now: datetime | None = None, push: bool = True) -> dict:
    """Génère et envoie les cards demandées. Renvoie un résumé {kind: [stems]}."""
    if push:
        with _DeviceLock():
            return _run(cfg, kinds, log, now, push)
    return _run(cfg, kinds, log, now, push)


def _run(cfg: dict, kinds: list[str] | None, log: Log, now: datetime | None, push: bool) -> dict:
    from scripts import send_clock, send_tokens, send_weather
    i18n.use(cfg.get("language"))
    tz = ZoneInfo(cfg["clock"]["timezone"])
    now = now or datetime.now(tz)
    kinds = kinds or list(settings.KINDS)
    entries = plan(cfg)
    client = GeekMagicClient(cfg["device"]["ip"], timeout=10) if push else None
    OUTPUT.mkdir(exist_ok=True)
    done: dict[str, list[str]] = {}

    if push and "crypto" in kinds:
        client.set_theme(3)
        client.set_album(autoplay=True, interval_s=cfg["crypto"]["cycle"])

    for kind in kinds:
        mine = [e for e in entries if e["kind"] == kind]
        active = settings.card_active(cfg, kind, now)
        if not active or not mine:
            if push:
                _cleanup(client, kind, set(), log)
            log(f"[-] {kind}: outside its time slot or disabled")
            done[kind] = []
            continue
        pushed = []
        for e in mine:
            gif = OUTPUT / f"{e['stem']}.gif"
            try:
                if kind == "crypto":
                    snap = data.get_market(e["key"])
                    send_tokens.build_token_gif(snap, gif)
                    log(f"[+] {snap.pair} {snap.change_24h:+.2f}%")
                elif kind == "weather":
                    loc = next(l for l in cfg["weather"]["locations"] if l["id"] == e["key"])
                    w = weather.get_weather(loc)
                    place = None if loc["scene"] == "auto" else loc["scene"]
                    send_weather.build_weather_gif(w, gif, place=place, allowed=cfg["weather"]["scenes_enabled"])
                    log(f"[+] weather {loc['city']} {w.temp:.0f}° {w.icon}")
                else:
                    w = None
                    if cfg["clock"]["show_weather"]:
                        locs = cfg["weather"]["locations"]
                        loc = next((l for l in locs if l["id"] == cfg["clock"]["location"]), locs[0] if locs else None)
                        try:
                            w = weather.get_weather(loc) if loc else None
                        except Exception as exc:  # noqa: BLE001 — l'heure prime sur la météo
                            log(f"[!] weather unavailable for the clock ({exc})")
                    effect = None if cfg["clock"]["effect"] == "random" else cfg["clock"]["effect"]
                    _, used = send_clock.build_clock_gif(now, w, effect, out=gif,
                                                         night_hours=(cfg["clock"]["night_start"], cfg["clock"]["night_end"]))
                    log(f"[+] clock {now:%H:%M} (entry: {used})")
                if push:
                    send_tokens.push_gif_alternating(client, gif)
                pushed.append(e["stem"])
            except (data.DataError, weather.WeatherError, GeekMagicError, OSError) as exc:
                log(f"[!] {e['label']} : {exc}")
        if push:
            _cleanup(client, kind, {e["stem"] for e in mine}, log)
        done[kind] = pushed
    return done
