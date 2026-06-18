"""Mizan Codex: UAE stock research agent.

The agent reads the app's normalized JSON contract plus optional local filing
snippets, then emits a structured research report. It can use Ollama, Gemini,
Groq, OpenRouter, or a deterministic stub for testing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.mizan_codex.hermes import write_handoff
from agents.mizan_codex.llm import LLMError, call_llm

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / "web" / "data" / "app_data.json"
DEFAULT_FILINGS = ROOT / "filings" / "inbox"
DEFAULT_OUT = ROOT / "agent_out" / "mizan_codex_reports.json"
DEFAULT_OLLAMA_CLOUD_MODEL = "gemma4:31b-cloud"


SYSTEM_PROMPT = """You are Mizan Codex, a UAE equities research-support agent.
You are not a broker and you do not give personalized financial advice.
Your job is to study one UAE-listed stock using only the supplied JSON and local filing snippets.
Separate official facts, company/issuer material, market/news context, and AI interpretation.
Preserve uncertainty. Never invent missing filings, prices, accounting values, or source URLs.
Never label demo financial units as AED, bn, audited, or real unless the input explicitly says so.
Return only valid JSON. No markdown.
"""


REQUIRED_KEYS = {
    "symbol",
    "company",
    "research_stance",
    "confidence",
    "time_horizon",
    "what_changed",
    "money_and_accounts",
    "filing_findings",
    "trend_findings",
    "news_signals",
    "positive_drivers",
    "negative_drivers",
    "watch_items",
    "evidence",
    "alert_rules",
    "trading_plan",
    "disclaimer",
    "review_flags",
}


def load_app_data(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"App data not found: {path}. Run `bash tools/build.sh` first.")
    return json.loads(path.read_text(encoding="utf-8"))


def get_security(data: dict, symbol: str) -> dict:
    symbol = symbol.upper()
    for item in data["securities"]:
        if item["symbol"] == symbol:
            return item
    raise KeyError(f"Unknown symbol: {symbol}")


def filing_snippets(filings_dir: Path, symbol: str, limit_chars: int = 9000) -> list[dict]:
    if not filings_dir.exists():
        return []
    symbol_re = re.compile(rf"(^|[^A-Z0-9]){re.escape(symbol.upper())}([^A-Z0-9]|$)")
    snippets = []
    for path in sorted(filings_dir.glob("**/*")):
        if not path.is_file() or path.suffix.lower() not in {".txt", ".md", ".html", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        haystack = f"{path.name}\n{text}".upper()
        if symbol_re.search(haystack) or symbol.upper() in haystack:
            snippets.append(
                {
                    "file": str(path.relative_to(ROOT)),
                    "chars": len(text),
                    "snippet": text[:limit_chars],
                }
            )
    return snippets


def build_prompt(data: dict, stock: dict, snippets: list[dict]) -> str:
    events = [event for event in data["events"] if event["symbol"] == stock["symbol"]]
    news = related_news(data, stock["symbol"])
    compact = {
        "metadata": data["metadata"],
        "stock": {
            "symbol": stock["symbol"],
            "name_en": stock["name_en"],
            "name_ar": stock["name_ar"],
            "exchange": stock["exchange"],
            "sector": stock["sector"],
            "summary": stock["summary"],
            "quote": stock["quote"],
            "scores": stock["scores"],
            "stance": stock["stance"],
            "confidence": stock["confidence"],
            "financials": stock["financials"],
            "dividends": stock["dividends"],
            "ownership": stock["ownership"],
            "global_factors": stock["global_factors"],
            "price_signal": stock.get("price_signal", {}),
            "top_risks": stock["top_risks"],
            "top_catalysts": stock["top_catalysts"],
        },
        "recent_events": events,
        "real_news_signals": news,
        "market_pulse": data["market_pulse"],
        "source_rules": data["source_badges"],
        "local_filing_snippets": snippets,
    }
    schema_hint = {key: "" for key in sorted(REQUIRED_KEYS)}
    schema_hint.update(
        {
            "money_and_accounts": [],
            "filing_findings": [],
            "trend_findings": [],
            "news_signals": [],
            "positive_drivers": [],
            "negative_drivers": [],
            "watch_items": [],
            "evidence": [],
            "alert_rules": [],
            "trading_plan": {},
            "review_flags": [],
        }
    )
    return (
        "Study this UAE stock and return a structured JSON report.\n"
        "Use `research_stance` values only: Bullish, Neutral, Cautious, or Needs Review.\n"
        "Use `confidence` values only: low, medium, high.\n"
        "For `trading_plan`, prefer the supplied `stock.price_signal` keys: buy_or_not, buy_below, target_12m, invalidation_price, expected_return_pct.\n"
        "Do not describe demo financial series, mock quotes, or demo market-cap fields as audited, confirmed, AED-denominated, or billions unless the input source explicitly says so.\n"
        "The output must match these keys exactly, with arrays where the template has arrays:\n"
        f"{json.dumps(schema_hint, ensure_ascii=False)}\n\n"
        "Input data:\n"
        f"{json.dumps(compact, ensure_ascii=False, indent=2)}"
    )


def deterministic_report(data: dict, stock: dict, snippets: list[dict], provider: str = "stub", model: str = "deterministic") -> dict:
    events = [event for event in data["events"] if event["symbol"] == stock["symbol"]]
    news = related_news(data, stock["symbol"])
    positives = [factor for factor in stock["global_factors"] if factor["impact_tag"] == "Positive"]
    negatives = [factor for factor in stock["global_factors"] if factor["impact_tag"] == "Cautious"]
    stance = stock["stance"]
    if snippets and any("dividend" in item["snippet"].lower() for item in snippets):
        what_changed = "Local filing snippets mention dividend or distribution language; review the original file before changing the stance."
    elif events:
        what_changed = f"Latest mapped event is {events[0]['event_type'].replace('_', ' ')} from {events[0]['source_name']}."
    else:
        what_changed = "No high-materiality local filing was supplied for this run."

    review_flags = []
    if stock["quote"]["data_quality"] == "demo":
        review_flags.append("Market data is demo; do not use this report as a trading signal.")
    if not snippets:
        review_flags.append("No local filing snippets found for this symbol.")
    if stock["scores"]["dividend"] < 55 and stock["dividends"]["yield_pct"] > 4:
        review_flags.append("Headline yield is higher than dividend-quality score; inspect payout coverage.")

    return {
        "symbol": stock["symbol"],
        "company": stock["name_en"],
        "research_stance": stance,
        "confidence": stock["confidence"],
        "time_horizon": {
            "short_term": "5-20 trading days, event and momentum sensitive",
            "long_term": "6-24 months, filing and fundamentals sensitive",
        },
        "what_changed": what_changed,
        "money_and_accounts": [
            f"Growth score {stock['scores']['growth']}/100; stability {stock['scores']['stability']}/100; dividend {stock['scores']['dividend']}/100.",
            f"Revenue growth demo input: {stock['financials']['revenue_growth_pct']:+.1f}%; profit growth demo input: {stock['financials']['profit_growth_pct']:+.1f}%.",
            f"Dividend yield {stock['dividends']['yield_pct']:.1f}%; payout ratio {stock['dividends']['payout_ratio_pct']:.0f}%; sustainability tag {stock['dividends']['sustainability']}.",
        ],
        "filing_findings": [
            f"{event['event_type']}: {event['summary']} Evidence: {', '.join(event['evidence'])}."
            for event in events[:4]
        ]
        or ["No mapped disclosure event in current app data."],
        "trend_findings": [
            f"{factor['label']}: {factor['move']} -> {factor['impact_tag']}. {factor['impact']}"
            for factor in stock["global_factors"][:5]
        ],
        "news_signals": [
            f"{item['source']}: {item['title']}" for item in news[:5]
        ]
        or ["No mapped real-news headline for this symbol in the current RSS fetch."],
        "positive_drivers": [
            f"{factor['label']} currently maps positive for this stock." for factor in positives[:4]
        ]
        + stock["top_catalysts"][:2],
        "negative_drivers": [
            f"{factor['label']} is a cautious factor." for factor in negatives[:4]
        ]
        + stock["top_risks"][:3],
        "watch_items": [
            "Next official disclosure or board agenda",
            "Dividend entitlement/payment date changes",
            "Material global factor shock from the exposure map",
            "Any contradiction between issuer filing and media summary",
        ],
        "evidence": [
            {"type": "app_contract", "source": "web/data/app_data.json", "note": "Normalized stock, score, event, and factor data"},
            *[
                {"type": "filing_snippet", "source": item["file"], "note": f"{item['chars']} characters loaded"}
                for item in snippets
            ],
            *[
                {"type": event["source_type"], "source": event["source_name"], "note": event["title_en"]}
                for event in events[:3]
            ],
        ],
        "alert_rules": [
            {"type": "disclosure", "symbol": stock["symbol"], "reason": "New official disclosure changes materiality or stance."},
            {"type": "dividend", "symbol": stock["symbol"], "reason": "Entitlement, ex-date, payment date, payout amount changes."},
            {"type": "global_factor", "symbol": stock["symbol"], "reason": "Mapped exposure receives high-materiality macro shock."},
        ],
        "trading_plan": stock.get("price_signal", {}),
        "disclaimer": "Research support only. Not personalized financial advice, not a buy/sell instruction.",
        "review_flags": review_flags,
        "llm": {"provider": provider, "model": model, "mode": "deterministic_fallback"},
    }


def parse_llm_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        report = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            report = json.loads(cleaned[start : end + 1])
        else:
            raise ValueError(f"LLM did not return JSON: {cleaned[:400]}") from exc
    missing = REQUIRED_KEYS - set(report)
    if missing:
        raise ValueError(f"LLM report missing keys: {sorted(missing)}")
    return report


def related_news(data: dict, symbol: str) -> list[dict]:
    articles = data.get("news", {}).get("articles", [])
    related = [item for item in articles if symbol in item.get("related_symbols", [])]
    if related:
        return related[:8]
    broad = [item for item in articles if any(term in item.get("title", "").upper() for term in ("ADX", "DFM", "UAE STOCK", "DUBAI FINANCIAL MARKET"))]
    return broad[:5]


def enrich_report(report: dict, provider: str, model: str, stock: dict, fallback_used: bool = False) -> dict:
    report["symbol"] = report.get("symbol") or stock["symbol"]
    report["company"] = report.get("company") or stock["name_en"]
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["agent"] = {
        "id": "mizan-codex",
        "name": "Mizan Codex",
        "provider": provider,
        "model": model,
        "fallback_used": fallback_used,
        "lives_in": "agents/mizan_codex",
    }
    report["disclaimer"] = "Research support only. Not personalized financial advice, not a buy/sell instruction."
    if not report.get("trading_plan"):
        report["trading_plan"] = stock.get("price_signal", {})
    else:
        report["trading_plan"] = _normalize_trading_plan(report["trading_plan"], stock.get("price_signal", {}))
    report["money_and_accounts"] = [_stringify_agent_item(item) for item in report.get("money_and_accounts", [])]
    report["trend_findings"] = [_clean_demo_units(_stringify_agent_item(item)) for item in report.get("trend_findings", [])]
    report["news_signals"] = [_stringify_agent_item(item) for item in report.get("news_signals", [])]
    flags = [_stringify_agent_item(flag) for flag in list(report.get("review_flags") or [])]
    if stock.get("quote", {}).get("data_quality") in {"demo", "stale", "unknown"} and not any("demo" in str(flag).lower() for flag in flags):
        flags.append("Current quote/data quality is demo or stale; do not treat the price signal as live trading advice.")
    report["review_flags"] = flags
    if not report.get("alert_rules"):
        report["alert_rules"] = [
            {"type": "disclosure", "symbol": stock["symbol"], "reason": "New official disclosure changes materiality or stance."},
            {"type": "dividend", "symbol": stock["symbol"], "reason": "Dividend date, payout amount, or policy wording changes."},
            {"type": "global_factor", "symbol": stock["symbol"], "reason": "Mapped macro or commodity exposure becomes high materiality."},
        ]
    if isinstance(report.get("evidence"), list):
        report["evidence"] = [
            _clean_evidence_item(item) if isinstance(item, dict) else {"type": "agent_evidence", "source": str(item), "note": _clean_demo_units(str(item))}
            for item in report["evidence"]
        ]
    return report


def _normalize_trading_plan(plan: dict, fallback: dict) -> dict:
    normalized = dict(fallback or {})
    normalized.update(plan)
    if "entry_below" in plan and "buy_below" not in normalized:
        normalized["buy_below"] = plan["entry_below"]
    if "target" in plan and "target_12m" not in normalized:
        normalized["target_12m"] = plan["target"]
    if "stop_loss" in plan and "invalidation_price" not in normalized:
        normalized["invalidation_price"] = plan["stop_loss"]
    if "buy_or_not" not in normalized and "label" in fallback:
        normalized["buy_or_not"] = fallback.get("buy_or_not")
    return normalized


def _stringify_agent_item(item) -> str:
    if isinstance(item, str):
        return _clean_demo_units(item)
    if isinstance(item, dict):
        if "metric" in item:
            return _clean_demo_units(f"{item.get('metric')}: {item.get('value', item.get('value_pct', 'n/a'))}")
        if "period" in item:
            return _clean_demo_units(f"{item.get('period')}: revenue {item.get('revenue')}, profit {item.get('profit')} (demo units)")
        return _clean_demo_units(", ".join(f"{key}: {value}" for key, value in item.items()))
    return _clean_demo_units(str(item))


def _clean_demo_units(text: str) -> str:
    text = text.replace("AED 121bn", "121 demo units").replace("AED 26bn", "26 demo units")
    text = re.sub(r"\bmarket_cap_bn:\s*([0-9.]+)\b", r"market cap demo input: \1", text, flags=re.I)
    text = re.sub(r"\bmarket cap(?:italization)?(?: of)?[: ]+([0-9.]+)\s*(?:bn|billion)\b", r"demo market-cap input of \1 units", text, flags=re.I)
    return text


def _clean_evidence_item(item: dict) -> dict:
    cleaned = {}
    for key, value in item.items():
        cleaned[key] = _clean_demo_units(value) if isinstance(value, str) else value
    return cleaned


def load_existing_reports(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"reports": [], "latest_by_symbol": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    store = load_existing_reports(path)
    reports = [row for row in store.get("reports", []) if row.get("symbol") != report.get("symbol")]
    reports.insert(0, report)
    store = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agent": report["agent"],
        "reports": reports[:50],
        "latest_by_symbol": {row["symbol"]: row for row in reports[:50]},
    }
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def analyze_symbol(args: argparse.Namespace, data: dict, symbol: str) -> dict:
    stock = get_security(data, symbol)
    snippets = filing_snippets(Path(args.filings_dir), stock["symbol"])
    fallback_used = False
    provider = args.provider
    model = args.model
    if provider == "stub":
        report = deterministic_report(data, stock, snippets, provider, model or "deterministic")
        return enrich_report(report, provider, model or "deterministic", stock, fallback_used=False)

    prompt = build_prompt(data, stock, snippets)
    try:
        response = call_llm(provider, model, SYSTEM_PROMPT, prompt, timeout=args.timeout)
        report = parse_llm_json(response.text)
        provider = response.provider
        model = response.model
    except (LLMError, ValueError) as exc:
        if not args.allow_fallback:
            raise
        fallback_used = True
        report = deterministic_report(data, stock, snippets, provider, model or "unknown")
        report.setdefault("review_flags", []).append(f"LLM call failed and deterministic fallback was used: {exc}")
    return enrich_report(report, provider, model or "unknown", stock, fallback_used=fallback_used)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Mizan Codex UAE stock research agent")
    parser.add_argument("--symbol", help="Analyze one symbol, e.g. EMAAR")
    parser.add_argument("--all", action="store_true", help="Analyze all symbols in app data")
    parser.add_argument("--provider", default=os.getenv("MIZAN_PROVIDER", "ollama"), choices=["ollama", "gemini", "groq", "openrouter", "stub"])
    parser.add_argument("--model", default=os.getenv("MIZAN_MODEL", DEFAULT_OLLAMA_CLOUD_MODEL))
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--filings-dir", default=str(DEFAULT_FILINGS))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--allow-fallback", action="store_true", help="Use deterministic fallback if LLM call fails")
    parser.add_argument("--send-hermes", action="store_true", help="Write a safe-capture Hermes bus message for each report")
    parser.add_argument("--print", action="store_true", help="Print report JSON to stdout")
    args = parser.parse_args(argv)

    if not args.symbol and not args.all:
        parser.error("pass --symbol SYMBOL or --all")

    data = load_app_data(Path(args.data))
    symbols = [item["symbol"] for item in data["securities"]] if args.all else [args.symbol.upper()]
    reports = []
    for symbol in symbols:
        report = analyze_symbol(args, data, symbol)
        save_report(Path(args.out), report)
        if args.send_hermes:
            path = write_handoff(report)
            report.setdefault("handoffs", {})["hermes"] = str(path)
        reports.append(report)
        if args.print:
            print(json.dumps(report, ensure_ascii=False, indent=2))

    print(f"mizan-codex wrote {len(reports)} report(s) -> {Path(args.out).resolve()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
