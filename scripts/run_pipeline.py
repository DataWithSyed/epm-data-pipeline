#!/usr/bin/env python3
"""CLI: fetch public data, assemble panels, validate, write results."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from epmdata.assemble import run_pipeline  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", default="2026-08-01", help="Inclusive start date (Europe/Berlin calendar)")
    p.add_argument("--end", default="2026-10-31", help="Inclusive end date")
    p.add_argument("--refresh", action="store_true", help="Bypass on-disk raw cache")
    args = p.parse_args()
    out = run_pipeline(args.start, args.end, refresh=args.refresh, write=True)
    print(json.dumps(out["summary"]["measured_facts"], indent=2))
    print("Wrote data/processed/ and results/summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
