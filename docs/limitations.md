# Limitations (honest)

1. **EUA is an auction-average proxy, not a spot/futures series.** Annual (2026: H1) German primary-auction VWAPs from DEHSt are mapped onto every month of that year. Intra-year EUA variation is therefore flattened. Do not treat `eua_eur_t` as a daily carbon price.
2. **TTF / coal are monthly World Bank benchmarks**, not exchange settles. “Natural gas, Europe” is the standard Pink Sheet TTF proxy; South African coal is a seaborne thermal-coal proxy, not the ARA CIF marker.
3. **Energy-Charts rate limits** (~2 req/min on several endpoints). The client chunks by month, caches raw JSON, and backs off on HTTP 429. Large multi-year refreshes are slow by design.
4. **15-minute → hourly mean** resampling (from Oct 2025 Energy-Charts resolution) smooths intra-hour spikes.
5. **No ENTSO-E token** → no official total load / generation per production type from the Transparency Platform. Public net generation from Energy-Charts is the public-net concept, not plant-level.
6. **Processed CSVs may be regenerated**; they are not a archival data product. Always re-run `scripts/run_pipeline.py` for a fresh window.
7. **Currency and calorific conversions are ASSUMED** (see `docs/sources.md`). Freight/handling for coal to plant gate is not added in this repo (unlike the clean-spreads study).
