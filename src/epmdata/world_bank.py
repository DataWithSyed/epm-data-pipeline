"""World Bank Pink Sheet commodity prices (CC BY 4.0)."""
from __future__ import annotations

import pandas as pd

from epmdata.cache import get
from epmdata.paths import RAW

WB_PINK_SHEET = (
    "https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/"
    "related/CMO-Historical-Data-Monthly.xlsx"
)


def fetch_fuels(refresh: bool = False) -> pd.DataFrame:
    """Monthly USD fuel prices: gas Europe (TTF proxy), SA coal, Brent.

    Returns a DataFrame indexed by monthly Period with columns
    gas_usd_mmbtu, coal_usd_t, brent_usd_bbl.
    """
    path = get(WB_PINK_SHEET, RAW / "CMO-Historical-Data-Monthly.xlsx", refresh=refresh, binary=True)
    raw = pd.read_excel(path, sheet_name="Monthly Prices", header=None)
    header_row = raw.index[raw.iloc[:, 1].map(lambda x: "Crude oil, average" in str(x))][0]
    names = pd.Series([str(x).strip() if pd.notna(x) else "" for x in raw.iloc[header_row]])
    data = raw.iloc[header_row + 2 :].copy()
    data.columns = ["month"] + list(names.iloc[1:])
    data = data[data["month"].astype(str).str.match(r"^\d{4}M\d{2}$")]

    def col(prefix: str) -> str:
        hits = [c for c in names if str(c).startswith(prefix)]
        if not hits:
            raise KeyError(f"Pink Sheet column starting with {prefix!r} not found")
        return hits[0]

    gas_c = col("Natural gas, Europe")
    # Sheet spelling varies: "Coal, South African" vs "Coal, South Africa"
    coal_hits = [c for c in names if str(c).startswith("Coal, South Africa")]
    if not coal_hits:
        raise KeyError("Pink Sheet coal column not found")
    coal_c = coal_hits[0]
    brent_c = col("Crude oil, Brent")

    out = pd.DataFrame(
        {
            "gas_usd_mmbtu": pd.to_numeric(data[gas_c], errors="coerce").values,
            "coal_usd_t": pd.to_numeric(data[coal_c], errors="coerce").values,
            "brent_usd_bbl": pd.to_numeric(data[brent_c], errors="coerce").values,
        },
        index=pd.PeriodIndex([str(m).replace("M", "-") for m in data["month"]], freq="M"),
    )
    return out.dropna(how="all")
