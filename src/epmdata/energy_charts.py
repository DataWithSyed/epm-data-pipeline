"""Energy-Charts v2 API clients (CC BY 4.0; check response licence)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from epmdata.cache import get
from epmdata.paths import RAW

EC_BASE = "https://api.energy-charts.info"
TZ = "Europe/Berlin"

# Canonical series ids we care about from /v2/public_power
POWER_SERIES = {
    "load": "load_mw",
    "residual_load": "residual_load_mw",
    "wind_onshore": "wind_onshore_mw",
    "wind_offshore": "wind_offshore_mw",
    "solar": "solar_mw",
    "fossil_gas": "fossil_gas_mw",
    "fossil_hard_coal": "fossil_hard_coal_mw",
    "fossil_brown_coal_lignite": "fossil_lignite_mw",
    "nuclear": "nuclear_mw",
    "biomass": "biomass_mw",
    "hydro_run_of_river": "hydro_ror_mw",
    "hydro_water_reservoir": "hydro_reservoir_mw",
    "hydro_pumped_storage": "hydro_ps_mw",
    "renewable_share_of_generation": "renewable_share_pct",
}


def _chunk_bounds(start: str, end: str, freq: str = "MS") -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Month-sized chunks to stay under API payload / rate limits."""
    s = pd.Timestamp(start)
    e = pd.Timestamp(end)
    month_starts = pd.date_range(s.normalize().replace(day=1), e, freq=freq)
    if len(month_starts) == 0 or month_starts[0] > s:
        month_starts = month_starts.insert(0, s.normalize().replace(day=1))
    out: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for i, a in enumerate(month_starts):
        if i + 1 < len(month_starts):
            b = pd.Timestamp(month_starts[i + 1]) - pd.Timedelta(days=1)
        else:
            b = e
        a2 = max(pd.Timestamp(a), s)
        b2 = min(pd.Timestamp(b), e)
        if a2 <= b2:
            out.append((a2, b2))
    return out


def _parse_v2_frame(payload: dict, value_map: dict[str, str]) -> pd.DataFrame:
    licence = payload.get("license") or payload.get("licence") or ""
    rows = []
    for rec in payload.get("data") or []:
        ts = rec.get("timestamp")
        vals = rec.get("values") or {}
        row = {"timestamp": ts, "_licence": licence}
        for src, dst in value_map.items():
            if src in vals:
                row[dst] = vals[src]
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
    # timestamps are Europe/Berlin wall times with offset; localize consistently
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize(TZ, ambiguous="infer", nonexistent="shift_forward")
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert(TZ)
    return df.set_index("timestamp").sort_index()


def fetch_day_ahead_prices(
    start: str,
    end: str,
    *,
    bzn: str = "DE-LU",
    refresh: bool = False,
) -> pd.DataFrame:
    """Day-ahead price (EUR/MWh) for a bidding zone. Returns columns da_price_eur_mwh, _licence."""
    parts = []
    for a, b in _chunk_bounds(start, end):
        url = f"{EC_BASE}/v2/price?bzn={bzn}&start={a:%Y-%m-%d}&end={b:%Y-%m-%d}"
        dest = RAW / f"ec_v2_price_{bzn}_{a:%Y%m%d}_{b:%Y%m%d}.json"
        path = get(url, dest, refresh=refresh)
        payload = json.loads(path.read_text(encoding="utf-8"))
        lic = payload.get("license") or ""
        if "CC BY" not in lic.upper() and lic:
            # Refuse to materialise non-CC zones into processed tables.
            raise RuntimeError(
                f"Bidding zone {bzn} price licence is not CC BY ({lic!r}). "
                "Only redistribute / process CC BY zones (e.g. DE-LU)."
            )
        df = _parse_v2_frame(payload, {"day_ahead_price": "da_price_eur_mwh"})
        if not df.empty:
            parts.append(df)
    if not parts:
        return pd.DataFrame(columns=["da_price_eur_mwh", "_licence"])
    out = pd.concat(parts).sort_index()
    out = out[~out.index.duplicated(keep="last")]
    return out.loc[start:end]


def fetch_public_power(
    start: str,
    end: str,
    *,
    country: str = "de",
    refresh: bool = False,
) -> pd.DataFrame:
    """Public net generation + load series (MW / %)."""
    parts = []
    for a, b in _chunk_bounds(start, end):
        url = f"{EC_BASE}/v2/public_power?country={country}&start={a:%Y-%m-%d}&end={b:%Y-%m-%d}"
        dest = RAW / f"ec_v2_power_{country}_{a:%Y%m%d}_{b:%Y%m%d}.json"
        path = get(url, dest, refresh=refresh)
        payload = json.loads(path.read_text(encoding="utf-8"))
        df = _parse_v2_frame(payload, POWER_SERIES)
        if not df.empty:
            parts.append(df)
    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts).sort_index()
    out = out[~out.index.duplicated(keep="last")]
    # Hydro aggregate (run-of-river + reservoir + pumped generation)
    hydro_cols = [c for c in ("hydro_ror_mw", "hydro_reservoir_mw", "hydro_ps_mw") if c in out.columns]
    if hydro_cols:
        out["hydro_mw"] = out[hydro_cols].sum(axis=1, min_count=1)
    return out.loc[start:end]


def fetch_installed_power(
    *,
    country: str = "de",
    time_step: str = "yearly",
    refresh: bool = False,
) -> pd.DataFrame:
    """Installed capacity by production type (MW) at end of each year/month."""
    url = f"{EC_BASE}/v2/installed_power?country={country}&time_step={time_step}"
    dest = RAW / f"ec_v2_installed_{country}_{time_step}.json"
    path = get(url, dest, refresh=refresh)
    payload = json.loads(path.read_text(encoding="utf-8"))
    # wide: each timestamp has values dict
    rows = []
    for rec in payload.get("data") or []:
        row = {"period": rec.get("timestamp"), **(rec.get("values") or {})}
        rows.append(row)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df
