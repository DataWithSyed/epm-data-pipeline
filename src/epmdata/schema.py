"""Column schemas and licence metadata for published tables."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceMeta:
    name: str
    url: str
    licence: str
    attribution: str
    notes: str = ""


SOURCES = {
    "energy_charts_power": SourceMeta(
        name="Energy-Charts public net generation",
        url="https://api.energy-charts.info/v2/public_power",
        licence="CC BY 4.0",
        attribution="Energy-Charts.info (Fraunhofer ISE)",
        notes="Response licence field is authoritative; do not redistribute raw JSON if licence changes.",
    ),
    "energy_charts_price": SourceMeta(
        name="Energy-Charts day-ahead price (DE-LU)",
        url="https://api.energy-charts.info/v2/price",
        licence="CC BY 4.0",
        attribution="Bundesnetzagentur | SMARD.de (via Energy-Charts.info)",
        notes="DE-LU prices are CC BY 4.0; other bidding zones may be restricted — check response.licence.",
    ),
    "energy_charts_installed": SourceMeta(
        name="Energy-Charts installed power",
        url="https://api.energy-charts.info/v2/installed_power",
        licence="CC BY 4.0",
        attribution="Energy-Charts.info (Fraunhofer ISE)",
    ),
    "world_bank_pink": SourceMeta(
        name="World Bank Commodity Price Data (Pink Sheet)",
        url="https://www.worldbank.org/en/research/commodity-markets",
        licence="CC BY 4.0 (World Bank)",
        attribution="World Bank Commodity Price Data (The Pink Sheet)",
        notes="Natural gas Europe used as TTF proxy; Coal South Africa as thermal-coal proxy.",
    ),
    "ecb_fx": SourceMeta(
        name="ECB reference exchange rate USD/EUR",
        url="https://data-api.ecb.europa.eu/service/data/EXR",
        licence="ECB free reuse with attribution",
        attribution="European Central Bank",
    ),
    "dehst_eua": SourceMeta(
        name="German EUA auction average prices",
        url="https://www.dehst.de/DE/Themen/EU-ETS-1/EU-ETS-1-Informationen/Versteigerung/versteigerung_node.html",
        licence="Official public reference figures (DEHSt / EEX)",
        attribution="DEHSt (German Emissions Trading Authority) / EEX",
        notes=(
            "Annual (and 2026 H1) volume-weighted German auction averages. "
            "This is an auction-average PROXY for the EUA carbon price, not a futures close. "
            "Daily EUA futures quotes are not redistributed here."
        ),
    ),
}

HOURLY_PANEL_COLUMNS = [
    "timestamp_berlin",
    "da_price_eur_mwh",
    "load_mw",
    "residual_load_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "fossil_gas_mw",
    "fossil_hard_coal_mw",
    "fossil_lignite_mw",
    "nuclear_mw",
    "biomass_mw",
    "hydro_mw",
    "renewable_share_pct",
]

MONTHLY_DRIVER_COLUMNS = [
    "month",
    "da_price_mean_eur_mwh",
    "da_price_p10_eur_mwh",
    "da_price_p90_eur_mwh",
    "gas_usd_mmbtu",
    "gas_eur_mwh_th",
    "coal_usd_t",
    "coal_eur_mwh_th",
    "brent_usd_bbl",
    "usd_per_eur",
    "eua_eur_t",
    "eua_source_note",
]
