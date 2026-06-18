"""Optional Hermes bus handoff writer.

Creating a message in `_Bus/inbox/hermes/` is a safe capture in Khalid OS.
The agent only writes there when the operator passes `--send-hermes`.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_VAULT = Path("/Volumes/Samsung_SSD_970_EVO_Plus_Media/Khalid OS")


def write_handoff(report: dict, vault: Path = DEFAULT_VAULT) -> Path:
    inbox = vault / "_Bus" / "inbox" / "hermes"
    inbox.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    symbol = report.get("symbol", "market")
    path = inbox / f"{stamp}-mizan-codex-{symbol}.md"
    body = json.dumps(report, ensure_ascii=False, indent=2)
    path.write_text(
        "\n".join(
            [
                "---",
                "type: agent-message",
                "status: new",
                "from: mizan-codex",
                "to: hermes",
                "sensitive: false",
                f"created: {stamp}",
                "---",
                "",
                f"# Mizan Codex report — {symbol}",
                "",
                "## Request",
                "Use this stock-research report to update the UAE Stocks Intelligence briefing layer.",
                "",
                "## Payload",
                "```json",
                body,
                "```",
                "",
                "## Response",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path

