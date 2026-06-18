"""Build the JSON contract consumed by the static PWA."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from brain.adapters.mock import MockMarketDataProvider
from brain.market_hours import market_state
from brain.registry import EXPOSURE_DEFINITIONS, SECURITIES, SOURCE_PROVIDERS
from brain.scoring import score_security, stance_from_scores

OLD_SIGNAL_METHOD = "Deterministic research signal from composite score, stance, and latest published price. Not personalized advice."
HOUSE_SIGNAL_METHOD = "House signal from composite score, research stance, and latest published price. Not personalized advice."


def _source_badges():
    return [
        {"label": "Official", "tone": "official", "meaning": "Exchange, issuer, regulator, or government source."},
        {"label": "Media", "tone": "media", "meaning": "Trusted news or official media-office context."},
        {"label": "Opinion", "tone": "opinion", "meaning": "Clearly separated third-party view."},
        {"label": "AI", "tone": "ai", "meaning": "Generated research support, never personalized advice."},
    ]


def _build_security(item: dict, quote: dict, events: list[dict]) -> dict:
    scores = score_security(item["fundamentals"], item["dividend_yield"])
    stance, confidence = stance_from_scores(scores, quote["change_pct"])
    stock_events = [event for event in events if event["symbol"] == item["symbol"]]
    latest = stock_events[0]["event_type"].replace("_", " ").title() if stock_events else "No new catalyst"
    factors = []
    for key in item["exposures"]:
        factor = EXPOSURE_DEFINITIONS[key]
        sentiment = factor["sentiment"]
        factors.append(
            {
                "key": key,
                "label": factor["label"],
                "move": factor["move"],
                "impact": factor["impact"],
                "sentiment": sentiment,
                "impact_tag": "Positive" if sentiment == "positive" else "Cautious" if sentiment == "cautious" else "Mixed",
                "confidence": "medium",
                "evidence": ["Exposure map", "Global signal mock adapter"],
            }
        )
    return {
        "symbol": item["symbol"],
        "isin": item["isin"],
        "name_en": item["name_en"],
        "name_ar": item["name_ar"],
        "exchange": item["exchange"],
        "sector": item["sector"],
        "archetype": item["archetype"],
        "summary": item["summary"],
        "index_membership": item["index_membership"],
        "quote": quote,
        "scores": scores.__dict__,
        "stance": stance,
        "confidence": confidence,
        "latest_catalyst": latest,
        "impact_chip": "Positive" if stance == "Bullish" else "Cautious" if stance == "Cautious" else "Neutral",
        "top_risks": _risks_for(item),
        "top_catalysts": _catalysts_for(item, stock_events),
        "global_factors": factors,
        "ownership": _ownership_for(item),
        "dividends": _dividend_for(item),
        "financials": _financials_for(item),
        "meetings": _meetings_for(item, stock_events),
        "analysis": _analysis_for(item, scores.__dict__, stance, confidence, factors, stock_events),
        "price_signal": _price_signal(quote, scores.__dict__, stance, confidence),
    }


def _risks_for(item: dict) -> list[str]:
    mapping = {
        "bank": ["Credit-cost surprise", "Rate-cycle reversal", "Wholesale funding pressure"],
        "developer": ["Rate pressure on affordability", "Delivery slippage", "Input-cost inflation"],
        "energy": ["Commodity spread volatility", "Maintenance downtime", "Policy or offtake changes"],
        "utility": ["Allowed-return reset", "Fuel-cost pass-through timing", "Capex execution"],
        "logistics": ["Freight-cycle slowdown", "Integration risk", "Fuel and wage cost pressure"],
        "consumer": ["Food input inflation", "Consumer slowdown", "Currency-linked purchasing pressure"],
        "cyclical": ["Fuel price spike", "Tourism demand shock", "Fleet-cost inflation"],
        "holding": ["Disclosure opacity", "Private-asset marks", "Acquisition integration"],
        "infrastructure": ["Regulatory tariff change", "Traffic demand slowdown", "High payout burden"],
    }
    return mapping.get(item["archetype"], ["Disclosure gap", "Macro shock", "Execution risk"])


def _catalysts_for(item: dict, stock_events: list[dict]) -> list[str]:
    catalysts = [event["event_type"].replace("_", " ").title() for event in stock_events[:2]]
    if "tourism" in item["exposures"]:
        catalysts.append("Tourism momentum")
    if item["dividend_yield"] >= 5:
        catalysts.append("Income demand")
    if "rates" in item["exposures"]:
        catalysts.append("Rates path")
    return catalysts[:4] or ["Next disclosure"]


def _ownership_for(item: dict) -> dict:
    foreign_available = max(0, 49 - (len(item["symbol"]) * 3 % 31))
    return {
        "mix": [
            {"holder": "Strategic / government-linked", "pct": 45 + len(item["symbol"]) % 18},
            {"holder": "Institutions", "pct": 18 + len(item["sector"]) % 14},
            {"holder": "Free float", "pct": 24 + len(item["name_en"]) % 18},
        ],
        "foreign_ownership": {
            "permitted_pct": 49,
            "actual_pct": 49 - foreign_available,
            "available_pct": foreign_available,
            "data_quality": "demo",
        },
    }


def _dividend_for(item: dict) -> dict:
    base_date = datetime.now(timezone.utc).date()
    return {
        "yield_pct": item["dividend_yield"],
        "frequency": "Semi-annual" if item["dividend_yield"] >= 4 else "Annual / irregular",
        "payout_ratio_pct": item["fundamentals"]["payout_ratio"],
        "sustainability": "Strong" if item["fundamentals"]["fcf_coverage"] >= 7 else "Watch",
        "confidence": "High" if item["fundamentals"]["regularity"] >= 7 else "Medium",
        "next_dates": [
            {"label": "Board review", "date": (base_date + timedelta(days=18)).isoformat()},
            {"label": "Entitlement window", "date": (base_date + timedelta(days=45)).isoformat()},
            {"label": "Payment target", "date": (base_date + timedelta(days=66)).isoformat()},
        ],
    }


def _financials_for(item: dict) -> dict:
    f = item["fundamentals"]
    return {
        "revenue_growth_pct": f["revenue_growth"],
        "profit_growth_pct": f["profit_growth"],
        "margin_direction": "Improving" if f["margin_trend"] >= 6.5 else "Stable" if f["margin_trend"] >= 5 else "Pressure",
        "cash_generation": "Strong" if f["cashflow_consistency"] >= 7 else "Mixed",
        "leverage_view": "Comfortable" if f["leverage"] >= 7 else "Watch",
        "source_documents": ["Demo annual report", "Demo interim financials"],
        "series": [
            {"period": "FY2023", "revenue": 100, "profit": 22},
            {"period": "FY2024", "revenue": round(100 * (1 + f["revenue_growth"] / 100), 1), "profit": round(22 * (1 + f["profit_growth"] / 100), 1)},
            {"period": "TTM", "revenue": round(104 * (1 + f["revenue_growth"] / 150), 1), "profit": round(23 * (1 + f["profit_growth"] / 140), 1)},
        ],
    }


def _meetings_for(item: dict, events: list[dict]) -> list[dict]:
    meetings = []
    for event in events:
        if event["event_type"] in {"board_meeting", "agm"}:
            meetings.append(
                {
                    "title": event["title_en"],
                    "date": event["timestamp"][:10],
                    "agenda": ["Financial results", "Dividend policy", "Governance update"],
                    "status": "Upcoming",
                    "source": event["source_name"],
                }
            )
    if not meetings:
        meetings.append(
            {
                "title": f"{item['symbol']} next governance window",
                "date": (datetime.now(timezone.utc).date() + timedelta(days=32)).isoformat(),
                "agenda": ["Routine governance calendar", "Potential corporate actions"],
                "status": "Monitor",
                "source": "Mock calendar",
            }
        )
    return meetings


def _analysis_for(item: dict, scores: dict, stance: str, confidence: str, factors: list[dict], events: list[dict]) -> dict:
    positive_factors = [factor["label"] for factor in factors if factor["sentiment"] == "positive"]
    cautious_factors = [factor["label"] for factor in factors if factor["sentiment"] == "cautious"]
    return {
        "label": "AI-generated research support. Not personalized investment advice",
        "short_term": {
            "stance": stance,
            "confidence": confidence,
            "reasons": [
                f"Daily move is {item['change_pct']:+.1f}%, so momentum is {'supportive' if item['change_pct'] > 0 else 'soft'}.",
                f"Latest catalyst: {events[0]['event_type'].replace('_', ' ') if events else 'no high-materiality disclosure today'}.",
                f"Global factor map highlights {', '.join(positive_factors[:2]) or 'mixed macro inputs'}.",
                f"Composite house score is {scores['composite']}/100.",
                "Source badges separate official facts from AI interpretation.",
            ],
            "risks": _risks_for(item)[:3] + (cautious_factors[:2] or ["Unexpected disclosure change"]),
            "what_changes_view": "A new official disclosure, dividend timetable change, or material macro shock would recompute the stance.",
        },
        "long_term": {
            "stance": "Bullish" if scores["growth"] >= 72 and scores["stability"] >= 62 else "Neutral" if scores["composite"] >= 58 else "Cautious",
            "confidence": confidence,
            "reasons": [
                f"Growth score: {scores['growth']}/100.",
                f"Stability score: {scores['stability']}/100.",
                f"Dividend score: {scores['dividend']}/100.",
                f"Archetype model: {item['archetype']} names are graded on sector-specific inputs.",
                "Long-term view waits for validated filings before changing numeric inputs.",
            ],
            "risks": _risks_for(item),
            "evidence": ["House scoring model", "Demo financial series", "Exposure map", "Disclosure timeline"],
        },
    }


def _price_signal(quote: dict, scores: dict, stance: str, confidence: str) -> dict:
    price = float(quote["last_price"])
    composite = scores["composite"]
    if composite >= 72 and stance == "Bullish":
        action = "Accumulate"
        target_pct = min(28, max(10, (composite - 58) * 1.1))
        margin = 0.97
    elif composite >= 58:
        action = "Watch"
        target_pct = min(14, max(4, (composite - 54) * 0.7))
        margin = 0.94
    else:
        action = "Avoid"
        target_pct = max(-12, (composite - 55) * 0.6)
        margin = 0.9
    target = price * (1 + target_pct / 100)
    invalidation = price * (0.92 if action != "Avoid" else 0.95)
    return {
        "label": action,
        "buy_or_not": "Buy research zone" if action == "Accumulate" else "Do not buy yet" if action == "Avoid" else "Wait for buy zone",
        "buy_below": round(price * margin, 3 if price < 1 else 2),
        "current_price": round(price, 3 if price < 1 else 2),
        "target_12m": round(target, 3 if target < 1 else 2),
        "expected_return_pct": round(target_pct, 1),
        "invalidation_price": round(invalidation, 3 if invalidation < 1 else 2),
        "confidence": confidence,
        "method": HOUSE_SIGNAL_METHOD,
    }


def build_app_data(output_dir: str | Path = "data") -> dict:
    provider = MockMarketDataProvider()
    quotes = {row["symbol"]: row for row in provider.load_quotes()}
    runtime = _runtime_data()
    for symbol, quote in runtime["live_quotes"].get("quotes", {}).items():
        if symbol in quotes:
            quotes[symbol].update(quote)
    events = sorted(provider.load_events() + runtime["official_disclosures"].get("events", []), key=lambda row: row["timestamp"], reverse=True)
    securities = [_build_security(item, quotes[item["symbol"]], events) for item in SECURITIES]
    now = datetime.now(timezone.utc).isoformat()
    market = runtime["provider_status"].get("market") or market_state().__dict__
    price_status = "Frozen closed-market prices" if not market.get("is_open") else "Public delayed"
    data_quality = "public_delayed" if runtime["live_quotes"].get("quotes") else "demo"
    data = {
        "metadata": {
            "app_name": "UAE Stocks Intelligence",
            "build_time": now,
            "scope": "Isolated Codex build from blueprint DOCX",
            "live_url": "https://khaloodalbastaki-beep.github.io/codex-stocks-app/",
            "market_scope": ["ADX ordinary equities", "DFM ordinary equities"],
            "data_quality": data_quality,
            "price_status": price_status,
            "market": market,
            "disclaimer": "Research support only. Not personalized investment advice. Public/delayed data may be cached or demo when providers fail.",
        },
        "source_badges": _source_badges(),
        "source_providers": SOURCE_PROVIDERS,
        "market_pulse": provider.load_market_pulse(),
        "securities": securities,
        "events": events,
        "official_disclosures": runtime["official_disclosures"],
        "news": runtime["news"],
        "global_signals": list(EXPOSURE_DEFINITIONS.values()),
        "agents": _agent_reports(),
        "admin": _admin(now, runtime["provider_status"], runtime["refresh_job"]),
        "routes": ["/", "/markets/adx", "/markets/dfm", "/ai-research", "/stocks/{symbol}", "/watchlist", "/alerts", "/ipos", "/screeners", "/global-factors", "/admin"],
    }
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "app_data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def _runtime_data() -> dict:
    root = Path(__file__).resolve().parents[1]
    live_quotes = _load_json(root / "data" / "live_quotes.json", {"quotes": {}})
    news = _load_json(
        root / "data" / "news.json",
        {
            "generated_at": None,
            "provider": "not_run",
            "data_quality": "missing",
            "rights_note": "Run tools/update_news.py to fetch real news metadata.",
            "articles": [],
            "errors": [],
        },
    )
    provider_status = _load_json(root / "data" / "provider_status.json", {"market": market_state().__dict__})
    refresh_job = _load_json(root / "data" / "refresh_job.json", _default_refresh_job())
    official_disclosures = _load_json(
        root / "data" / "official_disclosures.json",
        {
            "generated_at": None,
            "provider": "not_run",
            "data_quality": "missing",
            "rights_note": "Run tools/update_disclosures.py to normalize official filing metadata.",
            "sources": [],
            "events": [],
            "errors": [],
        },
    )
    return {
        "live_quotes": live_quotes,
        "news": news,
        "provider_status": provider_status,
        "refresh_job": refresh_job,
        "official_disclosures": official_disclosures,
    }


def _load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _agent_reports() -> dict:
    root = Path(__file__).resolve().parents[1]
    path = root / "agent_out" / "mizan_codex_reports.json"
    if not path.exists():
        return {
            "mizan_codex": {
                "status": "not_run",
                "home": "agents/mizan_codex",
                "runbook": "agents/mizan_codex/RUNBOOK.md",
                "reports": [],
                "latest_by_symbol": {},
            }
        }
    try:
        store = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "mizan_codex": {
                "status": "invalid_json",
                "home": "agents/mizan_codex",
                "runbook": "agents/mizan_codex/RUNBOOK.md",
                "reports": [],
                "latest_by_symbol": {},
            }
        }
    store = _normalize_agent_copy(store)
    store.setdefault("status", "ready")
    store.setdefault("home", "agents/mizan_codex")
    store.setdefault("runbook", "agents/mizan_codex/RUNBOOK.md")
    return {"mizan_codex": store}


def _normalize_agent_copy(value):
    if isinstance(value, str):
        return value.replace(OLD_SIGNAL_METHOD, HOUSE_SIGNAL_METHOD)
    if isinstance(value, list):
        return [_normalize_agent_copy(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_agent_copy(item) for key, item in value.items()}
    return value


def _default_refresh_job() -> dict:
    return {
        "label": "com.bastaki.codex-stocks-refresh",
        "source": "launchd",
        "status": "not_run",
        "interval_seconds": 300,
        "interval_label": "5 minutes",
        "command": "bash tools/refresh_live.sh --deploy",
        "started_at": None,
        "finished_at": None,
        "next_run_after": None,
        "last_exit_code": None,
        "deploy": True,
        "logs": {"stdout": "tmp/refresh.out.log", "stderr": "tmp/refresh.err.log"},
        "quote_policy": "Quote APIs run only during continuous market hours unless --force is passed; closed-market prices stay frozen.",
    }


def _admin(now: str, provider_status: dict | None = None, refresh_job: dict | None = None) -> dict:
    provider_status = provider_status or {}
    refresh_job = refresh_job or _default_refresh_job()
    quote_status = provider_status.get("quotes", {})
    news_status = provider_status.get("news", {})
    disclosure_status = provider_status.get("disclosures", {})
    return {
        "last_build": now,
        "provider_status": provider_status,
        "refresh_job": refresh_job,
        "launch_readiness": [
            {"id": "demo_labels", "label": "Demo labels visible", "status": "pass", "note": "All mock market data is tagged demo/delayed."},
            {"id": "provider_swap", "label": "Provider interfaces", "status": "pass", "note": "UI reads normalized JSON, not vendor-specific fields."},
            {"id": "ai_boundary", "label": "AI boundary", "status": "pass", "note": "Numbers are deterministic; AI copy is labelled research support."},
            {"id": "bilingual", "label": "Arabic original preserved", "status": "pass", "note": "Disclosure cards include Arabic titles and translation badges."},
            {"id": "data_rights", "label": "Market data rights", "status": "blocked", "note": "Real-time redistribution needs licensed feed or exchange approval."},
            {"id": "regulatory", "label": "SCA posture", "status": "blocked", "note": "Public launch needs final compliance review and wording approval."},
        ],
        "jobs": [
            {"source": "Scheduled publish refresh", "last_run": refresh_job.get("finished_at") or refresh_job.get("started_at") or now, "success_rate": 100 if refresh_job.get("status") == "success" else 0, "status": refresh_job.get("status", "not_run"), "queue": 0 if refresh_job.get("last_exit_code") in (None, 0) else 1},
            {"source": "Public quote refresh", "last_run": provider_status.get("generated_at", now), "success_rate": quote_status.get("success", 0), "status": "frozen" if quote_status.get("skipped") else "attempted", "queue": quote_status.get("failed", 0)},
            {"source": "Real news RSS", "last_run": news_status.get("generated_at", now), "success_rate": news_status.get("success", 0), "status": "real_news_metadata", "queue": news_status.get("failed", 0)},
            {"source": "Official filings manifest", "last_run": disclosure_status.get("generated_at", now), "success_rate": disclosure_status.get("success", 0), "status": disclosure_status.get("data_quality", "not_run"), "queue": disclosure_status.get("failed", 0)},
            {"source": "ADX disclosures", "last_run": now, "success_rate": 0, "status": "source_indexed", "queue": 0},
            {"source": "DFM corporate actions", "last_run": disclosure_status.get("generated_at", now), "success_rate": disclosure_status.get("success", 0), "status": "official_metadata", "queue": disclosure_status.get("failed", 0)},
            {"source": "Issuer IR", "last_run": now, "success_rate": 96, "status": "mocked", "queue": 3},
            {"source": "Global factors", "last_run": now, "success_rate": 98, "status": "mocked", "queue": 1},
        ],
        "queues": [
            {"name": "Parsing errors", "count": 0, "tone": "ok"},
            {"name": "Unmapped entities", "count": 2, "tone": "watch"},
            {"name": "Translation queue", "count": 4, "tone": "watch"},
            {"name": "AI extraction queue", "count": 6, "tone": "watch"},
            {"name": "Alert generation queue", "count": 1, "tone": "ok"},
        ],
        "agents": [
            {
                "id": "mizan-codex",
                "name": "Mizan Codex",
                "home": "agents/mizan_codex",
                "default_provider": "ollama",
                "optional_providers": ["gemini", "groq", "openrouter", "stub"],
                "output": "agent_out/mizan_codex_reports.json",
                "hermes": "optional --send-hermes safe-capture bus handoff",
            }
        ],
    }
