"""ECB USD/EUR reference exchange rate."""
from __future__ import annotations

import io

import pandas as pd

from epmdata.cache import get
from epmdata.paths import RAW

ECB_FX_MONTHLY = (
    "https://data-api.ecb.europa.eu/service/data/EXR/M.USD.EUR.SP00.A"
    "?format=csvdata&startPeriod=2018-01"
)


def fetch_fx_monthly(refresh: bool = False) -> pd.Series:
    """Monthly average USD per 1 EUR (ECB reference)."""
    path = get(ECB_FX_MONTHLY, RAW / "ecb_usd_per_eur_monthly.csv", refresh=refresh)
    d = pd.read_csv(io.StringIO(path.read_text(encoding="utf-8")))
    return pd.Series(
        d["OBS_VALUE"].astype(float).values,
        index=pd.PeriodIndex(d["TIME_PERIOD"], freq="M"),
        name="usd_per_eur",
    )
