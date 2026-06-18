"""UAE exchange market-hours helpers.

ADX and DFM continuous trading are treated as Monday-Friday 10:00-14:45
Asia/Dubai. Pre-open/close phases are surfaced as status, but quote refreshes
only happen during continuous trading unless a script is run with `--force`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo


DUBAI_TZ = ZoneInfo("Asia/Dubai")
PRE_OPEN = time(9, 30)
OPEN = time(10, 0)
CLOSE = time(14, 45)
TRADE_AT_LAST_END = time(15, 0)


@dataclass(frozen=True)
class MarketState:
    is_open: bool
    phase: str
    label: str
    now_local: str
    timezone: str
    next_change_hint: str


def market_state(now: datetime | None = None) -> MarketState:
    current = (now or datetime.now(timezone.utc)).astimezone(DUBAI_TZ)
    weekday = current.weekday()
    current_time = current.time()
    if weekday >= 5:
        return _state(False, "closed_weekend", "Market closed", current, "Next session: Monday 10:00 GST")
    if current_time < PRE_OPEN:
        return _state(False, "closed_pre_market", "Market closed", current, "Pre-open starts 09:30 GST")
    if PRE_OPEN <= current_time < OPEN:
        return _state(False, "pre_open", "Pre-open", current, "Continuous trading starts 10:00 GST")
    if OPEN <= current_time < CLOSE:
        return _state(True, "continuous", "Market open", current, "Continuous trading ends 14:45 GST")
    if CLOSE <= current_time < TRADE_AT_LAST_END:
        return _state(False, "closing_auction", "Closing auction", current, "Quotes frozen after continuous trading")
    return _state(False, "closed_after_hours", "Market closed", current, "Next session: next trading day 10:00 GST")


def _state(is_open: bool, phase: str, label: str, current: datetime, hint: str) -> MarketState:
    return MarketState(
        is_open=is_open,
        phase=phase,
        label=label,
        now_local=current.isoformat(),
        timezone="Asia/Dubai",
        next_change_hint=hint,
    )

