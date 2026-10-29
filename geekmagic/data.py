"""Récupération des données de marché (OHLC + ticker 24h).

Binance en source primaire (klines propres + ticker 24h), CoinGecko en
fallback si Binance est injoignable ou geo-bloqué (HTTP 451).
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

UA = {"User-Agent": "Mozilla/5.0 (geekmagic-dashboard)"}


class DataError(RuntimeError):
    """Échec de récupération des données de marché."""


@dataclass
class Candle:
    ts: int  # ms, heure d'ouverture
    open: float
    high: float
    low: float
    close: float


@dataclass
class MarketSnapshot:
    pair: str          # "BTC/USDT"
    price: float       # dernier prix
    change_24h: float  # % sur 24h
    candles: list[Candle]
    high_24h: float | None = None       # pour badge HIGH/LOW et range
    low_24h: float | None = None
    closes: list[float] | None = None   # ~24 dernières clôtures 1h (sparkline)
    volume_spike: bool = False          # volume de l'heure > 2x la moyenne 24h

    @property
    def at_high(self) -> bool:
        return self.high_24h is not None and self.price >= self.high_24h * 0.999

    @property
    def at_low(self) -> bool:
        return self.low_24h is not None and self.price <= self.low_24h * 1.001


def _get_json(url: str, timeout: float = 10.0):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


# ------------------------------------------------------------------ Binance

def _binance(pair: str, interval: str, limit: int) -> MarketSnapshot:
    symbol = pair.replace("/", "").upper()
    base = "https://api.binance.com/api/v3"
    kl = _get_json(f"{base}/klines?symbol={symbol}&interval=1h&limit=25")
    candles = [Candle(k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4])) for k in kl]
    vols = [float(k[5]) for k in kl]
    volume_spike = vols[-1] > 2 * (sum(vols[:-1]) / max(len(vols) - 1, 1))
    ticker = _get_json(f"{base}/ticker/24hr?symbol={symbol}")
    return MarketSnapshot(
        pair=pair,
        price=float(ticker["lastPrice"]),
        change_24h=float(ticker["priceChangePercent"]),
        candles=candles[-limit:],
        high_24h=float(ticker["highPrice"]),
        low_24h=float(ticker["lowPrice"]),
        closes=[c.close for c in candles[:-1]][-24:],
        volume_spike=volume_spike,
    )


# --------------------------------------------------------------- CoinGecko

# identifiants CoinGecko des bases courantes ; étendre au besoin
_CG_IDS = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "binancecoin",
           "XRP": "ripple", "ADA": "cardano", "DOGE": "dogecoin", "AVAX": "avalanche-2",
           "LINK": "chainlink", "MATIC": "matic-network", "DOT": "polkadot", "ATOM": "cosmos",
           "AAVE": "aave", "ONDO": "ondo-finance", "ENA": "ethena", "HYPE": "hyperliquid"}

# jours CoinGecko -> granularité imposée par l'API : 1j=30min, 7-30j=4h, >30j=4j
_CG_DAYS = {"15m": 1, "30m": 1, "1h": 1, "4h": 7, "1d": 30}


def _coingecko(pair: str, interval: str, limit: int) -> MarketSnapshot:
    base_sym = pair.split("/")[0].upper()
    cg_id = _CG_IDS.get(base_sym)
    if not cg_id:
        raise DataError(f"No CoinGecko ID for {base_sym}: add it to _CG_IDS.")
    days = _CG_DAYS.get(interval, 1)
    ohlc = _get_json(f"https://api.coingecko.com/api/v3/coins/{cg_id}/ohlc?vs_currency=usd&days={days}")
    candles = [Candle(ts, o, h, l, c) for ts, o, h, l, c in ohlc][-limit:]
    simple = _get_json(f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
                       "&include_24hr_change=true")
    info = simple[cg_id]
    return MarketSnapshot(
        pair=pair,
        price=info["usd"],
        change_24h=info.get("usd_24h_change", 0.0),
        candles=candles,
        closes=[c.close for c in candles],   # pas de high/low dispo sans appel supplémentaire
    )


# ------------------------------------------------------------------- façade

def get_market(pair: str = "BTC/USDT", interval: str = "1h", limit: int = 7) -> MarketSnapshot:
    """OHLC + ticker 24h. Binance d'abord, CoinGecko en secours."""
    errors = []
    for provider in (_binance, _coingecko):
        try:
            return provider(pair, interval, limit)
        except Exception as exc:  # noqa: BLE001 — on veut enchaîner sur le fallback
            errors.append(f"{provider.__name__}: {exc}")
    raise DataError(" | ".join(errors))


if __name__ == "__main__":
    snap = get_market()
    print(snap.pair, snap.price, f"{snap.change_24h:+.2f}%")
    for c in snap.candles[-3:]:
        print(f"  {time.strftime('%H:%M', time.localtime(c.ts / 1000))} O={c.open} C={c.close}")
