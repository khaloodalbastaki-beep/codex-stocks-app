"""Mock provider for isolated local development."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from brain.registry import SECURITIES


class MockMarketDataProvider:
    provider_id = "mock-demo"
    data_quality = "demo"

    def __init__(self, now: datetime | None = None):
        self.now = now or datetime.now(timezone.utc)

    def load_quotes(self) -> list[dict]:
        rows = []
        for item in SECURITIES:
            rows.append(
                {
                    "symbol": item["symbol"],
                    "last_price": item["price"],
                    "change_pct": item["change_pct"],
                    "currency": item["currency"],
                    "volume_m": item["volume_m"],
                    "market_cap_bn": item["market_cap_bn"],
                    "provider": self.provider_id,
                    "data_quality": self.data_quality,
                    "status_label": "Demo delayed",
                    "as_of": self.now.isoformat(),
                }
            )
        return rows

    def load_market_pulse(self) -> list[dict]:
        return [
            {
                "id": "ADX",
                "label": "ADX",
                "level": "10,184",
                "change_pct": 0.42,
                "breadth": "26 up / 18 down",
                "data_quality": "demo",
            },
            {
                "id": "DFMGI",
                "label": "DFMGI",
                "level": "6,238",
                "change_pct": 0.76,
                "breadth": "19 up / 11 down",
                "data_quality": "demo",
            },
            {
                "id": "BANKS",
                "label": "Banks",
                "level": "Sector",
                "change_pct": 0.36,
                "breadth": "Margins steady",
                "data_quality": "derived-demo",
            },
            {
                "id": "REAL_ESTATE",
                "label": "Real estate",
                "level": "Sector",
                "change_pct": 1.18,
                "breadth": "Dubai names leading",
                "data_quality": "derived-demo",
            },
        ]

    def load_events(self) -> list[dict]:
        base = self.now.replace(hour=7, minute=15, second=0, microsecond=0)
        return [
            {
                "id": "evt-emaar-board",
                "symbol": "EMAAR",
                "source_type": "official_exchange",
                "source_name": "DFM disclosure",
                "event_type": "board_meeting",
                "title_en": "Board meeting scheduled to review interim financials and dividend policy",
                "title_ar": "اجتماع مجلس الإدارة لمراجعة البيانات المالية المرحلية وسياسة التوزيعات",
                "summary": "Agenda flags interim results, capital allocation, and distribution policy.",
                "why_it_matters": "Board agenda includes dividend policy, making it price-relevant for income holders.",
                "materiality": 78,
                "sentiment": "Positive",
                "timestamp": (base - timedelta(hours=2)).isoformat(),
                "evidence": ["DFM official disclosure", "Board agenda terms extracted"],
            },
            {
                "id": "evt-fab-results",
                "symbol": "FAB",
                "source_type": "issuer_ir",
                "source_name": "Issuer IR",
                "event_type": "results",
                "title_en": "Quarterly results show stable net interest income and controlled credit costs",
                "title_ar": "نتائج ربع سنوية تظهر استقرار صافي دخل الفوائد وتكاليف ائتمان منضبطة",
                "summary": "Revenue and profit trends remain supportive; credit quality is the watch item.",
                "why_it_matters": "Bank score is sensitive to asset quality and rate margin direction.",
                "materiality": 72,
                "sentiment": "Neutral",
                "timestamp": (base - timedelta(hours=5)).isoformat(),
                "evidence": ["Issuer results presentation", "Income statement trend"],
            },
            {
                "id": "evt-dewa-dividend",
                "symbol": "DEWA",
                "source_type": "official_exchange",
                "source_name": "DFM corporate actions",
                "event_type": "dividend",
                "title_en": "Dividend entitlement and payment window added to corporate actions calendar",
                "title_ar": "إضافة تاريخ الاستحقاق وفترة الدفع إلى تقويم إجراءات الشركات",
                "summary": "The event updates entitlement, ex-dividend, and payment timing.",
                "why_it_matters": "Income investors need exact dates, not just yield.",
                "materiality": 81,
                "sentiment": "Positive",
                "timestamp": (base - timedelta(days=1)).isoformat(),
                "evidence": ["Corporate actions calendar", "Dividend timetable"],
            },
            {
                "id": "evt-adports-contract",
                "symbol": "ADPORTS",
                "source_type": "media",
                "source_name": "Official media office",
                "event_type": "contract",
                "title_en": "Logistics expansion headline linked to regional trade corridor",
                "title_ar": "خبر توسع لوجستي مرتبط بممر تجاري إقليمي",
                "summary": "New logistics activity could strengthen long-term trade exposure.",
                "why_it_matters": "Growth score responds to contract-backed expansion, not generic headlines.",
                "materiality": 66,
                "sentiment": "Positive",
                "timestamp": (base - timedelta(days=1, hours=4)).isoformat(),
                "evidence": ["Official media headline", "Exposure map: trade and freight"],
            },
            {
                "id": "evt-americana-inputs",
                "symbol": "AMERICANA",
                "source_type": "global_signal",
                "source_name": "Commodity monitor",
                "event_type": "macro_factor",
                "title_en": "Food input basket moved higher; margin sensitivity flagged",
                "title_ar": "ارتفاع سلة مدخلات الغذاء مع تنبيه لحساسية الهوامش",
                "summary": "Input-cost pressure increases the burden on restaurant margins.",
                "why_it_matters": "A revenue decline plus higher inputs lowers the short-term stance.",
                "materiality": 61,
                "sentiment": "Cautious",
                "timestamp": (base - timedelta(days=2)).isoformat(),
                "evidence": ["Commodity factor basket", "Exposure map: food inputs"],
            },
        ]

