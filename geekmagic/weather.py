"""Météo locale : géolocalisation par IP + Open-Meteo (aucune clé requise).

- ip-api.com (HTTP, gratuit) -> lat/lon/ville
- open-meteo.com -> température, code WMO, is_day, lever/coucher

Phases (calcul local au lieu détecté) :
  NUIT / AURORE / MATIN / JOURNEE / APRES-MIDI / CREPUSCULE
Repas (badges) : PETIT-DEJ 07-09h, DEJEUNER 12-14h, GOUTER 16-17h, DINER 19-21h.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

UA = {"User-Agent": "Mozilla/5.0 (geekmagic-dashboard)"}


class WeatherError(RuntimeError):
    pass


@dataclass
class WeatherSnapshot:
    city: str
    temp: float            # °C
    feels: float           # ressenti
    code: int              # code WMO
    is_day: bool
    icon: str              # SUN/MOON/CLOUD/PARTLY/RAIN/STORM/SNOW/FOG
    phase: str             # NUIT/AURORE/MATIN/JOURNEE/APRES-MIDI/CREPUSCULE
    meal: str | None       # PETIT-DEJ/DEJEUNER/GOUTER/DINER ou None
    wind: float = 0.0      # km/h
    temp_3h: float | None = None    # prévision à +3h
    icon_3h: str | None = None
    season: str = "SUMMER"          # WINTER/SPRING/SUMMER/AUTUMN
    hour: float = 12.0              # heure locale décimale (position soleil/lune)
    doy: int = 1                    # jour de l'année (rotation des scènes)
    year: int = 2026

    @property
    def alert(self) -> str | None:
        """Alerte prioritaire : remplace le badge repas le cas échéant."""
        if self.code >= 95:
            return "ORAGE"
        if self.code in (65, 82):
            return "PLUIE FORTE"
        if self.wind >= 60:
            return "VENT FORT"
        if self.temp <= 0:
            return "GEL"
        return None

    @property
    def chicken_situation(self) -> str:
        """Situation kawaii de la poule selon météo/vent/moment."""
        if self.icon == "STORM":
            return "STORM"                      # alerte : elle se cache
        if self.wind >= 38:
            return "WIND"                       # elle s'envole
        if self.icon == "RAIN":
            return "RAIN"                       # parapluie
        if self.icon == "SNOW":
            return "SNOW"                       # écharpe
        if not self.is_day:
            return "NIGHT"                      # elle dort
        if self.icon == "SUN":
            return "SUN"                        # lunettes de soleil
        if self.meal:
            return "MEAL"                       # elle picore
        return "NEUTRAL"


def _get_json(url: str, timeout: float = 10.0):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _icon_for(code: int, is_day: bool) -> str:
    if code == 0:
        return "SUN" if is_day else "MOON"
    if code in (1, 2):
        return "PARTLY"
    if code == 3:
        return "CLOUD"
    if code in (45, 48):
        return "FOG"
    if 51 <= code <= 67 or code in (80, 81, 82):     # bruines + pluies
        return "RAIN"
    if 71 <= code <= 77 or code in (85, 86):          # neiges
        return "SNOW"
    if code >= 95:                                     # orages
        return "STORM"
    return "CLOUD"


def _phase(now: datetime, sunrise: datetime, sunset: datetime) -> str:
    if abs((now - sunrise).total_seconds()) <= 45 * 60:
        return "AURORE"
    if abs((now - sunset).total_seconds()) <= 45 * 60:
        return "CREPUSCULE"
    if sunrise < now < sunset:
        return "MATIN" if now.hour < 12 else "APRES-MIDI"
    return "NUIT"


def _meal(hour: int) -> str | None:
    if 7 <= hour < 9:
        return "PETIT-DEJ"
    if 12 <= hour < 14:
        return "DEJEUNER"
    if 16 <= hour < 17:
        return "GOUTER"
    if 19 <= hour < 21:
        return "DINER"
    return None


def get_weather(location: dict | None = None) -> WeatherSnapshot:
    """Météo courante. `location` = surcharge config {"city","lat","lon","timezone"?}.

    Sans surcharge (ou incomplète) : géoloc IP — approximative au niveau ville
    (elle localise le point de sortie du FAI, pas l'utilisateur).
    """
    if location and location.get("lat") and location.get("lon"):
        geo = {
            "city": location.get("city", "?"),
            "lat": location["lat"],
            "lon": location["lon"],
            "timezone": location.get("timezone", "Europe/Paris"),
        }
    else:
        geo = _get_json("http://ip-api.com/json/?fields=status,lat,lon,city,timezone")
        if geo.get("status") != "success":
            raise WeatherError(f"Geoloc IP échouée : {geo}")

    tz = ZoneInfo(geo["timezone"])
    wx = _get_json(
        f"https://api.open-meteo.com/v1/forecast?latitude={geo['lat']}&longitude={geo['lon']}"
        "&current=temperature_2m,apparent_temperature,weather_code,is_day,wind_speed_10m"
        "&hourly=temperature_2m,weather_code&forecast_days=1"
        "&daily=sunrise,sunset&timezone=auto"
    )
    cur = wx["current"]
    now = datetime.now(tz)
    sunrise = datetime.fromisoformat(wx["daily"]["sunrise"][0]).replace(tzinfo=tz)
    sunset = datetime.fromisoformat(wx["daily"]["sunset"][0]).replace(tzinfo=tz)

    # prévision +3h : première heure horaire >= maintenant, +3 index
    temp_3h, icon_3h = None, None
    try:
        hours = [datetime.fromisoformat(t).replace(tzinfo=tz) for t in wx["hourly"]["time"]]
        idx = next(i for i, t in enumerate(hours) if t >= now)
        j = min(idx + 3, len(hours) - 1)
        temp_3h = wx["hourly"]["temperature_2m"][j]
        icon_3h = _icon_for(wx["hourly"]["weather_code"][j], hours[j].hour % 24 in range(7, 19))
    except (StopIteration, KeyError, IndexError):
        pass

    season = {12: "WINTER", 1: "WINTER", 2: "WINTER", 3: "SPRING", 4: "SPRING", 5: "SPRING",
              6: "SUMMER", 7: "SUMMER", 8: "SUMMER"}.get(now.month, "AUTUMN")

    return WeatherSnapshot(
        city=geo["city"],
        temp=cur["temperature_2m"],
        feels=cur["apparent_temperature"],
        code=cur["weather_code"],
        is_day=bool(cur["is_day"]),
        icon=_icon_for(cur["weather_code"], bool(cur["is_day"])),
        phase=_phase(now, sunrise, sunset),
        meal=_meal(now.hour),
        wind=cur.get("wind_speed_10m", 0.0),
        temp_3h=temp_3h,
        icon_3h=icon_3h,
        season=season,
        hour=now.hour + now.minute / 60,
        doy=now.timetuple().tm_yday,
        year=now.year,
    )


if __name__ == "__main__":
    w = get_weather()
    print(f"{w.city} {w.temp}° (ressenti {w.feels}°) code={w.code} {w.icon} "
          f"| {w.phase} | repas={w.meal}")
