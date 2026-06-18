import unittest

from brain.scoring import normalize_growth, score_security, stance_from_scores


class ScoringTests(unittest.TestCase):
    def test_growth_normalization_bounds(self):
        self.assertEqual(normalize_growth(-100), 0)
        self.assertEqual(normalize_growth(100), 100)
        self.assertGreater(normalize_growth(10), normalize_growth(0))

    def test_scores_are_deterministic_and_bounded(self):
        fundamentals = {
            "revenue_growth": 10,
            "profit_growth": 8,
            "margin_trend": 7,
            "capital_allocation": 7,
            "strategic_expansion": 7,
            "event_catalysts": 7,
            "leverage": 7,
            "liquidity": 8,
            "cashflow_consistency": 8,
            "volatility": 6,
            "governance_cadence": 8,
            "disclosure_consistency": 8,
            "macro_sensitivity": 5,
            "payout_ratio": 55,
            "fcf_coverage": 7,
            "debt_burden": 6,
            "cut_history": 8,
            "frequency": 6,
            "regularity": 8,
        }
        first = score_security(fundamentals, 5.0)
        second = score_security(fundamentals, 5.0)
        self.assertEqual(first, second)
        for value in first.__dict__.values():
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)

    def test_stance_uses_composite_and_momentum(self):
        fundamentals = {
            "revenue_growth": 20,
            "profit_growth": 20,
            "margin_trend": 8,
            "capital_allocation": 8,
            "strategic_expansion": 8,
            "event_catalysts": 8,
            "leverage": 8,
            "liquidity": 8,
            "cashflow_consistency": 8,
            "volatility": 8,
            "governance_cadence": 8,
            "disclosure_consistency": 8,
            "macro_sensitivity": 3,
            "payout_ratio": 45,
            "fcf_coverage": 8,
            "debt_burden": 8,
            "cut_history": 8,
            "frequency": 8,
            "regularity": 8,
        }
        scores = score_security(fundamentals, 5.5)
        stance, confidence = stance_from_scores(scores, 1.5)
        self.assertEqual(stance, "Bullish")
        self.assertIn(confidence, {"low", "medium", "high"})


if __name__ == "__main__":
    unittest.main()

