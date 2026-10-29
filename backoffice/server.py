"""Backoffice local GeekMagic : API + interface (FastAPI, aucun build).

Lancement : python backoffice/server.py  (http://localhost:8780, aussi joignable
depuis un téléphone du même réseau). Pas d'authentification : réseau local de confiance.
"""

from __future__ import annotations

import dataclasses
import io
import json
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from geekmagic import data, i18n, pipeline, places, render, scenes, settings, weather  # noqa: E402
from geekmagic.client import GeekMagicClient, GeekMagicError  # noqa: E402
from scripts import send_clock, send_tokens, send_weather  # noqa: E402

PORT = int(__import__("os").environ.get("GMV_PORT") or 8780)
(ROOT / "output").mkdir(exist_ok=True)
(ROOT / "logs").mkdir(exist_ok=True)
STATIC = Path(__file__).resolve().parent / "static"
UA = {"User-Agent": "Mozilla/5.0 (geekmagic-backoffice)"}

app = FastAPI(title="GeekMagic backoffice", docs_url=None, redoc_url=None)

# ------------------------------------------------------------------ caches

_cache: dict[str, tuple[float, object]] = {}
_lock = threading.Lock()


def cached(key: str, ttl: float, make):
    now = time.time()
    with _lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < ttl:
            return hit[1]
    value = make()
    with _lock:
        _cache[key] = (now, value)
        if len(_cache) > 120:
            for k in sorted(_cache, key=lambda k: _cache[k][0])[:40]:
                _cache.pop(k, None)
    return value


def _json_get(url: str, timeout: float = 8.0):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


# ------------------------------------------------------------------ config

@app.get("/api/config")
def get_config():
    return settings.load()


@app.put("/api/config")
def put_config(cfg: dict = Body(...)):
    try:
        return settings.save(cfg)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(422, f"Configuration rejected: {exc}")


@app.get("/api/meta")
def meta():
    return {"scenes": settings.SCENES, "effects": settings.EFFECTS, "plan": pipeline.plan(settings.load()),
            "max_locations": settings.MAX_LOCATIONS}


# ------------------------------------------------------------------ écran

_last_good: dict[str, tuple[float, dict]] = {}


def _device_state(ip: str) -> dict:
    """État de l'écran. Le firmware est mono-tâche : un échec isolé pendant un envoi
    ne doit pas faire croire qu'il est hors ligne (on garde le dernier état 90 s)."""
    out = {"online": False, "ip": ip}
    for attempt in range(2):
        try:
            client = GeekMagicClient(ip, timeout=4)
            if not client.reachable():
                continue
            out["online"] = True
            space = client.free_space()
            out["total"], out["free"] = int(space.get("total", 0)), int(space.get("free", 0))
            html = client.list_images()
            out["files"] = sorted({m.rsplit("/", 1)[-1] for m in re.findall(r"href='(/image/[^']+)'", html)})
            _last_good[ip] = (time.time(), out)
            return out
        except (GeekMagicError, OSError, ValueError, KeyError):
            time.sleep(0.4)
    good = _last_good.get(ip)
    if good and time.time() - good[0] < 90:
        return {**good[1], "busy": True}
    return out


def _last_known(ip: str) -> dict:
    """Pendant un envoi on ne sonde pas l'écran (il est mono-tâche) : dernier état connu."""
    good = _last_good.get(ip)
    return {**good[1], "busy": True} if good else {"online": True, "ip": ip, "busy": True}


@app.get("/api/status")
def status():
    cfg = settings.load()
    tz = ZoneInfo(cfg["clock"]["timezone"])
    now = datetime.now(tz)
    stamp = ROOT / "logs" / "last_refresh.txt"
    last = float(stamp.read_text()) if stamp.exists() and stamp.read_text().strip() else None
    return {
        "device": _last_known(cfg["device"]["ip"]) if _send["running"]
        else cached(f"dev:{cfg['device']['ip']}", 5, lambda: _device_state(cfg["device"]["ip"])),
        "now": now.isoformat(timespec="seconds"),
        "active": {k: settings.card_active(cfg, k, now) for k in settings.KINDS},
        "plan": pipeline.plan(cfg),
        "last_refresh": last,
        "send": _send,
    }


@app.post("/api/device/test")
def device_test(body: dict = Body(...)):
    ip = str(body.get("ip", "")).strip()
    if not re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", ip):
        raise HTTPException(422, "Invalid IP address")
    return _device_state(ip)


# ------------------------------------------------------------------ envoi

_send: dict = {"running": False, "log": [], "ok": None, "finished": None}


def _do_send(kinds: list[str]) -> None:
    def log(line: str) -> None:
        _send["log"].append(line)
    try:
        pipeline.run(settings.load(), kinds, log=log)
        _send["ok"] = True
    except Exception as exc:  # noqa: BLE001 — remonté à l'interface
        log(f"[!] {exc}")
        _send["ok"] = False
    finally:
        _send["running"], _send["finished"] = False, time.time()
        _cache.pop(f"dev:{settings.load()['device']['ip']}", None)


@app.post("/api/send")
def send(body: dict = Body(default={})):
    if _send["running"]:
        raise HTTPException(409, "A send is already in progress")
    kinds = [k for k in body.get("kinds", settings.KINDS) if k in settings.KINDS]
    _send.update(running=True, log=[], ok=None, finished=None)
    threading.Thread(target=_do_send, args=(kinds,), daemon=True).start()
    return _send


# ------------------------------------------------------------------ recherche

@app.get("/api/geocode")
def geocode(q: str = Query(min_length=2, max_length=60)):
    url = ("https://geocoding-api.open-meteo.com/v1/search?count=6&language=fr&name="
           + urllib.parse.quote(q))
    try:
        res = _json_get(url).get("results", [])
    except OSError as exc:
        raise HTTPException(502, f"Search unavailable: {exc}")
    return [{"city": r["name"], "region": r.get("admin1", ""), "country": r.get("country", ""),
             "lat": r["latitude"], "lon": r["longitude"], "timezone": r.get("timezone", "Europe/Paris")}
            for r in res]


def _all_prices() -> dict[str, float]:
    rows = _json_get("https://api.binance.com/api/v3/ticker/price", timeout=10)
    return {r["symbol"][:-4]: float(r["price"]) for r in rows if r["symbol"].endswith("USDT")}


@app.get("/api/crypto/search")
def crypto_search(q: str = Query(min_length=1, max_length=12)):
    try:
        prices = cached("prices", 600, _all_prices)
    except OSError as exc:
        raise HTTPException(502, f"Market unavailable: {exc}")
    q = q.upper().strip()
    hits = sorted((s for s in prices if s.startswith(q)), key=lambda s: (len(s), s))[:8]
    return [{"pair": f"{s}/USDT", "symbol": s, "price": prices[s]} for s in hits]


@app.get("/api/crypto/quotes")
def crypto_quotes(pairs: str):
    syms = [p.split("/")[0].upper() for p in pairs.split(",") if re.fullmatch(r"[A-Za-z0-9]{2,12}/[A-Za-z]{3,5}", p)][:12]
    if not syms:
        return {}

    def make():
        arg = urllib.parse.quote(json.dumps([s + "USDT" for s in syms], separators=(",", ":")))
        rows = _json_get(f"https://api.binance.com/api/v3/ticker/24hr?type=MINI&symbols={arg}", timeout=8)
        return {r["symbol"][:-4] + "/USDT": {"price": float(r["lastPrice"]),
                "change": (float(r["lastPrice"]) / float(r["openPrice"]) - 1) * 100 if float(r["openPrice"]) else 0.0}
                for r in rows}
    try:
        return cached("q:" + ",".join(syms), 45, make)
    except OSError:
        return {}


# ------------------------------------------------------------------ aperçus

MOMENT_HOURS = {"AURORE": 7.2, "MATIN": 9.5, "JOURNEE": 12.0, "APRES-MIDI": 15.0,
                "CREPUSCULE": 19.8, "NUIT": 23.0}
SAMPLE = weather.WeatherSnapshot(city="Aperçu", temp=21, feels=21, code=0, is_day=True, icon="SUN",
                                 phase="APRES-MIDI", meal=None, wind=8, season="SUMMER", hour=15,
                                 doy=120, year=2026)


def _loc(cfg: dict, loc_id: str | None) -> dict:
    locs = cfg["weather"]["locations"]
    return next((l for l in locs if l["id"] == loc_id), locs[0])


def _live_weather(loc: dict) -> weather.WeatherSnapshot:
    key = f"wx:{loc['lat']}:{loc['lon']}"
    try:
        return cached(key, 300, lambda: weather.get_weather(loc))
    except Exception:  # noqa: BLE001 — repli : météo d'exemple, l'aperçu doit toujours s'afficher
        return dataclasses.replace(SAMPLE, city=loc["city"])


def _simulate(w: weather.WeatherSnapshot, moment: str | None, cond: str | None,
              temp: float | None, season: str | None) -> weather.WeatherSnapshot:
    over: dict = {}
    if moment in MOMENT_HOURS:
        over.update(phase=moment, hour=MOMENT_HOURS[moment], is_day=moment != "NUIT")
    if cond in ("SUN", "MOON", "PARTLY", "CLOUD", "RAIN", "STORM", "SNOW", "FOG"):
        over.update(icon=cond, code={"RAIN": 63, "STORM": 95, "SNOW": 73, "FOG": 45}.get(cond, 0))
    if temp is not None:
        over.update(temp=temp, feels=temp)
    if season in ("SPRING", "SUMMER", "AUTUMN", "WINTER"):
        over.update(season=season)
    w = dataclasses.replace(w, **over)
    if w.phase == "NUIT" and w.icon == "SUN":
        w = dataclasses.replace(w, icon="MOON")
    if w.phase != "NUIT" and w.icon == "MOON":
        w = dataclasses.replace(w, icon="SUN")
    return w


def _gif_bytes(frames: list[Image.Image], durations, loop: bool, colors: int) -> bytes:
    q = [f.quantize(colors=colors, method=Image.MEDIANCUT) for f in frames]
    buf = io.BytesIO()
    kw = {"loop": 0} if loop else {}
    q[0].save(buf, format="GIF", save_all=True, append_images=q[1:], duration=durations, optimize=False, **kw)
    return buf.getvalue()


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@app.get("/api/preview/crypto")
def preview_crypto(pair: str = "BTC/USDT", fmt: str = "gif", frame: int = 0):
    i18n.use(settings.load()["language"])
    try:
        snap = cached(f"mk:{pair}", 60, lambda: data.get_market(pair))
    except data.DataError as exc:
        raise HTTPException(502, str(exc))

    def make():
        from geekmagic import sprites
        if fmt == "png":
            f = render.new_frame()
            render.draw_token_card(f, snap, frame % sprites.ROTATION_FRAMES)
            return _png_bytes(f)
        frames = []
        for step in range(sprites.ROTATION_FRAMES):
            f = render.new_frame()
            render.draw_token_card(f, snap, step)
            frames.append(f)
        return _gif_bytes(frames, send_tokens.FRAME_MS, True, 64)
    body = cached(f"pc:{pair}:{fmt}:{frame}:{int(snap.price)}", 120, make)
    return Response(body, media_type="image/png" if fmt == "png" else "image/gif")


@app.get("/api/preview/weather")
def preview_weather(loc: str | None = None, scene: str | None = None, moment: str | None = None,
                    cond: str | None = None, temp: float | None = None, season: str | None = None,
                    fmt: str = "gif", frame: int = 6, sample: bool = False, bare: bool = False):
    cfg = settings.load()
    i18n.use(cfg["language"])
    location = _loc(cfg, loc)
    base = dataclasses.replace(SAMPLE, city=location["city"]) if sample else _live_weather(location)
    w = _simulate(base, moment, cond, temp, season)
    place = scene if scene in places.PLACES else (None if location["scene"] == "auto" else location["scene"])
    allowed = cfg["weather"]["scenes_enabled"]

    def make():
        if fmt == "png":
            f = render.new_frame()
            render.draw_weather_card(f, w, frame % scenes.N, place=place, allowed=allowed, info=not bare)
            return _png_bytes(f)
        frames = []
        for step in range(scenes.N):
            f = render.new_frame()
            render.draw_weather_card(f, w, step, place=place, allowed=allowed)
            frames.append(f)
        return _gif_bytes(frames, send_weather.FRAME_MS, True, 128)
    key = f"pw:{location['id']}:{place}:{w.phase}:{w.icon}:{w.temp}:{w.season}:{fmt}:{frame}:{sample}:{bare}:{w.doy}"
    body = cached(key, 300, make)
    return Response(body, media_type="image/png" if fmt == "png" else "image/gif")


@app.get("/api/preview/clock")
def preview_clock(fmt: str = "gif", effect: str | None = None, frame: int = 18, replay: int = 0,
                  tz: str | None = None, show_weather: bool | None = None, loc: str | None = None,
                  ns: int | None = None, ne: int | None = None):
    cfg = settings.load()
    i18n.use(cfg["language"])
    try:
        now = datetime.now(ZoneInfo(tz or cfg["clock"]["timezone"]))
    except Exception:  # noqa: BLE001 — fuseau inconnu : on garde celui de la config
        now = datetime.now(ZoneInfo(cfg["clock"]["timezone"]))
    w = None
    if cfg["clock"]["show_weather"] if show_weather is None else show_weather:
        w = _live_weather(_loc(cfg, loc or cfg["clock"]["location"]))
    ns = cfg["clock"]["night_start"] if ns is None else ns
    ne = cfg["clock"]["night_end"] if ne is None else ne
    night = (now.hour >= ns or now.hour < ne) if ns > ne else (ns <= now.hour < ne)
    if fmt == "png":
        prev = now.replace(minute=(now.minute - 1) % 60)
        f = render.new_frame()
        render.draw_clock_card(f, now.hour, now.minute, frame % scenes.N, now=now,
                               prev=(prev.hour, prev.minute), night=night, w=w)
        return Response(_png_bytes(f), media_type="image/png")
    eff = effect if effect in settings.EFFECTS and effect != "random" else (
        None if cfg["clock"]["effect"] == "random" else cfg["clock"]["effect"])
    tmp = ROOT / "output" / "_preview_clock.gif"
    with _lock:
        send_clock.build_clock_gif(now, w, eff, out=tmp, night_hours=(ns, ne))
        body = tmp.read_bytes()
    return Response(body, media_type="image/gif", headers={"Cache-Control": "no-store"})


app.mount("/", StaticFiles(directory=STATIC, html=True), name="ui")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
