"""Live integration tests against public APIs. Uses a short window + cache."""
from __future__ import annotations

import os

import pytest

from epmdata.assemble import run_pipeline
from epmdata.energy_charts import fetch_day_ahead_prices
from epmdata.world_bank import fetch_fuels
from epmdata.ecb import fetch_fx_monthly


@pytest.mark.skipif(os.environ.get("EPM_SKIP_LIVE") == "1", reason="EPM_SKIP_LIVE=1")
def test_fetch_price_short_window():
    df = fetch_day_ahead_prices("2026-10-01", "2026-10-02", refresh=False)
    assert len(df) >= 24  # at least a day of 15-min or hourly
    assert df["da_price_eur_mwh"].notna().mean() > 0.9


@pytest.mark.skipif(os.environ.get("EPM_SKIP_LIVE") == "1", reason="EPM_SKIP_LIVE=1")
def test_fetch_fuels_and_fx():
    fuels = fetch_fuels(refresh=False)
    fx = fetch_fx_monthly(refresh=False)
    assert "gas_usd_mmbtu" in fuels.columns
    assert fuels["gas_usd_mmbtu"].notna().sum() > 100
    assert fx.notna().sum() > 50


@pytest.mark.skipif(os.environ.get("EPM_SKIP_LIVE") == "1", reason="EPM_SKIP_LIVE=1")
def test_run_pipeline_three_months():
    # Aug–Oct 2026: fits in memory, overlaps Pink Sheet months through Sep 2026 typically
    out = run_pipeline("2026-08-01", "2026-10-15", refresh=False, write=True)
    hourly = out["hourly"]
    monthly = out["monthly"]
    summary = out["summary"]
    assert summary["hourly"]["ok"] is True
    assert summary["monthly"]["ok"] is True
    assert len(hourly) >= 24 * 30  # ~2.5 months of hours
    assert len(monthly) >= 2
    assert "da_price_mean_eur_mwh" in summary["measured_facts"]
    # Pink Sheet through Sep 2026 should populate Aug+Sep; Oct may be NaN for fuels
    assert monthly["eua_eur_t"].notna().all()
