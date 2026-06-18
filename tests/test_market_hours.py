from datetime import datetime, timezone
import unittest

from brain.market_hours import market_state


class MarketHoursTests(unittest.TestCase):
    def test_open_during_continuous_trading(self):
        state = market_state(datetime(2026, 6, 18, 8, 30, tzinfo=timezone.utc))
        self.assertTrue(state.is_open)
        self.assertEqual(state.phase, "continuous")

    def test_closed_after_hours(self):
        state = market_state(datetime(2026, 6, 18, 13, 0, tzinfo=timezone.utc))
        self.assertFalse(state.is_open)
        self.assertIn("closed", state.phase)

    def test_closed_on_weekend(self):
        state = market_state(datetime(2026, 6, 20, 8, 30, tzinfo=timezone.utc))
        self.assertFalse(state.is_open)
        self.assertEqual(state.phase, "closed_weekend")


if __name__ == "__main__":
    unittest.main()
