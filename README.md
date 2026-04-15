# mrel-peer-benchmark

Cross-bank MREL capacity benchmarking tool built on official **EBA Pillar 3 disclosures** (EU KM2, EU TLAC1, EU TLAC3/TLAC3b, ILAC). Anchored on **Banco BPM** as the reference bank, with peer comparison against a tight default peer set and an outlier explorer over the full 113-bank EU universe.

Unlike the aggregate dashboards published by EBA and SRB, this tool benchmarks individual banks against each other on composition, residual maturity, subordination and quarterly trend.

## Status

Bootstrapped. Data ingestion and UI not yet implemented — see `docs/plan.md` for the phased roadmap.

## Data sources

- **Primary:** EBA Pillar 3 cell-level export (`data/raw/p3mreldata_2025q4.xlsx`) — 113 banks, 27 countries, 8 templates, quarterly (2025-06, 2025-09, 2025-12).
- **Supplementary:** Pillar 3 PDFs for banks missing from the EBA export (Intesa Sanpaolo, UniCredit S.p.A., BBVA, Crédit Agricole S.A., Société Générale).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run (once implemented)

```bash
python scripts/ingest.py       # build facts.parquet from EBA export + PDFs
python app/app.py              # Dash app on http://localhost:8050
```

## Repo layout

```
data/          raw inputs + processed parquet + duckdb
ingestion/     EBA export + per-bank PDF parsers
core/          schema, metrics, ranking, peers, captions
app/           Dash app: shell + pages + components
scripts/       ingest + fetch helpers
tests/         pytest
docs/          data dictionary, methodology
```
