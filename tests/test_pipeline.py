import json
import tempfile
import unittest
from pathlib import Path

from brain.pipeline import build_app_data


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = build_app_data(tmp)
            path = Path(tmp) / "app_data.json"
            self.assertTrue(path.exists())
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["metadata"]["data_quality"], "demo")
            self.assertGreaterEqual(len(loaded["securities"]), 10)
            self.assertIn("launch_readiness", loaded["admin"])
            self.assertEqual(loaded["admin"]["refresh_job"]["interval_seconds"], 300)

    def test_every_security_has_evidence_bound_analysis(self):
        data = build_app_data()
        for security in data["securities"]:
            self.assertIn("AI-generated research support", security["analysis"]["label"])
            self.assertTrue(security["analysis"]["long_term"]["evidence"])
            self.assertEqual(security["quote"]["data_quality"], "demo")
            self.assertIn(security["stance"], {"Bullish", "Neutral", "Cautious"})


if __name__ == "__main__":
    unittest.main()
