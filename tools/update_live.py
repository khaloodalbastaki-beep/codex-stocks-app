#!/usr/bin/env python3
"""Refresh public/delayed quote cache with market-hours protection.

This script is intentionally entitlement-aware:
- during market close it does not call quote APIs unless `--force` is passed
- when free public providers rate-limit or fail, the previous quote cache stays
- provider errors are published to `provider_status.json` for Admin visibility
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.market_hours import market_state
from brain.registry import SECURITIES

DATA_DIR = ROOT / "data"
QUOTE_PATH = DATA_DIR / "live_quotes.json"
STATUS_PATH = DATA_DIR / "provider_status.json"


YAHOO_SUFFIX = {"DFM": "DU", "ADX": "AD"}


def yahoo_symbol(row: dict) -> str:
    return row.get("quote_symbol") or f"{row['symbol']}.{YAHOO_SUFFIX.get(row['exchange'], row['exchange'])}"


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def fetch_yahoo(symbol: str, timeout: int = 8) -> dict:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1m"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 UAEStocksCodex/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    result = (data.get("chart", {}).get("result") or [None])[0]
    if not result:
        raise RuntimeError(data.get("chart", {}).get("error") or f"No quote result for {symbol}")
    meta = result.get("meta", {})
    price = meta.get("regularMarketPrice") or meta.get("previousClose")
    prev = meta.get("previousClose") or meta.get("chartPreviousClose") or price
    if price is None:
        raise RuntimeError(f"No price in provider response for {symbol}")
    change_pct = 0.0 if not prev else ((float(price) - float(prev)) / float(prev)) * 100
    return {
        "provider_symbol": symbol,
        "last_price": round(float(price), 3 if float(price) < 1 else 2),
        "change_pct": round(change_pct, 2),
        "currency": meta.get("currency") or "AED",
        "regular_market_time": meta.get("regularMarketTime"),
        "exchange_name": meta.get("exchangeName"),
        "provider": "yahoo_chart_public",
        "data_quality": "public_delayed",
        "status_label": "Public delayed",
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def refresh(force: bool = False, sleep_seconds: float = 0.25) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = market_state()
    previous = load_json(QUOTE_PATH, {"quotes": {}, "history": []})
    status = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market": state.__dict__,
        "quotes": {
            "attempted": False,
            "provider": "yahoo_chart_public",
            "success": 0,
            "failed": 0,
            "skipped": False,
            "errors": [],
            "note": "",
        },
    }
    if not state.is_open and not force:
        status["quotes"]["skipped"] = True
        status["quotes"]["note"] = "Market is closed; quote API calls skipped and previous published prices remain frozen."
        STATUS_PATH.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
        return status

    quotes = dict(previous.get("quotes", {}))
    status["quotes"]["attempted"] = True
    for row in SECURITIES:
        provider_symbol = yahoo_symbol(row)
        try:
            quotes[row["symbol"]] = fetch_yahoo(provider_symbol)
            status["quotes"]["success"] += 1
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            status["quotes"]["failed"] += 1
            status["quotes"]["errors"].append({"symbol": row["symbol"], "provider_symbol": provider_symbol, "error": str(exc)[:240]})
        time.sleep(sleep_seconds)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market": state.__dict__,
        "quotes": quotes,
        "history": ([{"at": datetime.now(timezone.utc).isoformat(), "success": status["quotes"]["success"], "failed": status["quotes"]["failed"]}] + previous.get("history", []))[:50],
    }
    QUOTE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    STATUS_PATH.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    return status


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh public delayed quote cache")
    parser.add_argument("--force", action="store_true", help="Call provider even when market is closed")
    parser.add_argument("--sleep", type=float, default=0.25, help="Seconds between provider calls")
    args = parser.parse_args()
    status = refresh(force=args.force, sleep_seconds=args.sleep)
    print(json.dumps(status, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
