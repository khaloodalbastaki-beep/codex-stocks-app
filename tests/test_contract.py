import unittest

from brain.pipeline import build_app_data


class ContractTests(unittest.TestCase):
    def test_required_routes_and_tabs(self):
        data = build_app_data()
        self.assertIn("/admin", data["routes"])
        sample = data["securities"][0]
        self.assertIn("global_factors", sample)
        self.assertIn("dividends", sample)
        self.assertIn("meetings", sample)
        self.assertIn("ownership", sample)
        self.assertIn("price_signal", sample)
        self.assertIn("buy_below", sample["price_signal"])
        self.assertIn("news", data)

    def test_launch_blockers_are_visible(self):
        data = build_app_data()
        blockers = [row for row in data["admin"]["launch_readiness"] if row["status"] == "blocked"]
        ids = {row["id"] for row in blockers}
        self.assertIn("data_rights", ids)
        self.assertIn("regulatory", ids)


if __name__ == "__main__":
    unittest.main()
