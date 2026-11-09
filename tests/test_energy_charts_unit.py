from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from epmdata.energy_charts import _parse_v2_frame


def test_parse_v2_frame_basic(tmp_path: Path):
    payload = {
        "license": "CC BY 4.0 (creativecommons.org/licenses/by/4.0), attribution: energy-charts.info",
        "data": [
            {"timestamp": "2026-09-01T00:00:00+02:00", "values": {"day_ahead_price": 42.5}},
            {"timestamp": "2026-09-01T01:00:00+02:00", "values": {"day_ahead_price": 40.0}},
        ],
    }
    df = _parse_v2_frame(payload, {"day_ahead_price": "da_price_eur_mwh"})
    assert len(df) == 2
    assert df["da_price_eur_mwh"].iloc[0] == 42.5
    assert str(df.index.tz) in ("Europe/Berlin", "CET", "CEST") or "Berlin" in str(df.index.tz)
