#!/usr/bin/env python3
"""Write the scheduled refresh heartbeat consumed by Admin."""

from __future__ import annotations

import argparse
import json
import plistlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "data" / "refresh_job.json"
PLIST_PATH = ROOT / "launchd" / "com.bastaki.codex-stocks-refresh.plist"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load_status() -> dict:
    if not STATUS_PATH.exists():
        return _base_status()
    try:
        data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    return {**_base_status(), **data}


def _base_status() -> dict:
    plist = _load_plist()
    interval = int(plist.get("StartInterval", 300) or 300)
    command = " ".join(str(part) for part in plist.get("ProgramArguments", []))
    if not command:
        command = "bash tools/refresh_live.sh --deploy"
    return {
        "label": plist.get("Label", "com.bastaki.codex-stocks-refresh"),
        "source": "launchd",
        "status": "not_run",
        "interval_seconds": interval,
        "interval_label": _interval_label(interval),
        "command": command,
        "started_at": None,
        "finished_at": None,
        "next_run_after": None,
        "last_exit_code": None,
        "deploy": True,
        "logs": {
            "stdout": "tmp/refresh.out.log",
            "stderr": "tmp/refresh.err.log",
        },
        "quote_policy": "Quote APIs run only during continuous market hours unless --force is passed; closed-market prices stay frozen.",
    }


def _load_plist() -> dict:
    if not PLIST_PATH.exists():
        return {}
    with PLIST_PATH.open("rb") as handle:
        return plistlib.load(handle)


def _interval_label(seconds: int) -> str:
    if seconds % 3600 == 0:
        hours = seconds // 3600
        return f"{hours} hour" if hours == 1 else f"{hours} hours"
    if seconds % 60 == 0:
        minutes = seconds // 60
        return f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"
    return f"{seconds} seconds"


def _write(data: dict) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def start(args: argparse.Namespace) -> None:
    current = _load_status()
    now = _now()
    interval = int(args.interval_seconds or current.get("interval_seconds") or 300)
    current.update(
        {
            "status": "running",
            "started_at": now.isoformat(),
            "finished_at": None,
            "next_run_after": (now + timedelta(seconds=interval)).isoformat(),
            "last_exit_code": None,
            "interval_seconds": interval,
            "interval_label": _interval_label(interval),
            "deploy": args.deploy,
        }
    )
    _write(current)


def finish(args: argparse.Namespace) -> None:
    current = _load_status()
    now = _now()
    interval = int(current.get("interval_seconds") or 300)
    exit_code = int(args.exit_code)
    current.update(
        {
            "status": "success" if exit_code == 0 else "failed",
            "finished_at": now.isoformat(),
            "next_run_after": (now + timedelta(seconds=interval)).isoformat(),
            "last_exit_code": exit_code,
        }
    )
    _write(current)


def main() -> int:
    parser = argparse.ArgumentParser(description="Write UAE stocks refresh heartbeat")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--deploy", action="store_true")
    start_parser.add_argument("--interval-seconds", type=int)
    start_parser.set_defaults(func=start)

    finish_parser = subparsers.add_parser("finish")
    finish_parser.add_argument("--exit-code", type=int, required=True)
    finish_parser.set_defaults(func=finish)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
