"""Yahoo Finance crypto summaries — fixed ticker list, sorted by volume."""

from dataclasses import dataclass

import yfinance as yf

# Scope: majors only; no dynamic screener or historical charts.
CRYPTO_TICKERS = (
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "XRP-USD",
    "DOGE-USD",
    "ADA-USD",
    "AVAX-USD",
    "LINK-USD",
)


@dataclass(frozen=True)
class CryptoSummary:
    symbol: str
    price: float
    change_pct: float
    volume: float


def fetch_crypto_summaries() -> list[CryptoSummary]:
    rows: list[CryptoSummary] = []
    for symbol in CRYPTO_TICKERS:
        info = yf.Ticker(symbol).fast_info
        price = float(info.get("last_price") or info.get("lastPrice") or 0)
        prev = float(info.get("previous_close") or info.get("previousClose") or 0)
        volume = float(info.get("last_volume") or info.get("lastVolume") or 0)
        change_pct = ((price - prev) / prev * 100) if prev else 0.0
        rows.append(CryptoSummary(symbol, price, change_pct, volume))
    rows.sort(key=lambda r: r.volume, reverse=True)
    return rows
