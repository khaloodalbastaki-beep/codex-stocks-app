"""CLI entrypoint for the local deterministic brain."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from brain.pipeline import build_app_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Build UAE Stocks Intelligence demo data")
    parser.add_argument("--out", default="data", help="Output directory for generated JSON")
    parser.add_argument("--copy-web", action="store_true", help="Also copy JSON into web/data")
    args = parser.parse_args()

    data = build_app_data(args.out)
    if args.copy_web:
        web_data = Path("web/data")
        web_data.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(args.out) / "app_data.json", web_data / "app_data.json")
    print(
        f"built {len(data['securities'])} securities + {len(data['events'])} events "
        f"-> {Path(args.out).resolve()} (data_quality={data['metadata']['data_quality']})"
    )


if __name__ == "__main__":
    main()

