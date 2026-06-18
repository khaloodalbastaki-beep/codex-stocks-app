"""Build the JSON contract consumed by the static PWA."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from brain.adapters.mock import MockMarketDataProvider
from brain.registry import EXPOSURE_DEFINITIONS, SECURITIES, SOURCE_PROVIDERS
from brain.scoring import score_security, stance_from_scores


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


def build_app_data(output_dir: str | Path = "data") -> dict:
    provider = MockMarketDataProvider()
    quotes = {row["symbol"]: row for row in provider.load_quotes()}
    events = sorted(provider.load_events(), key=lambda row: row["timestamp"], reverse=True)
    securities = [_build_security(item, quotes[item["symbol"]], events) for item in SECURITIES]
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "metadata": {
            "app_name": "UAE Stocks Intelligence",
            "build_time": now,
            "scope": "Isolated Codex build from blueprint DOCX",
            "market_scope": ["ADX ordinary equities", "DFM ordinary equities"],
            "data_quality": "demo",
            "price_status": "Demo delayed",
            "disclaimer": "Research support only. Not personalized investment advice. Demo market data.",
        },
        "source_badges": _source_badges(),
        "source_providers": SOURCE_PROVIDERS,
        "market_pulse": provider.load_market_pulse(),
        "securities": securities,
        "events": events,
        "global_signals": list(EXPOSURE_DEFINITIONS.values()),
        "agents": _agent_reports(),
        "admin": _admin(now),
        "routes": ["/", "/markets/adx", "/markets/dfm", "/stocks/{symbol}", "/watchlist", "/alerts", "/ipos", "/screeners", "/global-factors", "/admin"],
    }
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "app_data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


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
    store.setdefault("status", "ready")
    store.setdefault("home", "agents/mizan_codex")
    store.setdefault("runbook", "agents/mizan_codex/RUNBOOK.md")
    return {"mizan_codex": store}


def _admin(now: str) -> dict:
    return {
        "last_build": now,
        "launch_readiness": [
            {"id": "demo_labels", "label": "Demo labels visible", "status": "pass", "note": "All mock market data is tagged demo/delayed."},
            {"id": "provider_swap", "label": "Provider interfaces", "status": "pass", "note": "UI reads normalized JSON, not vendor-specific fields."},
            {"id": "ai_boundary", "label": "AI boundary", "status": "pass", "note": "Numbers are deterministic; AI copy is labelled research support."},
            {"id": "bilingual", "label": "Arabic original preserved", "status": "pass", "note": "Disclosure cards include Arabic titles and translation badges."},
            {"id": "data_rights", "label": "Market data rights", "status": "blocked", "note": "Real-time redistribution needs licensed feed or exchange approval."},
            {"id": "regulatory", "label": "SCA posture", "status": "blocked", "note": "Public launch needs final compliance review and wording approval."},
        ],
        "jobs": [
            {"source": "ADX disclosures", "last_run": now, "success_rate": 100, "status": "mocked", "queue": 0},
            {"source": "DFM corporate actions", "last_run": now, "success_rate": 100, "status": "mocked", "queue": 0},
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
