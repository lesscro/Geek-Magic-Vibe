"""Configuration unique du dashboard (config.json) : défauts, migration, sauvegarde.

Le backoffice et les scripts lisent et écrivent le même fichier. Les anciennes
clés (device_ip, crypto.pairs, weather.city/lat/lon) sont migrées au chargement
et `device_ip` reste écrit pour les scripts historiques (find_device, send_test).
"""

from __future__ import annotations

import copy
import json
import os
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(os.environ.get("GMV_CONFIG") or ROOT / "config.json")

KINDS = ("clock", "weather", "crypto")
SCENES = ["city", "cafe", "market", "bridge", "park", "playground", "picnic", "lake",
          "mountains", "farm", "harbor", "beach"]
EFFECTS = ["random", "fade", "slide_left", "slide_right", "slide_up", "slide_down",
           "zoom", "wipe", "dissolve", "iris"]
MAX_LOCATIONS = 3

DEFAULTS: dict = {
    "language": "en",
    "device": {"ip": "192.168.1.100", "refresh_minutes": 9},
    "resolution": [240, 240],
    "crypto": {
        "cycle": 10,
        "tokens": [{"pair": p, "enabled": True} for p in
                   ("BTC/USDT", "ETH/USDT", "SOL/USDT", "AAVE/USDT", "ONDO/USDT", "ENA/USDT", "HYPE/USDT")],
    },
    "weather": {
        "scenes_enabled": list(SCENES),
        "locations": [{"id": "paris", "city": "Paris", "lat": 48.8566,
                       "lon": 2.3522, "timezone": "Europe/Paris", "enabled": True, "scene": "auto"}],
    },
    "clock": {"timezone": "Europe/Paris", "night_start": 22, "night_end": 7,
              "effect": "random", "show_weather": True, "location": "paris"},
    "schedule": {
        "order": ["clock", "weather", "crypto"],
        "clock": {"enabled": True, "slots": [["00:00", "24:00"]]},
        "weather": {"enabled": True, "slots": [["00:00", "24:00"]]},
        "crypto": {"enabled": True, "slots": [["00:00", "24:00"]]},
    },
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())[:10] or "lieu"


def _migrate(raw: dict) -> dict:
    """Ancien format -> nouveau (sans perdre d'information)."""
    raw = copy.deepcopy(raw)
    if "device" not in raw and raw.get("device_ip"):
        raw["device"] = {"ip": raw["device_ip"]}
    crypto = raw.get("crypto", {})
    if "pairs" in crypto and "tokens" not in crypto:
        crypto["tokens"] = [{"pair": p, "enabled": True} for p in crypto["pairs"]]
        crypto.pop("pairs")
        raw["crypto"] = crypto
    wx = raw.get("weather", {})
    if "locations" not in wx and wx.get("lat") is not None:
        loc = {"id": _slug(wx.get("city", "lieu")), "city": wx.get("city", "Lieu"), "lat": wx["lat"],
               "lon": wx["lon"], "timezone": wx.get("timezone", "Europe/Paris"), "enabled": True,
               "scene": "auto"}
        raw["weather"] = {"locations": [loc]}
    return raw


def load() -> dict:
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
    cfg = _merge(DEFAULTS, _migrate(raw))
    cfg["device_ip"] = cfg["device"]["ip"]
    return cfg


def validate(cfg: dict) -> dict:
    """Nettoie et borne une config reçue du backoffice (jamais de confiance aveugle)."""
    out = _merge(DEFAULTS, cfg)
    out["language"] = out.get("language") if out.get("language") in ("en", "fr") else "en"
    ip = str(out["device"].get("ip", "")).strip()
    if not re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", ip):
        raise ValueError("Invalid IP address")
    out["device"]["ip"] = ip
    out["device"]["refresh_minutes"] = max(3, min(120, int(out["device"].get("refresh_minutes", 9))))
    out["crypto"]["cycle"] = max(3, min(120, int(out["crypto"].get("cycle", 10))))
    seen, tokens = set(), []
    for t in out["crypto"]["tokens"]:
        pair = str(t.get("pair", "")).upper().strip()
        if re.fullmatch(r"[A-Z0-9]{2,12}/[A-Z]{3,5}", pair) and pair not in seen:
            seen.add(pair)
            tokens.append({"pair": pair, "enabled": bool(t.get("enabled", True))})
    out["crypto"]["tokens"] = tokens[:12]
    locs, ids = [], set()
    for loc in out["weather"]["locations"][:MAX_LOCATIONS]:
        lid = _slug(str(loc.get("id") or loc.get("city", "")))
        while lid in ids:
            lid += "x"
        ids.add(lid)
        scene = loc.get("scene", "auto")
        locs.append({"id": lid, "city": str(loc["city"])[:40], "lat": round(float(loc["lat"]), 4),
                     "lon": round(float(loc["lon"]), 4), "timezone": str(loc.get("timezone", "Europe/Paris")),
                     "enabled": bool(loc.get("enabled", True)),
                     "scene": scene if scene in SCENES else "auto"})
    out["weather"]["locations"] = locs
    out["weather"]["scenes_enabled"] = [s for s in out["weather"]["scenes_enabled"] if s in SCENES] or list(SCENES)
    clock = out["clock"]
    clock["night_start"] = int(clock.get("night_start", 22)) % 24
    clock["night_end"] = int(clock.get("night_end", 7)) % 24
    if clock.get("effect") not in EFFECTS:
        clock["effect"] = "random"
    sched = out["schedule"]
    order = [k for k in sched.get("order", []) if k in KINDS]
    sched["order"] = order + [k for k in KINDS if k not in order]
    for k in KINDS:
        slots = []
        for a, b in sched[k].get("slots", []):
            if re.fullmatch(r"\d{2}:\d{2}", a) and re.fullmatch(r"(\d{2}:\d{2}|24:00)", b):
                slots.append([a, b])
        sched[k] = {"enabled": bool(sched[k].get("enabled", True)), "slots": slots or [["00:00", "24:00"]]}
    out["device_ip"] = ip
    return out


def save(cfg: dict) -> dict:
    clean = validate(cfg)
    CONFIG_PATH.write_text(json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8")
    return clean


# ----------------------------------------------------------------- planning

def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def in_slots(slots: list[list[str]], now: datetime) -> bool:
    cur = now.hour * 60 + now.minute
    for a, b in slots:
        s, e = _minutes(a), _minutes(b)
        if (s <= cur < e) if s < e else (cur >= s or cur < e):
            return True
    return False


def card_active(cfg: dict, kind: str, now: datetime) -> bool:
    c = cfg["schedule"][kind]
    return bool(c["enabled"]) and in_slots(c["slots"], now)
