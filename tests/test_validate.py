from __future__ import annotations

import pandas as pd
import pytest

from epmdata.schema import HOURLY_PANEL_COLUMNS, MONTHLY_DRIVER_COLUMNS
from epmdata.validate import validate_hourly_panel, validate_monthly_drivers


def _empty_hourly(n=48):
    idx = pd.date_range("2026-09-01", periods=n, freq="h", tz="Europe/Berlin")
    data = {c: 0.0 for c in HOURLY_PANEL_COLUMNS if c != "timestamp_berlin"}
    data["timestamp_berlin"] = idx.astype(str)
    data["da_price_eur_mwh"] = [40.0 + (i % 24) for i in range(n)]
    data["load_mw"] = [50000.0] * n
    return pd.DataFrame(data)


def test_validate_hourly_ok():
    rep = validate_hourly_panel(_empty_hourly())
    assert rep.ok, rep.issues
    assert rep.stats["n_negative_price_intervals"] == 0


def test_validate_hourly_flags_duplicates():
    df = _empty_hourly(10)
    df.loc[5, "timestamp_berlin"] = df.loc[4, "timestamp_berlin"]
    rep = validate_hourly_panel(df)
    assert not rep.ok
    assert any("duplicate" in i for i in rep.issues)


def test_validate_monthly_ok():
    df = pd.DataFrame(
        {
            "month": ["2026-08", "2026-09"],
            "da_price_mean_eur_mwh": [70.0, 80.0],
            "da_price_p10_eur_mwh": [10.0, 20.0],
            "da_price_p90_eur_mwh": [120.0, 130.0],
            "gas_usd_mmbtu": [10.0, 11.0],
            "gas_eur_mwh_th": [30.0, 32.0],
            "coal_usd_t": [100.0, 105.0],
            "coal_eur_mwh_th": [12.0, 13.0],
            "brent_usd_bbl": [80.0, 82.0],
            "usd_per_eur": [1.1, 1.1],
            "eua_eur_t": [76.02, 76.02],
            "eua_source_note": ["H1", "H1"],
        }
    )
    assert set(MONTHLY_DRIVER_COLUMNS) <= set(df.columns)
    rep = validate_monthly_drivers(df)
    assert rep.ok, rep.issues
