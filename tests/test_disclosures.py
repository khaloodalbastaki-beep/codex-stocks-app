import unittest

from tools.update_disclosures import normalize_record


class DisclosureImportTests(unittest.TestCase):
    def test_normalize_official_filing_record(self):
        event = normalize_record(
            {
                "id": "dfm-emaar-test",
                "symbol": "EMAAR",
                "exchange": "DFM",
                "source_name": "DFM official filing",
                "category": "financial_statements",
                "title_en": "Emaar Properties PJSC financial statements",
                "published_at": "2026-02-12T00:00:00+04:00",
                "source_url": "https://www.dfm.ae/the-exchange/news-disclosures/disclosures",
                "document_url": "https://feeds.dfm.ae/documents/example.pdf",
                "signals": ["financial_statements", "dividend_policy"],
            }
        )
        self.assertEqual(event["symbol"], "EMAAR")
        self.assertEqual(event["source_type"], "official_exchange")
        self.assertEqual(event["event_type"], "dividend")
        self.assertEqual(event["data_quality"], "official_metadata")
        self.assertIn("document_url", event)
        self.assertTrue(event["evidence"])


if __name__ == "__main__":
    unittest.main()
