# Manual-entry Pillar 3 values

These JSON files hold KM2 + TLAC1 headline cells hand-read from the
published Pillar 3 disclosure of each bank that is NOT in the EBA export
(Intesa, UniCredit S.p.A., BBVA, Crédit Agricole S.A., Société Générale).

## Workflow

1. Grab the latest Pillar 3 PDF from the bank's IR page (see
   `BankMeta.ir_page` on each parser in `ingestion/missing_banks/*.py`).
2. Fill the cells you have for each reference date under
   `reference_dates.<YYYY-MM-DD>`. `null` = "not filled in yet" and the
   cell is skipped without error.
3. Values for ratios are **decimals** (0.3402 = 34.02%), consistent with
   the EBA export convention. Values for amounts are in **EUR** (raw,
   not millions). All amounts should be positive.
4. Re-run `python scripts/ingest.py` — the new facts are merged into
   `data/processed/facts.parquet` alongside the EBA export.

## Cell mapping

See `ingestion/missing_banks/base.py` for the authoritative mapping. In
short:

- `km2.*` → K_90.01 (KM2) cells
- `tlac1.*` → K_91.00 (TLAC1) composition cells, all at column c0010

## Precedence

If a bank is later added to the EBA export, the EBA fact wins — see
`ingestion/normalize.merge_sources`.
