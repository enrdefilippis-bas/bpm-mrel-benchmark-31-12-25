# Methodology

How every derived metric in the dashboard is computed, anchored to the Pillar
3 source cell. Pair this with [`data-dictionary.md`](data-dictionary.md),
which maps the underlying template cells, and with `core/metrics.py` which is
the authoritative implementation.

Units: ratios are stored as decimals (0.3402 = 34.02%); amounts are stored in
EUR (not millions). Percentage-point (pp) metrics are differences between two
ratios, also in decimal form.

## Conventions

- `K_{tpl}.rXXXX.cYYYY` is shorthand for a single cell in the EBA template,
  where `tpl` is the template code (`90.01`, `91.00`, `97.00`, `98.00`), `XXXX`
  is the row code and `YYYY` is the column code.
- `open_key` suffixes identify a disaggregation (per insolvency rank, per
  residual-maturity bucket, etc.).
- Missing values are *never* carry-forward. A bank without a KM2 row at a
  reference date is excluded from all aggregates for that date — the UI
  greys out the affected tiles explicitly.

## Headline KM2 metrics

| Metric key                     | Formula                                                       | Unit |
|--------------------------------|---------------------------------------------------------------|------|
| `mrel_total_amount`            | `K_90.01.r0010.c0010`                                         | €    |
| `trea`                         | `K_90.01.r0030.c0010`                                         | €    |
| `tem`                          | `K_90.01.r0060.c0010`                                         | €    |
| `mrel_pct_trea`                | `K_90.01.r0040.c0010`                                         | %    |
| `subord_pct_trea`              | `K_90.01.r0050.c0010`                                         | %    |
| `mrel_pct_tem`                 | `K_90.01.r0070.c0010`                                         | %    |
| `mrel_requirement_trea`        | `K_90.01.r0120.c0010`                                         | %    |
| `mrel_subord_requirement_trea` | `K_90.01.r0130.c0010`                                         | %    |
| `mrel_requirement_tem`         | `K_90.01.r0140.c0010`                                         | %    |
| `mrel_subord_requirement_tem`  | `K_90.01.r0150.c0010`                                         | %    |

## Derived cushion / subordination metrics

| Metric key               | Formula                                                             | Unit |
|--------------------------|---------------------------------------------------------------------|------|
| `mrel_surplus_trea_pp`   | `mrel_pct_trea − mrel_requirement_trea`                             | pp   |
| `mrel_surplus_tem_pp`    | `mrel_pct_tem − mrel_requirement_tem`                               | pp   |
| `subordination_ratio`    | `subord_pct_trea / mrel_pct_trea` (NaN when the denominator is 0)   | %    |

`mrel_surplus_trea_pp > 0` means the bank has a cushion above the binding
MREL requirement. Implementation: `core.metrics.km2_wide`.

## Composition (TLAC1) — stack by class

The Composition page shows five classes summing to the MREL stack
(`total_stack`):

```
cet1                           = K_91.00.r0010.c0010
at1                            = K_91.00.r0020.c0010
tier2                          = K_91.00.r0060.c0010
subord_eligible_liabilities    = r0100 + r0110 + r0120 + r0130  (all c0010)
senior_eligible_liabilities    = r0140 + r0150 + r0160          (all c0010)
total_stack                    = sum of the five classes above
```

Implementation: `core.metrics.tlac1_composition` +
`TLAC1_COMPOSITION_CLASSES`.

The stack total may diverge from KM2 `r0010` because TLAC1 sums ignore
deductions and the Article 72b(3) non-subordination cap, while KM2 reflects
the post-adjustment figure.

## Maturity (TLAC3) — residual-maturity profile

Shares are derived from `K_97.00.cXXXX.c0050` (the “Sum of 1 to n” column,
i.e. aggregated across every insolvency rank):

```
maturity_1_to_2y    = K_97.00.r0060.c0050
maturity_2_to_5y    = K_97.00.r0070.c0050
maturity_5_to_10y   = K_97.00.r0080.c0050
maturity_10y_plus   = K_97.00.r0090.c0050
maturity_perpetual  = K_97.00.r0100.c0050

total_eligible      = sum of the five buckets
<bucket>_share      = <bucket> / total_eligible
```

Shares sum to 1.0 by definition. MREL-eligible liabilities must have
residual maturity ≥ 1y — the `<1y` bucket is excluded on purpose.

Implementation: `core.metrics.tlac3_maturity` + `TLAC3_MATURITY_BUCKETS`.

## Creditor ranking (TLAC3 / TLAC3b)

| Scope            | Source                                                            |
|------------------|-------------------------------------------------------------------|
| `resolution`     | `K_97.00.r0050.c0010`, one row per `Ranking in insolvency = Rank N`. |
| `non_resolution` | `K_98.00.r0020.c0010`, same rank convention.                      |

Rank 1 is the most senior creditor class; higher rank numbers are more
subordinated. The Creditor-rank page stacks the per-rank values and colours
low ranks steel (senior) grading into amber/red (deeply subordinated).

Derived sort metrics shown on the page:

- `senior_share` = sum of Rank 1 + 2 / total across ranks present.
- `subord_share` = sum of Rank ≥ 5 / total across ranks present.

Implementation: `core.metrics.creditor_rank_breakdown` +
`CREDITOR_RANK_SOURCES`.

## Country / universe statistics

- Per-country **median**, **IQR** and **whiskers** are computed directly
  from the per-bank metric values by Plotly `go.Box` — no preaggregation.
- The **peer median**, **peer rank** and **universe rank** surfaced on the
  Cushion page and on the Home tiles are computed in
  `core.ranking.peer_summary` and `core.ranking.rank_in_peer_set`. Ranking
  is stable (ties resolved by LEI) and always ignores `NaN` values.

## Peer set resolution

The default BPM peer set is declared in `core.peers.DEFAULT_BPM_PEERS`. A
peer set is a list of LEIs plus a display label; at query time the LEIs are
intersected with the banks present in the latest ingest to produce the
concrete set of banks the page actually plots. This means the peer set
visibly thins out when banks are missing from the Pillar 3 release — the
page shows `N banks with data / M selected` in the header, so the gap is
always explicit.

## Out-of-scope by design

- **No carry-forward across quarters.** If a bank files KM2 at `2025-09-30`
  but not `2025-12-31`, it is simply excluded from the 2025-12-31 aggregate.
- **No bank-reported estimates.** Every value in the tool is a Pillar 3
  disclosure or directly derived from one; broker forecasts, press releases
  and prospectuses are deliberately excluded.
- **No prospectus-level reconciliation.** The sibling
  `mrel-analysis` project reconciles single-bank prospectus and Pillar 3
  figures; this project is strictly cross-bank benchmark.
