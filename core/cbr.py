"""Combined Buffer Requirement (CBR) lookup + MREL requirement normalization.

The EBA Pillar 3 cell-level export **does not include CBR** (row 0160 of
K_90.01 is absent for every bank in the 2025 release), so we cannot read
CBR from the export. Banks disclose CBR — and, crucially, *whether their
MREL-TREA requirement already includes it* — only in the narrative body
of their Pillar 3 PDFs.

The canonical KM2 filing convention, per SRB/EBA instructions and
explicitly cited in Banco BPM's Pillar 3 ("*i requisiti MREL-TREA sono
riportati al netto del requisito combinato di riserva di capitale*"), is
**on_top**: the MREL-TREA requirement shown in KM2 row 0120 EXCLUDES the
CBR, which the bank must meet in addition. Some banks (notably
Mediobanca, Iccrea) deviate and publish the figure already inclusive of
CBR. A per-bank flag is therefore needed to make requirements comparable.

This module is the single source of truth for:
- `CBR_DISCLOSURES` — per-(LEI, ref-date) CBR treatment + value
- `normalize_requirement` — derive `req_ex_cbr` and `req_with_cbr` from the
  raw KM2 r0120 using the disclosure flag + CBR value
- `infer_cbr_treatment` — apply the fallback rule when treatment unknown:
  if capacity < req + CBR (would breach under on_top assumption), then the
  published req more likely already includes CBR (reclassify to `included`)

The lookup values below are sourced from:
- the sibling `mrel-analysis/cbr/dataset.csv` scrape of Italian Pillar 3 PDFs;
- explicit BBVA footnote ("MREL requirement includes CBR per BBVA footnote");
- the EU KM2 filing-instruction default (`on_top`) where no explicit
  disclosure is available.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

import pandas as pd


class CbrTreatment(str, Enum):
    """How the MREL-TREA requirement figure relates to the CBR.

    ``on_top`` — the disclosed req EXCLUDES CBR (CBR must be added on top).
    ``included`` — the disclosed req already INCLUDES CBR (don't double-count).
    ``unknown`` — treatment not determined; the fallback inference rule applies.
    """

    ON_TOP = "on_top"
    INCLUDED = "included"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CbrDisclosure:
    """Per-bank CBR evidence from a narrative Pillar 3 source."""

    cbr_pct_trea: float | None     # CBR as a decimal share of TREA, e.g. 0.0359
    treatment: CbrTreatment        # how the KM2 r0120 figure is reported
    source: str                    # free-text citation ("BPM Pillar 3 30-06-2025 p.21")
    is_estimate: bool = False      # True when cbr_pct_trea is a placeholder


# Per-(LEI, reference_date_iso) CBR evidence. Keys are tuples
# (entity_lei, "YYYY-MM-DD"). A missing key falls through to
# `DEFAULT_CBR_ESTIMATE` (CCB 2.5% + typical Italian O-SII buffer 1.0% =
# 3.5%) and treatment `ON_TOP` — the KM2 filing default.
#
# Sources are explicit in-PDF quotes where possible. The CBR value (not
# the treatment) is independently reported by the bank in the same or
# adjacent paragraph.
CBR_DISCLOSURES: Final[dict[tuple[str, str], CbrDisclosure]] = {
    # Banco BPM — reference bank. Footnote in P3 2025-Q2 cites the KM2
    # filing instruction explicitly: reqs reported net of CBR.
    ("815600E4E6DCD2D25E30", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.0355,  # 2.5 CCB + 0.50 O-SII + ~0.55 CCyB (IT+foreign)
        treatment=CbrTreatment.ON_TOP,
        source="BPM Pillar 3 30-06-2025 p.21",
        is_estimate=True,  # CBR value inferred; treatment explicit
    ),
    ("815600E4E6DCD2D25E30", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.0355,
        treatment=CbrTreatment.ON_TOP,
        source="BPM Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    ("815600E4E6DCD2D25E30", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.0374,  # explicit: P3 dicembre 2025 ITA p.27
        treatment=CbrTreatment.ON_TOP,
        source="BPM Pillar 3 31-12-2025 ITA p.27 ('requisito combinato di riserva di capitale ... è pari a 3,74%')",
        is_estimate=False,
    ),
    # Intesa Sanpaolo — Pillar 3 31-12-2025 EU KM1 row 11 explicit: CBR = 4.49%
    # (CCB 2.50 + CCyB 0.31 + SyRB 0.43 + O-SII 1.25); req_ex_cbr = 21.00%,
    # req_inc_cbr = 25.49%. Q2/Q3 2025 use Q2 explicit value 4.48%.
    # Updated 19 May 2026 with primary verification on Pillar 3 dic 2025 PDF.
    ("2W8N8UU78PMDQKZENC08", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.0448,
        treatment=CbrTreatment.ON_TOP,
        source="Intesa Pillar 3 30-06-2025 EU KM1 row 11 (4.48%)",
        is_estimate=False,
    ),
    ("2W8N8UU78PMDQKZENC08", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.0449,
        treatment=CbrTreatment.ON_TOP,
        source="Intesa Pillar 3 31-12-2025 EU KM1 row 11 (4.49% explicit for 30-09-2025)",
        is_estimate=False,
    ),
    ("2W8N8UU78PMDQKZENC08", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.0449,
        treatment=CbrTreatment.ON_TOP,
        source="Intesa Pillar 3 31-12-2025 EU KM1 row 11: CBR 4.49% (CCB 2.50 + CCyB 0.31 + SyRB 0.43 + O-SII 1.25); verified 19 May 2026",
        is_estimate=False,
    ),
    # UniCredit — Pillar 3 31-12-2025 p.30 EN: CBR = 4.87% explicit.
    # Treatment INCLUDED inferred: MREL realized 30.59% < 27.05 + 4.87 = 31.92%
    # would breach OCR under ON_TOP assumption (very unlikely for a published
    # filing), so 27.05% must already include CBR. Same logic rolled back to
    # earlier 2025 quarters (treatment stable within fiscal year).
    ("549300TRUWO2CD2G5692", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.0487,
        treatment=CbrTreatment.INCLUDED,
        source="UniCredit Pillar 3 (treatment rolled back from 31-12-2025; CBR 4.87% explicit)",
        is_estimate=True,
    ),
    ("549300TRUWO2CD2G5692", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.0487,
        treatment=CbrTreatment.INCLUDED,
        source="UniCredit Pillar 3 (treatment rolled back from 31-12-2025; CBR 4.87% explicit)",
        is_estimate=True,
    ),
    ("549300TRUWO2CD2G5692", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.0487,
        treatment=CbrTreatment.INCLUDED,
        source="UniCredit Pillar 3 31-12-2025 EN p.30: CBR = 4.87% explicit; treatment INCLUDED inferred by breach-test (capacity 30.59 < req 27.05 + CBR 4.87 = 31.92)",
        is_estimate=False,
    ),
    # Monte dei Paschi — Pillar 3 dicembre 2025 EU KM1 row 11 verified
    # 19 May 2026: CBR = 3.2691% al 31-12-2025 (CCB 2.50 + CCyB 0.0940 +
    # SyRB 0.6751; no O-SII buffer — MPS non è O-SII 2024). Q3 2025 = 3.2743%
    # e Q2 2025 = 3.2791% sono nello stesso KM1, quindi ora tutti esplicit.
    # Treatment INCLUDED rolled forward dal 31-12-2024 footnote esplicito
    # ('(*) Il dato include il CBR pari al 2,89%' = 2.8866% nel KM1).
    # Narrative anche flagga pre-Mediobanca-merger target awaiting recalibration.
    # TREA al 31-12-2025 è 87.71 bn — quasi raddoppiato vs 45.86 bn giu-25
    # per acquisizione Gruppo Mediobanca (OPAS perfezionata settembre 2025).
    ("J4CP7MHCXR8DAQMKIL78", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.032791,
        treatment=CbrTreatment.INCLUDED,
        source="MPS Pillar 3 31-12-2025 EU KM1 row 11 (3.2791% explicit for 30-06-2025)",
        is_estimate=False,
    ),
    ("J4CP7MHCXR8DAQMKIL78", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.032743,
        treatment=CbrTreatment.INCLUDED,
        source="MPS Pillar 3 31-12-2025 EU KM1 row 11 (3.2743% explicit for 30-09-2025)",
        is_estimate=False,
    ),
    ("J4CP7MHCXR8DAQMKIL78", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.032691,
        treatment=CbrTreatment.INCLUDED,
        source="MPS Pillar 3 31-12-2025 EU KM1 row 11: CBR 3.2691% (CCB 2.50 + CCyB 0.0940 + SyRB 0.6751; no O-SII); treatment INCLUDED rolled forward from 31-12-2024 explicit footnote. Verified 19 May 2026 — replaces prior rolled-forward value 3.27% (rounded)",
        is_estimate=False,
    ),
    # MPS Q4 2024 — explicit baseline for the roll-forward.
    ("J4CP7MHCXR8DAQMKIL78", "2024-12-31"): CbrDisclosure(
        cbr_pct_trea=0.0289,
        treatment=CbrTreatment.INCLUDED,
        source="MPS Pillar 3 31-12-2024 p.14 footnote: '(*) Il dato include il Requisito Combinato di Riserva di Capitale (CBR) pari al 2,89% al 31.12.2024'",
        is_estimate=False,
    ),
    # BPER — Pillar 3 31-12-2025 p.14 (KM2) + p.12 (KM1 row 11).
    # CBR = 3.522% (CCB 2.50% + CCyB 0.055% + O-SII 0.250% + SRB 0.717%)
    # from KM1 row 11. Treatment INCLUDED inferred via breach-test:
    # capacity 27.35% < req 25.44% + CBR 3.52% = 28.96%; TLAC1 rows 28-31
    # (CBR breakdown) are blank, consistent with INCLUDED convention (same
    # presentation as MPS). KM2 rows EU-7 = 25.44% TREA, EU-8 = 18.58%.
    ("N747OI7JINV7RUUH6190", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.UNKNOWN,
        source="[default] BPER Pillar 3 not published at Q2 2025 reference date; CBR estimated from Q4 2025 value",
        is_estimate=True,
    ),
    ("N747OI7JINV7RUUH6190", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.UNKNOWN,
        source="[default] BPER Pillar 3 not published at Q3 2025 reference date; CBR estimated from Q4 2025 value",
        is_estimate=True,
    ),
    ("N747OI7JINV7RUUH6190", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.03522,
        treatment=CbrTreatment.INCLUDED,
        source="BPER Pillar 3 31-12-2025 p.12 KM1 row 11: CBR = 3.522% (CCB 2.50 + CCyB 0.055 + O-SII 0.250 + SRB 0.717); treatment INCLUDED inferred by breach-test (capacity 27.35 < req 25.44 + CBR 3.52 = 28.96); TLAC1 rows 28-31 blank consistent with INCLUDED",
        is_estimate=False,
    ),
    # Mediobanca — Pillar 3 dicembre 2025 p.63 + EU KM1 row 11 (verified 19 May
    # 2026 on PDF dec 2025): CBR = 3.4382% al 31-12-2025 (CCB 2.50 + CCyB 0.1499
    # + SyRB 0.7884 + O-SII 0.00). L'O-SII è sceso a zero vs sept 2025 (era
    # 0.25%) per riallocazione/macro-prudential decision dell'autorità. Quindi
    # req_ex_cbr = 24.44 − 3.44 = 21.00% (era erroneamente 20.75% basato sul
    # vecchio CBR 3.69% del Q2 2025). Q2 2025 = 3.6822%, Q3 2025 = 3.7429%.
    ("PSNL19R2RXX5U3QWHI44", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.036822,
        treatment=CbrTreatment.INCLUDED,
        source="Mediobanca Pillar 3 31-12-2025 EU KM1 row 11 (3.6822% explicit for 30-06-2025)",
        is_estimate=False,
    ),
    ("PSNL19R2RXX5U3QWHI44", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.037429,
        treatment=CbrTreatment.INCLUDED,
        source="Mediobanca Pillar 3 31-12-2025 EU KM1 row 11 (3.7429% explicit for 30-09-2025)",
        is_estimate=False,
    ),
    ("PSNL19R2RXX5U3QWHI44", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.034382,
        treatment=CbrTreatment.INCLUDED,
        source="Mediobanca Pillar 3 31-12-2025 EU KM1 row 11: CBR 3.4382% (CCB 2.50 + CCyB 0.1499 + SyRB 0.7884 + O-SII 0.00); verified 19 May 2026 — corrects prior value 3.69% (was Q2 2025 carried forward in error)",
        is_estimate=False,  # CBR value explicit from press release
    ),
    # Iccrea — Pillar 3 explicit: 26.03% INCLUDES CBR of 3.59%.
    ("NNVPP80YIZGEY2314M97", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.0359,
        treatment=CbrTreatment.INCLUDED,
        source="Iccrea Pillar 3 30-06-2025 p.40 ('26,03% comprensivo del CBR 3,59%')",
        is_estimate=False,
    ),
    ("NNVPP80YIZGEY2314M97", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.0359,
        treatment=CbrTreatment.INCLUDED,
        source="Iccrea Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    ("NNVPP80YIZGEY2314M97", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.0359,
        treatment=CbrTreatment.INCLUDED,
        source="Iccrea Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    # Cassa Centrale Banca — Pillar 3 explicit: on_top ("a cui sommare il CBR").
    ("LOO0AWXR8GF142JCO404", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.ON_TOP,
        source="Cassa Centrale Pillar 3 30-06-2025 p.19",
        is_estimate=True,  # treatment explicit; CBR value estimated
    ),
    ("LOO0AWXR8GF142JCO404", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.ON_TOP,
        source="Cassa Centrale Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    ("LOO0AWXR8GF142JCO404", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.ON_TOP,
        source="Cassa Centrale Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    # Credem — Pillar 3 explicit: 19.55% + CBR applicable (on_top).
    ("815600AD83B2B6317788", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.ON_TOP,
        source="Credem Pillar 3 30-06-2025 p.23",
        is_estimate=True,  # treatment explicit; CBR value estimated
    ),
    ("815600AD83B2B6317788", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.ON_TOP,
        source="Credem Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    ("815600AD83B2B6317788", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.ON_TOP,
        source="Credem Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    # Banca Mediolanum — Pillar 3 explicit: 18.22% + CBR 3.16% = 21.38%.
    ("7LVZJ6XRIE7VNZ4UBX81", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.0316,
        treatment=CbrTreatment.ON_TOP,
        source="Mediolanum Pillar 3 30-06-2025 p.35",
        is_estimate=False,
    ),
    ("7LVZJ6XRIE7VNZ4UBX81", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.0316,
        treatment=CbrTreatment.ON_TOP,
        source="Mediolanum Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    ("7LVZJ6XRIE7VNZ4UBX81", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.0316,
        treatment=CbrTreatment.ON_TOP,
        source="Mediolanum Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    # Banca Popolare di Sondrio — Pillar 3 explicit: 22.76% NON inclusivo CBR.
    ("J48C8PCSJVUBR8KCW529", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.ON_TOP,
        source="Sondrio Pillar 3 30-06-2025 p.40",
        is_estimate=True,  # treatment explicit; CBR value estimated
    ),
    ("J48C8PCSJVUBR8KCW529", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.ON_TOP,
        source="Sondrio Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    ("J48C8PCSJVUBR8KCW529", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.ON_TOP,
        source="Sondrio Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    # Mediobanca Premier — shares the Mediobanca Group Pillar 3 source.
    ("815600DDCE9083CAC598", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.INCLUDED,
        source="Mediobanca Group Pillar 3 (used as fallback) p.63",
        is_estimate=True,
    ),
    ("815600DDCE9083CAC598", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.INCLUDED,
        source="Mediobanca Group Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    ("815600DDCE9083CAC598", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.INCLUDED,
        source="Mediobanca Group Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    # BBVA — manual entry note: "MREL requirement includes CBR per BBVA
    # footnote". BBVA is a G-SII, so CBR ~ 2.5 CCB + 1.0 G-SII + CCyB ~0.3.
    ("K8MS7FD7N5Z2WQ51AZ71", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.038,
        treatment=CbrTreatment.INCLUDED,
        source="BBVA Pillar 3 2025 footnote (manual entry)",
        is_estimate=True,  # treatment explicit; CBR value estimated
    ),
    # Same bank, alternate LEI observed in banks.parquet.
    ("U48ZC55EFS0K6YKA1212", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.038,
        treatment=CbrTreatment.INCLUDED,
        source="BBVA Pillar 3 2025 footnote (manual entry)",
        is_estimate=True,
    ),
    # =========================================================================
    # CLUSTER 2 — EU peers of similar size (CdA presentation 2026-05).
    # =========================================================================
    # AIB Group plc (Ireland) — Pillar 3 31-12-2025 p.6 EN explicit:
    # "The current MREL requirement for the Group is the higher of 23.05% of
    # TREA (28.49% including the Combined Buffer Requirement) and..."
    # => req_ex_cbr 23.05%, req_with_cbr 28.49%, CBR = 28.49 - 23.05 = 5.44%.
    # Treatment ON_TOP confirmed: 23.05 + 5.44 = 28.49 exactly.
    ("635400AKJBGNS5WNQL34", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.0544,
        treatment=CbrTreatment.ON_TOP,
        source="AIB Pillar 3 (treatment rolled back from 31-12-2025)",
        is_estimate=True,
    ),
    ("635400AKJBGNS5WNQL34", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.0544,
        treatment=CbrTreatment.ON_TOP,
        source="AIB Pillar 3 31-12-2025 EN p.6: 'MREL = higher of 23.05% TREA (28.49% including CBR) and...' => CBR = 5.44%, ON_TOP",
        is_estimate=False,
    ),
    # Bank of Ireland Group plc (Ireland) — Pillar 3 31-12-2025 not yet
    # published as of 12-May-2026 (BoI publishes semi-annual: H1 2025 + FY 2025
    # expected Mar-Apr 2026). Placeholder uses Q4 2024 disclosure (assumed
    # ON_TOP per Irish convention; CBR value to be confirmed when FY 2025 P3
    # is published — currently 4% estimate consistent with AIB neighbor).
    ("635400C8EK6DRI12LJ39", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.040,
        treatment=CbrTreatment.UNKNOWN,
        source="Bank of Ireland Pillar 3 Q4 2025 pending (expected Mar-Apr 2026; scrape: not_found); default treatment UNKNOWN, CBR estimated as Irish neighbor",
        is_estimate=True,
    ),
    ("635400C8EK6DRI12LJ39", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.040,
        treatment=CbrTreatment.UNKNOWN,
        source="Bank of Ireland Pillar 3 Q4 2025 pending (expected Mar-Apr 2026; scrape: not_found); default treatment UNKNOWN, CBR estimated as Irish neighbor",
        is_estimate=True,
    ),
    # Belfius Bank (Belgium) — Pillar 3 31-12-2025 p.39 EN explicit:
    # "MREL requirement on a consolidated basis is set at 23.68% of TREA ...
    # combined buffer requirement (CBR) ... at 5.23% of TREA for Belfius
    # currently" and "binding target of 28.91% (including the CBR)".
    # 23.68 + 5.23 = 28.91 => ON_TOP confirmed.
    ("A5GWLFH3KM7YV2SFQL84", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.0523,
        treatment=CbrTreatment.ON_TOP,
        source="Belfius Pillar 3 (treatment rolled back from 31-12-2025)",
        is_estimate=True,
    ),
    ("A5GWLFH3KM7YV2SFQL84", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.0523,
        treatment=CbrTreatment.ON_TOP,
        source="Belfius Pillar 3 31-12-2025 EN p.39: 'MREL 23.68% TREA + CBR 5.23% = 28.91% binding target with CBR' => ON_TOP",
        is_estimate=False,
    ),
    # Banco de Sabadell, S.A. (Spain) — Pillar 3 31-12-2025 p.87 EN explicit
    # footnote: "(1) The MREL and subordination requirements expressed in
    # terms of the TREA include the Combined Buffer Requirement (CBR) of
    # 3.50%, as the own funds used by the Institution to meet the CBR are
    # not eligible..." Narrative confirms: "The MREL requirement is 22.14%
    # of TREA" (i.e. req ex CBR = 25.64 - 3.50 = 22.14 ✓).
    ("SI5RG2M0WQQLZCXKRM20", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.0350,
        treatment=CbrTreatment.INCLUDED,
        source="Sabadell Pillar 3 (treatment rolled back from 31-12-2025)",
        is_estimate=True,
    ),
    ("SI5RG2M0WQQLZCXKRM20", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.0350,
        treatment=CbrTreatment.INCLUDED,
        source="Sabadell Pillar 3 31-12-2025 EN p.87 footnote (1): 'requirements include the CBR of 3.50%' (req incl-CBR 25.64% = ex-CBR 22.14% + CBR 3.50%) => INCLUDED",
        is_estimate=False,
    ),
}


# Fallback when a (LEI, date) has no entry: treatment is UNKNOWN so the
# breach-test fallback in `infer_cbr_treatment` can decide between on_top
# (the KM2 default) and included (if capacity < req + cbr would breach).
# CBR value is a conservative placeholder (CCB 2.5% + typical European
# O-SII buffer 1.0% = 3.5%).
DEFAULT_CBR_ESTIMATE: Final[CbrDisclosure] = CbrDisclosure(
    cbr_pct_trea=0.035,
    treatment=CbrTreatment.UNKNOWN,
    source="Default KM2 convention + 3.5% CBR placeholder",
    is_estimate=True,
)


def lookup_cbr(entity_lei: str, reference_date: pd.Timestamp) -> CbrDisclosure:
    """Return the CBR disclosure for one bank on one ref-date, else the default.

    The default uses `CbrTreatment.ON_TOP` because that is the KM2 filing
    convention (per the BPM footnote citation above); a 3.5% placeholder
    CBR value is flagged `is_estimate=True` so the UI can caveat it.
    """
    key = (str(entity_lei), pd.Timestamp(reference_date).date().isoformat())
    return CBR_DISCLOSURES.get(key, DEFAULT_CBR_ESTIMATE)


def infer_cbr_treatment(
    capacity_pct_trea: float | None,
    requirement_pct_trea: float | None,
    cbr_pct_trea: float | None,
    declared_treatment: CbrTreatment,
) -> CbrTreatment:
    """Apply the breach-test fallback rule when treatment is unknown.

    Rule (per user decision):
    1. If treatment is already known (ON_TOP or INCLUDED), return it as-is.
    2. If treatment is UNKNOWN:
       - Assume ON_TOP by default (the KM2 filing convention).
       - If any input is None, keep the default.
       - Otherwise, check `capacity < requirement + cbr`. If that holds,
         the bank would be in breach under the ON_TOP assumption, which is
         very unlikely for a published disclosure. Reclassify as INCLUDED.
    """
    if declared_treatment is not CbrTreatment.UNKNOWN:
        return declared_treatment
    if (
        capacity_pct_trea is None
        or requirement_pct_trea is None
        or cbr_pct_trea is None
        or pd.isna(capacity_pct_trea)
        or pd.isna(requirement_pct_trea)
        or pd.isna(cbr_pct_trea)
    ):
        return CbrTreatment.ON_TOP
    if capacity_pct_trea < requirement_pct_trea + cbr_pct_trea:
        return CbrTreatment.INCLUDED
    return CbrTreatment.ON_TOP


def normalize_requirement(
    requirement_pct_trea: float | None,
    cbr_pct_trea: float | None,
    treatment: CbrTreatment,
) -> tuple[float | None, float | None]:
    """Return (req_ex_cbr, req_with_cbr) on a consistent 'excludes CBR' base.

    ``req_ex_cbr`` is the MREL-TREA requirement stripped of CBR (what BPM's
    KM2 r0120 shows natively). ``req_with_cbr`` is req_ex_cbr + CBR — the
    OCR-equivalent threshold below which M-MDA restrictions trigger.

    If the bank discloses its req **including CBR** (``INCLUDED``), we
    subtract the CBR to obtain req_ex_cbr; ``req_with_cbr`` is then just
    the originally-disclosed value.
    """
    if requirement_pct_trea is None or pd.isna(requirement_pct_trea):
        return None, None
    if cbr_pct_trea is None or pd.isna(cbr_pct_trea):
        # Without a CBR value we cannot translate between bases.
        if treatment is CbrTreatment.INCLUDED:
            return None, float(requirement_pct_trea)
        return float(requirement_pct_trea), None
    req = float(requirement_pct_trea)
    cbr = float(cbr_pct_trea)
    if treatment is CbrTreatment.INCLUDED:
        return req - cbr, req
    # ON_TOP or defaulted ON_TOP
    return req, req + cbr


def attach_cbr(wide: pd.DataFrame) -> pd.DataFrame:
    """Attach CBR columns + normalized requirement bases to a km2_wide frame.

    Adds, for each (bank, ref-date) row:
    - `cbr_pct_trea` — CBR value (from lookup)
    - `cbr_treatment` — 'on_top' / 'included' / 'unknown_defaulted'
    - `cbr_is_estimate` — True if CBR value is a placeholder
    - `cbr_source` — free-text citation
    - `mrel_requirement_trea_ex_cbr` — total-MREL requirement on EX-CBR base
    - `mrel_requirement_trea_with_cbr` — total-MREL requirement + CBR (OCR)
    - `mrel_surplus_trea_ex_cbr_pp` — capacity - req_ex_cbr (cushion vs MREL)
    - `mrel_surplus_trea_with_cbr_pp` — capacity - req_with_cbr (cushion vs OCR)
    - `mrel_subord_requirement_trea_ex_cbr` — subordination req on EX-CBR base
    - `mrel_subord_requirement_trea_with_cbr` — subordination req + CBR
    - `subord_surplus_trea_ex_cbr_pp` — subord_pct - subord_req_ex_cbr
    - `subord_surplus_trea_with_cbr_pp` — subord_pct - subord_req_with_cbr

    The subordination requirement follows the same CBR treatment as the
    total-MREL requirement for the same bank (both figures come from the
    same KM2 template and the bank's disclosed CBR convention applies to
    both rows 0120 and 0130 uniformly).
    """
    if wide.empty:
        for col in (
            "cbr_pct_trea", "cbr_treatment", "cbr_is_estimate", "cbr_source",
            "mrel_requirement_trea_ex_cbr", "mrel_requirement_trea_with_cbr",
            "mrel_surplus_trea_ex_cbr_pp", "mrel_surplus_trea_with_cbr_pp",
            "mrel_subord_requirement_trea_ex_cbr",
            "mrel_subord_requirement_trea_with_cbr",
            "subord_surplus_trea_ex_cbr_pp",
            "subord_surplus_trea_with_cbr_pp",
        ):
            wide[col] = pd.Series(dtype="object" if col.endswith(("treatment", "source")) else "Float64")
        return wide

    out = wide.copy()
    records = []
    for _, row in out.iterrows():
        disc = lookup_cbr(row["entity_lei"], row["reference_date"])
        # First, apply user's breach-test rule in case declared treatment is UNKNOWN.
        effective_treatment = infer_cbr_treatment(
            capacity_pct_trea=row.get("mrel_pct_trea"),
            requirement_pct_trea=row.get("mrel_requirement_trea"),
            cbr_pct_trea=disc.cbr_pct_trea,
            declared_treatment=disc.treatment,
        )
        req_ex_cbr, req_with_cbr = normalize_requirement(
            row.get("mrel_requirement_trea"),
            disc.cbr_pct_trea,
            effective_treatment,
        )
        subord_req_ex_cbr, subord_req_with_cbr = normalize_requirement(
            row.get("mrel_subord_requirement_trea"),
            disc.cbr_pct_trea,
            effective_treatment,
        )
        capacity = row.get("mrel_pct_trea")
        subord_capacity = row.get("subord_pct_trea")
        surplus_ex = (capacity - req_ex_cbr) if (
            capacity is not None and req_ex_cbr is not None
            and not pd.isna(capacity) and not pd.isna(req_ex_cbr)
        ) else None
        surplus_with = (capacity - req_with_cbr) if (
            capacity is not None and req_with_cbr is not None
            and not pd.isna(capacity) and not pd.isna(req_with_cbr)
        ) else None
        subord_surplus_ex = (subord_capacity - subord_req_ex_cbr) if (
            subord_capacity is not None and subord_req_ex_cbr is not None
            and not pd.isna(subord_capacity) and not pd.isna(subord_req_ex_cbr)
        ) else None
        subord_surplus_with = (subord_capacity - subord_req_with_cbr) if (
            subord_capacity is not None and subord_req_with_cbr is not None
            and not pd.isna(subord_capacity) and not pd.isna(subord_req_with_cbr)
        ) else None
        records.append({
            "cbr_pct_trea": disc.cbr_pct_trea,
            "cbr_treatment": effective_treatment.value,
            "cbr_is_estimate": disc.is_estimate,
            "cbr_source": disc.source,
            "mrel_requirement_trea_ex_cbr": req_ex_cbr,
            "mrel_requirement_trea_with_cbr": req_with_cbr,
            "mrel_surplus_trea_ex_cbr_pp": surplus_ex,
            "mrel_surplus_trea_with_cbr_pp": surplus_with,
            "mrel_subord_requirement_trea_ex_cbr": subord_req_ex_cbr,
            "mrel_subord_requirement_trea_with_cbr": subord_req_with_cbr,
            "subord_surplus_trea_ex_cbr_pp": subord_surplus_ex,
            "subord_surplus_trea_with_cbr_pp": subord_surplus_with,
        })
    attached = pd.DataFrame(records, index=out.index)
    return pd.concat([out, attached], axis=1)
