from __future__ import annotations

import pandas as pd
import pytest

from epmdata.eua import eua_series_by_month, load_eua_auction_averages
from epmdata.schema import HOURLY_PANEL_COLUMNS, MONTHLY_DRIVER_COLUMNS, SOURCES


def test_sources_have_attribution():
    assert "energy_charts_price" in SOURCES
    for key, meta in SOURCES.items():
        assert meta.attribution, key
        assert meta.licence, key
        assert meta.url.startswith("http"), key


def test_column_lists_stable():
    assert "da_price_eur_mwh" in HOURLY_PANEL_COLUMNS
    assert "eua_eur_t" in MONTHLY_DRIVER_COLUMNS
    assert "gas_eur_mwh_th" in MONTHLY_DRIVER_COLUMNS


def test_eua_reference_loads_and_is_sourced():
    df = load_eua_auction_averages()
    assert len(df) >= 7
    assert df["year"].is_monotonic_increasing
    assert (df["eua_eur_t"] > 0).all()
    assert df["source"].str.contains("DEHSt").all()
    row_2026 = df.set_index("year").loc[2026]
    assert abs(row_2026["eua_eur_t"] - 76.02) < 1e-6
    assert "H1" in row_2026["period_note"]


def test_eua_month_mapping():
    months = pd.period_range("2024-01", "2026-06", freq="M")
    mapped = eua_series_by_month(months)
    assert len(mapped) == len(months)
    assert mapped.loc[pd.Period("2024-06")]["eua_eur_t"] == pytest.approx(65.01)
    assert mapped.loc[pd.Period("2026-03")]["eua_eur_t"] == pytest.approx(76.02)
