"""Deterministic scoring logic.

The model deliberately separates numeric scoring from language generation.
Every number here comes from explicit inputs and can be tested.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def normalize_growth(percent: float) -> float:
    """Map growth percent to a 0-100 score with room for cyclicality."""
    return clamp(50 + percent * 2.2)


def normalize_inverse_percent(percent: float, good_below: float, bad_above: float) -> float:
    """Higher score when the input percent is lower."""
    if percent <= good_below:
        return 90.0
    if percent >= bad_above:
        return 20.0
    span = bad_above - good_below
    return clamp(90 - ((percent - good_below) / span) * 70)


def weighted(parts: Mapping[str, tuple[float, float]]) -> int:
    total_weight = sum(weight for _, weight in parts.values())
    if total_weight <= 0:
        raise ValueError("weights must be positive")
    score = sum(value * weight for value, weight in parts.values()) / total_weight
    return int(round(clamp(score)))


@dataclass(frozen=True)
class HouseScores:
    growth: int
    stability: int
    dividend: int
    composite: int


def score_security(fundamentals: Mapping[str, float], dividend_yield: float) -> HouseScores:
    growth = weighted(
        {
            "revenue_growth": (normalize_growth(fundamentals["revenue_growth"]), 1.2),
            "profit_growth": (normalize_growth(fundamentals["profit_growth"]), 1.2),
            "margin_direction": (fundamentals["margin_trend"] * 10, 0.9),
            "capital_allocation": (fundamentals["capital_allocation"] * 10, 0.8),
            "strategic_expansion": (fundamentals["strategic_expansion"] * 10, 0.7),
            "event_catalysts": (fundamentals["event_catalysts"] * 10, 0.6),
        }
    )
    stability = weighted(
        {
            "leverage": (fundamentals["leverage"] * 10, 1.0),
            "liquidity": (fundamentals["liquidity"] * 10, 1.0),
            "cashflow_consistency": (fundamentals["cashflow_consistency"] * 10, 1.1),
            "volatility": (fundamentals["volatility"] * 10, 0.7),
            "governance_cadence": (fundamentals["governance_cadence"] * 10, 0.8),
            "disclosure_consistency": (fundamentals["disclosure_consistency"] * 10, 0.9),
            "macro_sensitivity": ((10 - fundamentals["macro_sensitivity"]) * 10, 0.7),
        }
    )
    dividend = weighted(
        {
            "yield_quality": (clamp(dividend_yield * 12), 0.8),
            "payout_ratio": (normalize_inverse_percent(fundamentals["payout_ratio"], 35, 95), 1.1),
            "fcf_coverage": (fundamentals["fcf_coverage"] * 10, 1.2),
            "debt_burden": (fundamentals["debt_burden"] * 10, 0.8),
            "cut_history": (fundamentals["cut_history"] * 10, 0.8),
            "frequency": (fundamentals["frequency"] * 10, 0.7),
            "regularity": (fundamentals["regularity"] * 10, 1.0),
        }
    )
    composite = weighted(
        {
            "growth": (growth, 1.0),
            "stability": (stability, 1.1),
            "dividend": (dividend, 0.9),
        }
    )
    return HouseScores(growth=growth, stability=stability, dividend=dividend, composite=composite)


def stance_from_scores(scores: HouseScores, change_pct: float) -> tuple[str, str]:
    """Return a transparent house stance and confidence band."""
    momentum_adjustment = 4 if change_pct > 1.0 else -4 if change_pct < -1.0 else 0
    view_score = scores.composite + momentum_adjustment
    if view_score >= 72:
        stance = "Bullish"
    elif view_score <= 52:
        stance = "Cautious"
    else:
        stance = "Neutral"
    dispersion = max(scores.growth, scores.stability, scores.dividend) - min(
        scores.growth, scores.stability, scores.dividend
    )
    confidence = "high" if dispersion < 12 else "medium" if dispersion < 24 else "low"
    return stance, confidence

