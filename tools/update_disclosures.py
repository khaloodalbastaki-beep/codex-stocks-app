#!/usr/bin/env python3
"""Normalize official disclosure metadata into the app contract.

This importer is intentionally rights-safe: it stores source metadata and links,
not full exchange filings. Put official DFM/ADX/issuer filing links in
`filings/official_disclosures.json`; the app will publish normalized events and
the AI agent can treat them as official evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.registry import SECURITIES

MANIFEST_PATH = ROOT / "filings" / "official_disclosures.json"
DATA_DIR = ROOT / "data"
OUT_PATH = DATA_DIR / "official_disclosures.json"
STATUS_PATH = DATA_DIR / "provider_status.json"


SECURITY_SYMBOLS = {row["symbol"] for row in SECURITIES}


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "rights_note": "No official disclosure manifest found.", "sources": [], "records": []}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_record(record: dict) -> dict:
    symbol = str(record.get("symbol", "")).upper().strip()
    title = clean(record.get("title_en") or record.get("title") or "Official filing")
    published = record.get("published_at") or datetime.now(timezone.utc).isoformat()
    source_url = record.get("source_url") or record.get("document_url") or ""
    document_url = record.get("document_url") or source_url
    event_id = record.get("id") or hashlib.sha1(f"{symbol}|{title}|{document_url}".encode("utf-8")).hexdigest()[:16]
    signals = [str(item) for item in record.get("signals", []) if item]
    evidence = [record.get("source_name") or record.get("exchange") or "Official filing"]
    if source_url:
        evidence.append(source_url)
    if document_url and document_url != source_url:
        evidence.append(document_url)
    return {
        "id": event_id,
        "symbol": symbol,
        "exchange": record.get("exchange") or exchange_for_symbol(symbol),
        "source_type": record.get("source_type") or "official_exchange",
        "source_name": record.get("source_name") or "Official exchange filing",
        "event_type": record.get("event_type") or infer_event_type(title, record.get("category", ""), signals),
        "category": record.get("category") or "official_filing",
        "title_en": title,
        "title_ar": clean(record.get("title_ar", "")),
        "summary": clean(record.get("summary", "")) or f"Official filing metadata for {symbol}. Open the source document for full content.",
        "why_it_matters": clean(record.get("why_it_matters", "")) or "Official filings can change scores, risk flags, dividends, and the AI research stance.",
        "materiality": int(record.get("materiality", infer_materiality(title, signals))),
        "sentiment": record.get("sentiment") or infer_sentiment(title, signals),
        "timestamp": published,
        "source_url": source_url,
        "document_url": document_url,
        "signals": signals,
        "data_quality": "official_metadata",
        "evidence": evidence,
    }


def exchange_for_symbol(symbol: str) -> str:
    for row in SECURITIES:
        if row["symbol"] == symbol:
            return row["exchange"]
    return "unknown"


def infer_event_type(title: str, category: str, signals: list[str]) -> str:
    haystack = f"{title} {category} {' '.join(signals)}".lower()
    if "dividend" in haystack:
        return "dividend"
    if "agm" in haystack or "annual general" in haystack:
        return "agm"
    if "board" in haystack:
        return "board_meeting"
    if "financial" in haystack or "result" in haystack or "annual report" in haystack or "integrated report" in haystack:
        return "results"
    return "official_filing"


def infer_materiality(title: str, signals: list[str]) -> int:
    haystack = f"{title} {' '.join(signals)}".lower()
    score = 65
    if "financial" in haystack or "result" in haystack:
        score += 10
    if "dividend" in haystack:
        score += 8
    if "board" in haystack or "agm" in haystack:
        score += 5
    return min(score, 90)


def infer_sentiment(title: str, signals: list[str]) -> str:
    haystack = f"{title} {' '.join(signals)}".lower()
    if "dividend" in haystack or "cashflow" in haystack:
        return "Positive"
    return "Neutral"


def clean(value: object) -> str:
    return " ".join(str(value or "").split())


def verify_link(url: str, timeout: int = 10) -> dict:
    if not url:
        return {"url": url, "ok": False, "error": "missing_url"}
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 UAEStocksCodex/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(256)
            return {
                "url": url,
                "ok": 200 <= response.status < 400,
                "status": response.status,
                "content_type": response.getheader("content-type"),
            }
    except Exception as exc:  # noqa: BLE001 - reflected in provider status
        return {"url": url, "ok": False, "error": str(exc)[:240]}


def update_disclosures(verify_links: bool = False) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(MANIFEST_PATH)
    errors = []
    events = []
    for record in manifest.get("records", []):
        try:
            event = normalize_record(record)
            if not event["symbol"] or event["symbol"] not in SECURITY_SYMBOLS:
                errors.append({"record": record.get("id"), "error": f"Unknown symbol: {event['symbol']}"})
                continue
            if verify_links:
                checks = [verify_link(event.get("source_url", "")), verify_link(event.get("document_url", ""))]
                event["link_checks"] = checks
                if not all(item.get("ok") for item in checks if item.get("url")):
                    errors.append({"record": event["id"], "error": "One or more official links could not be verified", "checks": checks})
            events.append(event)
        except Exception as exc:  # noqa: BLE001 - status should capture bad records
            errors.append({"record": record.get("id"), "error": str(exc)[:240]})

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": "official_disclosure_manifest",
        "data_quality": "official_metadata",
        "rights_note": manifest.get("rights_note", "Official filing metadata and source links only."),
        "sources": manifest.get("sources", []),
        "events": sorted(events, key=lambda row: row["timestamp"], reverse=True),
        "errors": errors,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    status = {}
    if STATUS_PATH.exists():
        try:
            status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            status = {}
    status["disclosures"] = {
        "generated_at": payload["generated_at"],
        "provider": payload["provider"],
        "success": len(events),
        "failed": len(errors),
        "data_quality": payload["data_quality"],
        "rights_note": payload["rights_note"],
        "errors": errors,
    }
    STATUS_PATH.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize official filing metadata")
    parser.add_argument("--verify-links", action="store_true", help="Fetch official links and record reachability status")
    args = parser.parse_args()
    payload = update_disclosures(verify_links=args.verify_links)
    print(json.dumps({"events": len(payload["events"]), "errors": payload["errors"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
