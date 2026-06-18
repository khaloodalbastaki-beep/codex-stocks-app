#!/usr/bin/env python3
"""Fetch real UAE market news via Google News RSS.

The app stores headlines, source labels, timestamps, and original links. Article
text is not copied. The PWA opens an in-app detail view with source metadata and
an explicit link to the original page.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.registry import SECURITIES

DATA_DIR = ROOT / "data"
NEWS_PATH = DATA_DIR / "news.json"
STATUS_PATH = DATA_DIR / "provider_status.json"


QUERIES = [
    "ADX DFM UAE stocks",
    "Dubai Financial Market listed company disclosure dividend",
    "Abu Dhabi Securities Exchange listed company disclosure",
    "UAE stock market board meeting dividend",
]


def fetch_rss(query: str, limit: int) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "hl": "en-AE", "gl": "AE", "ceid": "AE:en"})
    url = f"https://news.google.com/rss/search?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 UAEStocksCodex/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        xml = response.read()
    root = ET.fromstring(xml)
    articles = []
    for item in root.findall("./channel/item")[:limit]:
        title = clean(item.findtext("title", ""))
        link = item.findtext("link", "")
        published = item.findtext("pubDate", "")
        source_node = item.find("source")
        source = clean(source_node.text if source_node is not None and source_node.text else "Google News")
        summary = clean(item.findtext("description", ""))
        article_id = hashlib.sha1(f"{title}|{link}".encode("utf-8")).hexdigest()[:16]
        related = related_symbols(f"{title} {summary}")
        articles.append(
            {
                "id": article_id,
                "title": title,
                "url": link,
                "source": source,
                "published_at": published,
                "summary": summary[:500],
                "query": query,
                "related_symbols": related,
                "source_type": "real_news_rss",
            }
        )
    return articles


def clean(text: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def related_symbols(text: str) -> list[str]:
    upper = text.upper()
    matches = []
    for row in SECURITIES:
        if row["symbol"] in upper or row["name_en"].upper().split()[0] in upper:
            matches.append(row["symbol"])
    return matches[:6]


def update_news(limit_per_query: int = 8) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_articles = []
    errors = []
    seen = set()
    for query in QUERIES:
        try:
            for article in fetch_rss(query, limit_per_query):
                if article["id"] in seen:
                    continue
                seen.add(article["id"])
                all_articles.append(article)
        except Exception as exc:  # noqa: BLE001 - status should capture provider failure
            errors.append({"query": query, "error": str(exc)[:240]})
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": "google_news_rss",
        "data_quality": "real_news_metadata",
        "rights_note": "Headlines and links only; open original publisher/Google News URL for article content.",
        "articles": all_articles[:40],
        "errors": errors,
    }
    NEWS_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    status = {}
    if STATUS_PATH.exists():
        try:
            status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            status = {}
    status["news"] = {
        "generated_at": payload["generated_at"],
        "provider": payload["provider"],
        "success": len(all_articles),
        "failed": len(errors),
        "errors": errors,
    }
    STATUS_PATH.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch real UAE market news metadata")
    parser.add_argument("--limit-per-query", type=int, default=8)
    args = parser.parse_args()
    payload = update_news(limit_per_query=args.limit_per_query)
    print(json.dumps({"articles": len(payload["articles"]), "errors": payload["errors"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
