"""German EUA auction-average carbon price proxy (DEHSt / EEX).

Daily EUA futures closes are proprietary and are NOT fetched or redistributed.
This module loads the official German primary-auction volume-weighted averages
published by DEHSt (sourced from EEX), shipped as a small attributed reference
CSV that can be updated when new DEHSt quarterly figures appear.
"""
from __future__ import annotations

import pandas as pd

from epmdata.paths import REFERENCE

REF_CSV = REFERENCE / "eua_dehst_annual.csv"


def load_eua_auction_averages() -> pd.DataFrame:
    """Annual (or sub-annual) DEHSt German auction average EUA price (EUR/tCO2).

    Columns: year, eua_eur_t, period_note, source.
    """
    if not REF_CSV.exists():
        raise FileNotFoundError(
            f"Missing {REF_CSV}. Ship the DEHSt-attributed reference table with the repo."
        )
    df = pd.read_csv(REF_CSV)
    required = {"year", "eua_eur_t", "period_note", "source"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"EUA reference CSV missing columns: {sorted(missing)}")
    df["year"] = df["year"].astype(int)
    df["eua_eur_t"] = df["eua_eur_t"].astype(float)
    return df.sort_values("year").reset_index(drop=True)


def eua_series_by_month(months: pd.PeriodIndex) -> pd.DataFrame:
    """Map each month to the corresponding annual (or H1) DEHSt average.

    Returns DataFrame with eua_eur_t and eua_source_note aligned to ``months``.
    """
    ref = load_eua_auction_averages().set_index("year")
    rows = []
    for m in months:
        if m.year not in ref.index:
            rows.append({"eua_eur_t": float("nan"), "eua_source_note": f"no DEHSt figure for {m.year}"})
            continue
        row = ref.loc[m.year]
        rows.append(
            {
                "eua_eur_t": float(row["eua_eur_t"]),
                "eua_source_note": str(row["period_note"]),
            }
        )
    return pd.DataFrame(rows, index=months)
