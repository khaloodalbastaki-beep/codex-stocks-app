"""Adapter contracts.

Future live providers should implement these methods and return the same
normalized shapes as the mock adapter. The UI never depends on a vendor.
"""

from __future__ import annotations

from typing import Protocol


class MarketDataProvider(Protocol):
    provider_id: str
    data_quality: str

    def load_quotes(self) -> list[dict]:
        ...

    def load_events(self) -> list[dict]:
        ...

    def load_market_pulse(self) -> list[dict]:
        ...

