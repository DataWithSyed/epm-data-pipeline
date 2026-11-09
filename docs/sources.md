# Data sources, licences and attribution

This pipeline **fetches and caches** public data. Raw API payloads in `data/raw/` are git-ignored and must not be committed when a licence forbids redistribution. Processed panels in `data/processed/` are derived summaries intended for analysis under the same attribution requirements.

| Dataset | Endpoint / file | Licence | Attribution required |
|---|---|---|---|
| DE public net generation, load, residual load | Energy-Charts `GET /v2/public_power?country=de` | CC BY 4.0 | Energy-Charts.info (Fraunhofer ISE) |
| DE-LU day-ahead price | Energy-Charts `GET /v2/price?bzn=DE-LU` | CC BY 4.0 | Bundesnetzagentur \| SMARD.de (via Energy-Charts) |
| DE installed power | Energy-Charts `GET /v2/installed_power` | CC BY 4.0 | Energy-Charts.info (Fraunhofer ISE) |
| Natural gas Europe, SA coal, Brent | World Bank Pink Sheet monthly XLSX | CC BY 4.0 (World Bank) | World Bank Commodity Price Data (The Pink Sheet) |
| USD per EUR | ECB Data Portal `EXR/M.USD.EUR.SP00.A` | ECB free reuse | European Central Bank |
| EUA auction average (proxy) | `data/reference/eua_dehst_annual.csv` | Official public DEHSt figures | DEHSt / EEX |

## Licence gate

The price client **refuses** to materialise a bidding zone whose response `license` field is not CC BY. Several Energy-Charts price zones are restricted to private/internal use; only CC BY zones (including DE-LU) are processed.

## Unit conversions (ASSUMED)

| Factor | Value | Use |
|---|---|---|
| MMBtu per MWh | 3.412141156 | gas USD/MMBtu → EUR/MWh_th with ECB FX |
| Coal MWh_th per tonne | `6000 kcal/kg × 4.1868 / 3600` ≈ 6.978 | SA coal USD/t → EUR/MWh_th |

These are labelled **ASSUMED** engineering conventions, consistent with the related `clean-spreads-fuel-switching-de` repo.

## What is intentionally not fetched

- Daily EUA futures closes (exchange proprietary).
- ENTSO-E Transparency Platform bulk dumps (require a registered token; out of scope for this key-free pipeline).
- Non-CC BY Energy-Charts bidding-zone prices.
