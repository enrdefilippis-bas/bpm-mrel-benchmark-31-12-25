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
        cbr_pct_trea=0.0360,  # slight CCyB uptick assumed
        treatment=CbrTreatment.ON_TOP,
        source="BPM Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    # Intesa Sanpaolo — Pillar 3 explicit: 21.00% TREA + CBR 4.48% = 25.48%.
    ("2W8N8UU78PMDQKZENC08", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.0448,
        treatment=CbrTreatment.ON_TOP,
        source="Intesa Pillar 3 30-06-2025 p.37",
        is_estimate=False,
    ),
    ("2W8N8UU78PMDQKZENC08", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.0448,
        treatment=CbrTreatment.ON_TOP,
        source="Intesa Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    ("2W8N8UU78PMDQKZENC08", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.0448,
        treatment=CbrTreatment.ON_TOP,
        source="Intesa Pillar 3 (treatment rolled forward)",
        is_estimate=True,
    ),
    # UniCredit — treatment not explicit in scraped Q2-2025 text ("not_found").
    # UNKNOWN so the breach-test rule can drive the decision. CBR estimate:
    # 2.5 CCB + 1.00 O-SII + G-SII 1.00% (UniCredit is a G-SII from 2024)
    # + CCyB ~0.50.
    ("549300TRUWO2CD2G5692", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.050,
        treatment=CbrTreatment.UNKNOWN,
        source="Default (scrape: not_found); treatment inferred by breach-test; CBR estimated",
        is_estimate=True,
    ),
    ("549300TRUWO2CD2G5692", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.050,
        treatment=CbrTreatment.UNKNOWN,
        source="Default (scrape: not_found); treatment inferred by breach-test; CBR estimated",
        is_estimate=True,
    ),
    ("549300TRUWO2CD2G5692", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.050,
        treatment=CbrTreatment.UNKNOWN,
        source="Default (scrape: not_found); treatment inferred by breach-test; CBR estimated",
        is_estimate=True,
    ),
    # Monte dei Paschi — not_found in scrape. UNKNOWN so breach-test drives
    # the decision; CBR estimate 2.5 CCB + 0.50 O-SII + ~0.30 CCyB = 3.3%.
    ("J4CP7MHCXR8DAQMKIL78", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.033,
        treatment=CbrTreatment.UNKNOWN,
        source="Default (scrape: not_found); treatment inferred by breach-test; CBR estimated",
        is_estimate=True,
    ),
    ("J4CP7MHCXR8DAQMKIL78", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.033,
        treatment=CbrTreatment.UNKNOWN,
        source="Default (scrape: not_found); treatment inferred by breach-test; CBR estimated",
        is_estimate=True,
    ),
    ("J4CP7MHCXR8DAQMKIL78", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.033,
        treatment=CbrTreatment.UNKNOWN,
        source="Default (scrape: not_found); treatment inferred by breach-test; CBR estimated",
        is_estimate=True,
    ),
    # BPER — not_found in scrape. UNKNOWN; CBR estimate ~3.0%.
    ("N747OI7JINV7RUUH6190", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.UNKNOWN,
        source="Default (scrape: not_found); treatment inferred by breach-test; CBR estimated",
        is_estimate=True,
    ),
    ("N747OI7JINV7RUUH6190", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.UNKNOWN,
        source="Default (scrape: not_found); treatment inferred by breach-test; CBR estimated",
        is_estimate=True,
    ),
    ("N747OI7JINV7RUUH6190", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.030,
        treatment=CbrTreatment.UNKNOWN,
        source="Default (scrape: not_found); treatment inferred by breach-test; CBR estimated",
        is_estimate=True,
    ),
    # Mediobanca — Pillar 3 dicembre 2025 p.63 explicit: "MREL-TREA: 24,44%
    # (incl. CBR)". CBR components per Mediobanca press release (ECB 2025
    # capital requirement): CCB 2.5% + O-SII 0.25% + SyRB 0.8% + CCyB 0.14%
    # = 3.69%. So req_ex_cbr = 24.44 − 3.69 = 20.75%.
    ("PSNL19R2RXX5U3QWHI44", "2025-06-30"): CbrDisclosure(
        cbr_pct_trea=0.0369,
        treatment=CbrTreatment.INCLUDED,
        source="Mediobanca Pillar 3 30-06-2025 (treatment); press release 2025 (CBR components — roll-back)",
        is_estimate=True,  # CBR value rolled back from Q4 2025
    ),
    ("PSNL19R2RXX5U3QWHI44", "2025-09-30"): CbrDisclosure(
        cbr_pct_trea=0.0369,
        treatment=CbrTreatment.INCLUDED,
        source="Mediobanca Pillar 3 (treatment rolled forward); press release 2025 (CBR components)",
        is_estimate=True,
    ),
    ("PSNL19R2RXX5U3QWHI44", "2025-12-31"): CbrDisclosure(
        cbr_pct_trea=0.0369,
        treatment=CbrTreatment.INCLUDED,
        source="Mediobanca Pillar 3 31-12-2025 p.63 ('24,44% incl. CBR') + press release 2025 (CCB 2.5 + O-SII 0.25 + SyRB 0.8 + CCyB 0.14)",
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
    - `mrel_requirement_trea_ex_cbr` — requirement on a comparable EX-CBR base
    - `mrel_requirement_trea_with_cbr` — requirement + CBR (the M-MDA threshold)
    - `mrel_surplus_trea_ex_cbr_pp` — capacity - req_ex_cbr  (cushion vs MREL)
    - `mrel_surplus_trea_with_cbr_pp` — capacity - req_with_cbr (cushion vs OCR)
    """
    if wide.empty:
        for col in (
            "cbr_pct_trea", "cbr_treatment", "cbr_is_estimate", "cbr_source",
            "mrel_requirement_trea_ex_cbr", "mrel_requirement_trea_with_cbr",
            "mrel_surplus_trea_ex_cbr_pp", "mrel_surplus_trea_with_cbr_pp",
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
        capacity = row.get("mrel_pct_trea")
        surplus_ex = (capacity - req_ex_cbr) if (
            capacity is not None and req_ex_cbr is not None
            and not pd.isna(capacity) and not pd.isna(req_ex_cbr)
        ) else None
        surplus_with = (capacity - req_with_cbr) if (
            capacity is not None and req_with_cbr is not None
            and not pd.isna(capacity) and not pd.isna(req_with_cbr)
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
        })
    attached = pd.DataFrame(records, index=out.index)
    return pd.concat([out, attached], axis=1)
