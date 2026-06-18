import unittest

from agents.mizan_codex.agent import deterministic_report, enrich_report, get_security
from brain.pipeline import build_app_data


class MizanAgentTests(unittest.TestCase):
    def test_deterministic_report_has_required_operating_fields(self):
        data = build_app_data()
        stock = get_security(data, "EMAAR")
        report = deterministic_report(data, stock, [], provider="stub", model="deterministic")
        report = enrich_report(report, "stub", "deterministic", stock)
        self.assertEqual(report["symbol"], "EMAAR")
        self.assertIn(report["research_stance"], {"Bullish", "Neutral", "Cautious", "Needs Review"})
        self.assertTrue(report["money_and_accounts"])
        self.assertTrue(report["watch_items"])
        self.assertTrue(report["alert_rules"])
        self.assertIn("Not personalized", report["disclaimer"])


if __name__ == "__main__":
    unittest.main()
