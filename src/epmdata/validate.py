"""Data-quality checks on assembled panels."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from epmdata.schema import HOURLY_PANEL_COLUMNS, MONTHLY_DRIVER_COLUMNS


@dataclass
class ValidationReport:
    name: str
    n_rows: int
    issues: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


def validate_hourly_panel(df: pd.DataFrame) -> ValidationReport:
    rep = ValidationReport(name="hourly_panel", n_rows=len(df))
    if df.empty:
        rep.issues.append("hourly panel is empty")
        return rep

    missing_cols = [c for c in HOURLY_PANEL_COLUMNS if c not in df.columns]
    if missing_cols:
        rep.issues.append(f"missing columns: {missing_cols}")

    # Monotonic unique timestamps
    ts = pd.to_datetime(df["timestamp_berlin"])
    if not ts.is_monotonic_increasing:
        rep.issues.append("timestamps not monotonic increasing")
    if ts.duplicated().any():
        rep.issues.append(f"duplicate timestamps: {int(ts.duplicated().sum())}")

    # Price sanity for DE-LU: allow negatives (common) but flag extremes
    p = df["da_price_eur_mwh"]
    if p.isna().mean() > 0.05:
        rep.issues.append(f"da_price missingness {p.isna().mean():.1%} > 5%")
    if (p.dropna() < -500).any() or (p.dropna() > 4000).any():
        rep.issues.append("da_price outside [-500, 4000] EUR/MWh")

    # Load / residual non-negative where present
    for col in ("load_mw", "wind_onshore_mw", "solar_mw"):
        if col in df.columns and (df[col].dropna() < -1).any():
            rep.issues.append(f"{col} has values < -1 MW")

    rep.stats = {
        "start": str(ts.iloc[0]),
        "end": str(ts.iloc[-1]),
        "da_price_mean": float(p.mean()),
        "da_price_min": float(p.min()),
        "da_price_max": float(p.max()),
        "da_price_missing_pct": float(p.isna().mean() * 100),
        "n_negative_price_hours": int((p < 0).sum()) if hasattr(p, "sum") else 0,
    }
    # After hourly resample, "hours" may be 15-min; count negative intervals
    if "da_price_eur_mwh" in df.columns:
        # reinterpret as intervals
        rep.stats["n_negative_price_intervals"] = int((p < 0).sum())
    return rep


def validate_monthly_drivers(df: pd.DataFrame) -> ValidationReport:
    rep = ValidationReport(name="monthly_drivers", n_rows=len(df))
    if df.empty:
        rep.issues.append("monthly drivers table is empty")
        return rep
    missing_cols = [c for c in MONTHLY_DRIVER_COLUMNS if c not in df.columns]
    if missing_cols:
        rep.issues.append(f"missing columns: {missing_cols}")

    for col in ("gas_usd_mmbtu", "coal_usd_t", "usd_per_eur", "eua_eur_t"):
        s = df[col]
        if s.isna().all():
            rep.issues.append(f"{col} entirely missing")
        if (s.dropna() <= 0).any() and col != "eua_eur_t":
            # fuels/FX must be positive
            rep.issues.append(f"{col} has non-positive values")

    if (df["eua_eur_t"].dropna() < 0).any() or (df["eua_eur_t"].dropna() > 500).any():
        rep.issues.append("eua_eur_t outside [0, 500]")

    rep.stats = {
        "months": int(len(df)),
        "gas_usd_mmbtu_last": float(df["gas_usd_mmbtu"].dropna().iloc[-1]) if df["gas_usd_mmbtu"].notna().any() else None,
        "eua_eur_t_last": float(df["eua_eur_t"].dropna().iloc[-1]) if df["eua_eur_t"].notna().any() else None,
        "da_price_mean_overall": float(df["da_price_mean_eur_mwh"].mean()) if "da_price_mean_eur_mwh" in df else None,
    }
    return rep


def assert_ok(report: ValidationReport) -> None:
    if not report.ok:
        raise AssertionError(f"{report.name} failed: " + "; ".join(report.issues))
