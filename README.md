# epm-data-pipeline

**Step 1** of the [European Power Market Lab](https://github.com/DataWithSyed/eu-power-market-lab).

Reproducible **fetch → cache → validate → assemble** pipeline for public European power-market inputs used by the rest of the lab:

| Stream | Source | Licence / attribution |
|---|---|---|
| DE-LU day-ahead price, DE public net generation / load / residual load, installed power | [Energy-Charts](https://api.energy-charts.info) v2 (Fraunhofer ISE); DE-LU prices from Bundesnetzagentur \| SMARD.de | **CC BY 4.0** — attribute as required; non-CC BY bidding zones are refused |
| Natural gas Europe (TTF proxy), SA thermal coal, Brent | World Bank Pink Sheet monthly | **CC BY 4.0** — World Bank Commodity Price Data |
| USD per EUR | ECB Data Portal `EXR/M.USD.EUR.SP00.A` | ECB free reuse with attribution |
| EUA carbon **proxy** | German primary-auction VWAP (`data/reference/eua_dehst_annual.csv`) | Official DEHSt / EEX public figures (not futures) |

Raw API payloads stay in `data/raw/` (**git-ignored**). This repo ships fetch scripts + a small attributed EUA reference table, not a wholesale redistribution of restricted feeds.

## Measured results (real run, 2026-08-01 → 2026-10-15)

All figures below come from `python scripts/run_pipeline.py --start 2026-08-01 --end 2026-10-15` on this machine (Asia/Karachi wall clock 2026-11-09). None are invented.

| Fact | Value |
|---|---|
| Hourly panel rows | **1,824** (76 days × 24 h) |
| DE-LU DA price mean | **140.48 €/MWh** |
| DA price min / max | **−19.00 / 697.31 €/MWh** |
| Share of hours with negative DA price | **5.15 %** (94 h) |
| Residual load mean / min / max | **23,137 / −13,991 / 59,478 MW** |
| Sep 2026 mean DA price | **144.82 €/MWh** |
| Sep 2026 World Bank gas Europe | **25.42 USD/MMBtu** ≈ **75.34 €/MWh_th** (ECB FX) |
| EUA proxy (DEHSt H1-2026 VWAP) | **76.02 €/tCO₂** |
| DE installed solar (AC), end-2026 stock (Energy-Charts) | **120.56 GW** |
| DE installed wind onshore, end-2026 stock | **71.77 GW** |

Monthly drivers (pipeline output):

| month | DA mean €/MWh | gas USD/MMBtu | gas €/MWh_th | coal USD/t | EUA €/t |
|---|---:|---:|---:|---:|---:|
| 2026-08 | 126.89 | 21.11 | 62.13 | 96.8 | 76.02 |
| 2026-09 | 144.82 | 25.42 | 75.34 | 98.2 | 76.02 |
| 2026-10 | 159.89 | — (Pink Sheet not yet published) | — | — | 76.02 |

See `results/summary.json` and `results/measured_facts.md` for the machine-readable dump.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python scripts/run_pipeline.py --start 2026-08-01 --end 2026-10-15
pytest -q
```

Outputs:

- `data/processed/hourly_panel.csv` (+ `.parquet`)
- `data/processed/monthly_drivers.csv`
- `data/processed/installed_power_de_yearly.csv`
- `results/summary.json`

## Tests

`pytest -q` — **11 passed** (schema / EUA reference / validators / Energy-Charts parser / live short-window fetch / full pipeline). Set `EPM_SKIP_LIVE=1` to skip network tests.

## Package layout

```
src/epmdata/
  energy_charts.py   # v2 price, public_power, installed_power (+ CC BY licence gate)
  world_bank.py      # Pink Sheet fuels
  ecb.py             # USD/EUR
  eua.py             # DEHSt auction-average proxy
  assemble.py        # hourly panel + monthly drivers
  validate.py        # data-quality reports
  schema.py          # column contracts + SourceMeta
scripts/run_pipeline.py
tests/
docs/sources.md
docs/limitations.md
```

## Related work (not duplicated)

- [eu-power-market-lab](https://github.com/DataWithSyed/eu-power-market-lab) — umbrella roadmap
- [clean-spreads-fuel-switching-de](https://github.com/DataWithSyed/clean-spreads-fuel-switching-de) — SRMC / switching price study (reuses same public sources)
- [de-day-ahead-price-forecasting](https://github.com/DataWithSyed/de-day-ahead-price-forecasting) — forecast models that will consume this panel in step 5

## Limitations

Read [`docs/limitations.md`](docs/limitations.md). Short version: EUA is an **auction-average proxy** (not futures); fuels are **monthly** Pink Sheet benchmarks; 15-min data is averaged to hours; no ENTSO-E token; Energy-Charts rate limits apply.

## Licence

MIT for code. Upstream data keep their own licences — always attribute (Energy-Charts.info / SMARD.de / World Bank / ECB / DEHSt).
