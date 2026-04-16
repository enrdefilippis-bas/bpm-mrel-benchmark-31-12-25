# Data dictionary

Mapping from EBA Pillar 3 template cells to the canonical facts schema and to
the derived metrics the UI displays. Anything in this file must match what
is wired in `core/captions.py`, `core/metrics.py` and
`ingestion/missing_banks/base.py` — these modules are the authoritative source
of truth; this document reproduces the same mapping in human-readable form.

## Sources

| Source tag           | Feed                                       | Notes                                           |
|----------------------|--------------------------------------------|-------------------------------------------------|
| `eba-export`         | `data/raw/p3mreldata_2025q4.xlsx`          | Authoritative. 112 banks × 3 quarters in 2025. |
| `pdf-intesa`         | `ingestion/missing_banks/intesa.py`        | Manual-entry JSON until PDF parser lands.      |
| `pdf-unicredit`      | `ingestion/missing_banks/unicredit.py`     | Same.                                          |
| `pdf-bbva`           | `ingestion/missing_banks/bbva.py`          | Same.                                          |
| `pdf-credit-agricole`| `ingestion/missing_banks/credit_agricole.py` | Same.                                        |
| `pdf-socgen`         | `ingestion/missing_banks/socgen.py`        | Same.                                          |

Precedence: the EBA export wins on any LEI overlap. A per-bank source only
contributes rows for LEIs that are absent from the EBA export
(see `ingestion/normalize.merge_sources`).

## Canonical fact schema

Long format, one row per `(entity_lei, template, row_code, col_code,
open_key, reference_date)`.

| Column           | Type            | Meaning                                         |
|------------------|-----------------|-------------------------------------------------|
| `entity_lei`     | `string`        | 20-char Legal Entity Identifier.               |
| `entity_name`    | `string`        | Bank display name.                              |
| `country`        | `string`        | ISO country name (source: bank dimension).      |
| `reference_date` | `datetime64[ns]`| Quarter-end reporting date.                    |
| `template`       | `string`        | EBA template code (see below).                  |
| `row_code`       | `string`        | Template row code, zero-padded (e.g. `0040`).  |
| `row_name`       | `string`        | Template row label (English).                   |
| `col_code`       | `string`        | Template column code.                           |
| `col_name`       | `string`        | Template column label.                          |
| `open_key`       | `string`        | Disaggregation key (rank, maturity, …).        |
| `raw_value`      | `Float64`       | As-reported value, no unit normalisation.      |
| `value`          | `Float64`       | Normalised: ratios as decimals (0.3402 = 34.02%); amounts in EUR. |
| `unit`           | `string`        | `ratio` / `amount_eur`.                        |
| `source`         | `string`        | Source tag (see above).                         |
| `ingested_at`    | `datetime64[ns]`| When this row was produced.                    |

## Templates used

| Code      | Short name | What it contains                                              |
|-----------|------------|---------------------------------------------------------------|
| `K_00.05` | Narrative  | Qualitative disclosures (ignored by this tool).              |
| `K_90.01` | KM2        | Headline MREL/TLAC ratios and amounts.                        |
| `K_91.00` | TLAC1      | Composition of the MREL/TLAC stack by instrument class.       |
| `K_93.00` | ILAC       | Internal TLAC — filed by non-resolution subsidiaries only.   |
| `K_95.00` | CR non-res | Creditor ranking at non-resolution entity (part 1).          |
| `K_96.00` | CR non-res | Creditor ranking at non-resolution entity (part 2).          |
| `K_97.00` | TLAC3      | Creditor ranking at the resolution entity + maturity ladder. |
| `K_98.00` | TLAC3b     | Creditor ranking at a non-resolution subsidiary.             |

## KM2 (K_90.01) — canonical cells

All on column `c0010` (MREL — resolution group).

| Cell        | Metric key                     | Unit      | What it is                                           |
|-------------|--------------------------------|-----------|------------------------------------------------------|
| `r0010`     | `mrel_total_amount`            | €         | Own funds and eligible liabilities — the MREL stack. |
| `r0030`     | `trea`                         | €         | Total Risk Exposure Amount.                          |
| `r0040`     | `mrel_pct_trea`                | ratio     | Headline MREL % of TREA.                             |
| `r0050`     | `subord_pct_trea`              | ratio     | Own funds + subordinated liabilities, % of TREA.     |
| `r0060`     | `tem`                          | €         | Total Exposure Measure (leverage denominator).       |
| `r0070`     | `mrel_pct_tem`                 | ratio     | MREL % of TEM.                                       |
| `r0080`     | `subord_pct_tem`               | ratio     | Subordinated portion, % of TEM.                      |
| `r0120`     | `mrel_requirement_trea`        | ratio     | Binding MREL requirement, % of TREA.                 |
| `r0130`     | `mrel_subord_requirement_trea` | ratio     | Subordination requirement, % of TREA.                |
| `r0140`     | `mrel_requirement_tem`         | ratio     | Binding MREL requirement, % of TEM.                  |
| `r0150`     | `mrel_subord_requirement_tem`  | ratio     | Subordination requirement, % of TEM.                 |

## TLAC1 (K_91.00) — composition cells

All on column `c0010` (MREL).

| Cell    | Composition key                | Instrument class                              |
|---------|--------------------------------|-----------------------------------------------|
| `r0010` | `cet1`                         | Common Equity Tier 1.                        |
| `r0020` | `at1`                          | Additional Tier 1.                           |
| `r0060` | `tier2`                        | Tier 2.                                       |
| `r0100` | `subord_own_issuance`          | Own-issuance subordinated eligible liab.     |
| `r0110` | `subord_intra_group`           | Intra-group subordinated eligible liab.      |
| `r0120` | `subord_grandfathered`         | Grandfathered subordinated eligible liab.    |
| `r0130` | `subord_t2_residual`           | Tier 2 with residual maturity < 1y.           |
| `r0140` | `senior_pre_cap`               | Senior eligible liab. pre Art 72b(3) cap.    |
| `r0150` | `senior_grandfathered`         | Grandfathered senior eligible liab.           |
| `r0160` | `senior_post_cap`              | Senior eligible liab. post-cap amount.        |

Composition classes aggregated by the app (see
`core.metrics.TLAC1_COMPOSITION_CLASSES`):

- **`cet1`**, **`at1`**, **`tier2`** — own funds.
- **`subord_eligible_liabilities`** = `subord_own_issuance + subord_intra_group + subord_grandfathered + subord_t2_residual`.
- **`senior_eligible_liabilities`** = `senior_pre_cap + senior_grandfathered + senior_post_cap`.

## TLAC3 (K_97.00) — creditor ranking and maturity

- **Rank breakdown** → `r0050 c0010`, disaggregated by
  `open_key = "Ranking in insolvency = Rank N"`. Rank 1 is the most senior.
  Used by the Creditor-rank page (resolution scope).
- **Maturity ladder** → `r0060–r0100 c0050` (aggregated across all ranks):
  - `r0060` = 1–2y, `r0070` = 2–5y, `r0080` = 5–10y,
  - `r0090` = 10y+, `r0100` = perpetual.

## TLAC3b (K_98.00) — creditor ranking (non-resolution subsidiary)

- **Rank breakdown** → `r0020 c0010`, disaggregated by `open_key`
  (same Rank-N convention). Used by the Creditor-rank page when the scope
  toggle is set to “Non-resolution subsidiary.”
