"""Assemble hourly panel + monthly driver table from fetched sources."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from epmdata.ecb import fetch_fx_monthly
from epmdata.energy_charts import fetch_day_ahead_prices, fetch_installed_power, fetch_public_power
from epmdata.eua import eua_series_by_month
from epmdata.paths import PROCESSED, RESULTS
from epmdata.validate import assert_ok, validate_hourly_panel, validate_monthly_drivers
from epmdata.world_bank import fetch_fuels

# Unit conversions (labelled ASSUMED where conventional factors are used)
MMBTU_PER_MWH = 3.412141156  # ASSUMED: IEA/engineering conversion 1 MWh = 3.412141156 MMBtu
# Richards Bay NAR 6000 kcal/kg ≈ 25.12 GJ/t ≈ 6.978 MWh_th/t  (ASSUMED, same convention as clean-spreads)
COAL_MWH_TH_PER_T = 6000 * 4.1868 / 3600  # kcal/kg * kJ/kcal / (kJ/MWh) -> MWh_th/t


def _to_hourly_mean(df: pd.DataFrame) -> pd.DataFrame:
    """Resample 15-min Energy-Charts series to hourly means (Europe/Berlin)."""
    if df.empty:
        return df
    num = df.select_dtypes(include=[np.number])
    other = df[[c for c in df.columns if c not in num.columns]]
    h = num.resample("1h").mean()
    if not other.empty:
        # keep last licence string per hour
        for c in other.columns:
            h[c] = other[c].resample("1h").last()
    return h


def build_hourly_panel(start: str, end: str, *, refresh: bool = False) -> pd.DataFrame:
    prices = fetch_day_ahead_prices(start, end, refresh=refresh)
    power = fetch_public_power(start, end, refresh=refresh)
    prices_h = _to_hourly_mean(prices)
    power_h = _to_hourly_mean(power)
    panel = prices_h.join(power_h, how="outer", rsuffix="_pwr")
    panel = panel.sort_index()
    panel = panel.loc[start:end]

    out = pd.DataFrame(
        {
            "timestamp_berlin": panel.index.astype(str),
            "da_price_eur_mwh": panel.get("da_price_eur_mwh"),
            "load_mw": panel.get("load_mw"),
            "residual_load_mw": panel.get("residual_load_mw"),
            "wind_onshore_mw": panel.get("wind_onshore_mw"),
            "wind_offshore_mw": panel.get("wind_offshore_mw"),
            "solar_mw": panel.get("solar_mw"),
            "fossil_gas_mw": panel.get("fossil_gas_mw"),
            "fossil_hard_coal_mw": panel.get("fossil_hard_coal_mw"),
            "fossil_lignite_mw": panel.get("fossil_lignite_mw"),
            "nuclear_mw": panel.get("nuclear_mw"),
            "biomass_mw": panel.get("biomass_mw"),
            "hydro_mw": panel.get("hydro_mw"),
            "renewable_share_pct": panel.get("renewable_share_pct"),
        }
    )
    return out.reset_index(drop=True)


def build_monthly_drivers(hourly: pd.DataFrame, *, refresh: bool = False) -> pd.DataFrame:
    ts = pd.to_datetime(hourly["timestamp_berlin"], utc=True).dt.tz_convert("Europe/Berlin")
    tmp = hourly.copy()
    tmp["_ts"] = ts
    tmp["month"] = tmp["_ts"].dt.tz_localize(None).dt.to_period("M")
    price_m = tmp.groupby("month")["da_price_eur_mwh"].agg(
        da_price_mean_eur_mwh="mean",
        da_price_p10_eur_mwh=lambda s: s.quantile(0.10),
        da_price_p90_eur_mwh=lambda s: s.quantile(0.90),
    )

    fuels = fetch_fuels(refresh=refresh)
    fx = fetch_fx_monthly(refresh=refresh)
    months = price_m.index
    # align fuels/fx
    gas = fuels.reindex(months)["gas_usd_mmbtu"]
    coal = fuels.reindex(months)["coal_usd_t"]
    brent = fuels.reindex(months)["brent_usd_bbl"]
    usd_eur = fx.reindex(months)

    eua = eua_series_by_month(months)

    # Convert fuels to EUR/MWh_th
    gas_eur_mwh = (gas / usd_eur) * MMBTU_PER_MWH  # USD/MMBtu / (USD/EUR) * MMBtu/MWh
    coal_eur_mwh = (coal / usd_eur) / COAL_MWH_TH_PER_T

    out = pd.DataFrame(
        {
            "month": months.astype(str),
            "da_price_mean_eur_mwh": price_m["da_price_mean_eur_mwh"].values,
            "da_price_p10_eur_mwh": price_m["da_price_p10_eur_mwh"].values,
            "da_price_p90_eur_mwh": price_m["da_price_p90_eur_mwh"].values,
            "gas_usd_mmbtu": gas.values,
            "gas_eur_mwh_th": gas_eur_mwh.values,
            "coal_usd_t": coal.values,
            "coal_eur_mwh_th": coal_eur_mwh.values,
            "brent_usd_bbl": brent.values,
            "usd_per_eur": usd_eur.values,
            "eua_eur_t": eua["eua_eur_t"].values,
            "eua_source_note": eua["eua_source_note"].values,
        }
    )
    return out


def run_pipeline(
    start: str,
    end: str,
    *,
    refresh: bool = False,
    write: bool = True,
) -> dict:
    """Fetch → assemble → validate → optionally write parquet/csv + summary JSON."""
    hourly = build_hourly_panel(start, end, refresh=refresh)
    h_rep = validate_hourly_panel(hourly)
    assert_ok(h_rep)

    monthly = build_monthly_drivers(hourly, refresh=refresh)
    m_rep = validate_monthly_drivers(monthly)
    assert_ok(m_rep)

    installed = fetch_installed_power(refresh=refresh)

    summary = {
        "period": {"start": start, "end": end},
        "hourly": h_rep.stats | {"n_rows": h_rep.n_rows, "ok": h_rep.ok},
        "monthly": m_rep.stats | {"n_rows": m_rep.n_rows, "ok": m_rep.ok},
        "installed_power_rows": int(len(installed)),
        "conversions": {
            "MMBTU_PER_MWH": MMBTU_PER_MWH,
            "COAL_MWH_TH_PER_T": COAL_MWH_TH_PER_T,
            "notes": "ASSUMED engineering conversions; see docs/sources.md",
        },
    }

    # Concrete measured facts for README
    facts = _measured_facts(hourly, monthly, installed)
    summary["measured_facts"] = facts

    if write:
        PROCESSED.mkdir(parents=True, exist_ok=True)
        RESULTS.mkdir(parents=True, exist_ok=True)
        hourly.to_parquet(PROCESSED / "hourly_panel.parquet", index=False)
        hourly.to_csv(PROCESSED / "hourly_panel.csv", index=False)
        monthly.to_csv(PROCESSED / "monthly_drivers.csv", index=False)
        if not installed.empty:
            installed.to_csv(PROCESSED / "installed_power_de_yearly.csv", index=False)
        (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
        (RESULTS / "measured_facts.md").write_text(_facts_markdown(facts, start, end), encoding="utf-8")

    return {"hourly": hourly, "monthly": monthly, "installed": installed, "summary": summary}


def _measured_facts(hourly: pd.DataFrame, monthly: pd.DataFrame, installed: pd.DataFrame) -> dict:
    p = hourly["da_price_eur_mwh"]
    facts = {
        "n_hourly_rows": int(len(hourly)),
        "da_price_mean_eur_mwh": round(float(p.mean()), 2),
        "da_price_min_eur_mwh": round(float(p.min()), 2),
        "da_price_max_eur_mwh": round(float(p.max()), 2),
        "negative_price_hour_share_pct": round(float((p < 0).mean() * 100), 2),
        "months": int(len(monthly)),
    }
    if monthly["gas_usd_mmbtu"].notna().any():
        last = monthly.dropna(subset=["gas_usd_mmbtu"]).iloc[-1]
        facts["last_month"] = str(last["month"])
        facts["last_gas_usd_mmbtu"] = round(float(last["gas_usd_mmbtu"]), 2)
        facts["last_gas_eur_mwh_th"] = round(float(last["gas_eur_mwh_th"]), 2)
        facts["last_eua_eur_t"] = round(float(last["eua_eur_t"]), 2)
        facts["last_da_price_mean_eur_mwh"] = round(float(last["da_price_mean_eur_mwh"]), 2)
    if len(installed):
        # Prefer AC solar name from Energy-Charts installed_power; fall back to DC.
        solar_col = "solar_ac" if "solar_ac" in installed.columns else ("solar_dc" if "solar_dc" in installed.columns else None)
        if solar_col:
            series = installed.dropna(subset=[solar_col])
            if len(series):
                # Prefer the latest historical (non-planned) year with a value
                hist = series[~series["period"].astype(str).str.startswith(("2027", "2028", "2029", "2030"))]
                use = hist if len(hist) else series
                facts["installed_solar_ac_gw_latest"] = round(float(use[solar_col].iloc[-1]), 2)  # Energy-Charts unit: GW
                facts["installed_period_latest"] = str(use["period"].iloc[-1])
        if "wind_onshore" in installed.columns:
            series = installed.dropna(subset=["wind_onshore"])
            hist = series[~series["period"].astype(str).str.startswith(("2027", "2028", "2029", "2030"))]
            use = hist if len(hist) else series
            if len(use):
                facts["installed_wind_onshore_gw_latest"] = round(float(use["wind_onshore"].iloc[-1]), 2)  # GW
    # residual load stats if present
    if hourly["residual_load_mw"].notna().any():
        rl = hourly["residual_load_mw"]
        facts["residual_load_mean_mw"] = round(float(rl.mean()), 1)
        facts["residual_load_min_mw"] = round(float(rl.min()), 1)
        facts["residual_load_max_mw"] = round(float(rl.max()), 1)
    return facts


def _facts_markdown(facts: dict, start: str, end: str) -> str:
    lines = [
        f"# Measured facts ({start} → {end})",
        "",
        "All numbers below come from a real pipeline run on public sources. None are invented.",
        "",
    ]
    for k, v in facts.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    return "\n".join(lines)
