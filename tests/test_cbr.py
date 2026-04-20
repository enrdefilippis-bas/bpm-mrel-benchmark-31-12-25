"""Tests for the CBR lookup + MREL requirement normalization logic."""
from __future__ import annotations

import pandas as pd
import pytest

from core.cbr import (
    CBR_DISCLOSURES,
    DEFAULT_CBR_ESTIMATE,
    CbrTreatment,
    attach_cbr,
    infer_cbr_treatment,
    lookup_cbr,
    normalize_requirement,
)
from core.metrics import km2_wide
from core.schema import Source, Template, UnitType


# -----------------------------------------------------------------------------
# lookup_cbr — explicit hits + fallback to default
# -----------------------------------------------------------------------------


def test_lookup_cbr_returns_explicit_bpm_disclosure():
    """Banco BPM at 2025-06-30 should come back as ON_TOP with the KM2 footnote citation."""
    disc = lookup_cbr("815600E4E6DCD2D25E30", pd.Timestamp("2025-06-30"))
    assert disc.treatment is CbrTreatment.ON_TOP
    assert "BPM" in disc.source
    assert disc.cbr_pct_trea is not None


def test_lookup_cbr_returns_included_for_iccrea():
    disc = lookup_cbr("NNVPP80YIZGEY2314M97", pd.Timestamp("2025-06-30"))
    assert disc.treatment is CbrTreatment.INCLUDED
    assert disc.cbr_pct_trea == pytest.approx(0.0359)
    assert disc.is_estimate is False  # explicit quote


def test_lookup_cbr_returns_default_for_unknown_bank():
    """A random LEI we don't have evidence for falls back to the default.

    The default's treatment is UNKNOWN so the breach-test rule can drive
    the decision downstream; if there's no breach, it resolves to ON_TOP.
    """
    disc = lookup_cbr("XXXX_UNKNOWN_LEI_XXXX", pd.Timestamp("2025-12-31"))
    assert disc.treatment is CbrTreatment.UNKNOWN
    assert disc.is_estimate is True
    assert disc == DEFAULT_CBR_ESTIMATE


# -----------------------------------------------------------------------------
# normalize_requirement — ex-CBR vs with-CBR bases
# -----------------------------------------------------------------------------


def test_normalize_requirement_on_top_adds_cbr():
    """ON_TOP bank: stored req IS ex-CBR; req_with_cbr = req + CBR."""
    ex, with_ = normalize_requirement(0.21, 0.0448, CbrTreatment.ON_TOP)
    assert ex == pytest.approx(0.21)
    assert with_ == pytest.approx(0.21 + 0.0448)


def test_normalize_requirement_included_subtracts_cbr():
    """INCLUDED bank: stored req already HAS CBR; req_ex_cbr = req - CBR."""
    # Iccrea-style: 26.03% includes 3.59% CBR -> ex-CBR = 22.44%
    ex, with_ = normalize_requirement(0.2603, 0.0359, CbrTreatment.INCLUDED)
    assert ex == pytest.approx(0.2244)
    assert with_ == pytest.approx(0.2603)


def test_normalize_requirement_handles_missing_cbr():
    """If CBR unknown, we can still populate one side depending on treatment."""
    ex, with_ = normalize_requirement(0.21, None, CbrTreatment.ON_TOP)
    assert ex == pytest.approx(0.21)
    assert with_ is None
    ex, with_ = normalize_requirement(0.26, None, CbrTreatment.INCLUDED)
    assert ex is None
    assert with_ == pytest.approx(0.26)


def test_normalize_requirement_handles_missing_requirement():
    ex, with_ = normalize_requirement(None, 0.04, CbrTreatment.ON_TOP)
    assert ex is None and with_ is None


# -----------------------------------------------------------------------------
# infer_cbr_treatment — the breach-test fallback rule
# -----------------------------------------------------------------------------


def test_infer_cbr_treatment_respects_explicit_classification():
    """If treatment is already known, the rule is a no-op."""
    assert (
        infer_cbr_treatment(0.34, 0.22, 0.04, CbrTreatment.ON_TOP)
        is CbrTreatment.ON_TOP
    )
    assert (
        infer_cbr_treatment(0.28, 0.27, 0.04, CbrTreatment.INCLUDED)
        is CbrTreatment.INCLUDED
    )


def test_infer_cbr_treatment_defaults_to_on_top_when_not_breach():
    """UNKNOWN treatment, capacity > req + CBR -> treat as ON_TOP (KM2 default)."""
    # BPM-like: 34.02% cap vs 22.6% req + 3.5% CBR = 26.1% OCR -> cushion ~8pp
    assert (
        infer_cbr_treatment(0.3402, 0.226, 0.035, CbrTreatment.UNKNOWN)
        is CbrTreatment.ON_TOP
    )


def test_infer_cbr_treatment_flips_to_included_on_breach():
    """UNKNOWN, capacity < req + CBR -> reclassify as INCLUDED per user rule."""
    # e.g. bank disclosed 28% req, 27.5% capacity, 3% CBR -> 27.5 < 28+3=31 -> breach
    # so the 28% must already include CBR (ex-CBR ~ 25%).
    assert (
        infer_cbr_treatment(0.275, 0.28, 0.03, CbrTreatment.UNKNOWN)
        is CbrTreatment.INCLUDED
    )


def test_infer_cbr_treatment_with_missing_inputs_stays_default():
    """If any input is None, we cannot run the test — stay with ON_TOP default."""
    assert (
        infer_cbr_treatment(None, 0.22, 0.035, CbrTreatment.UNKNOWN)
        is CbrTreatment.ON_TOP
    )
    assert (
        infer_cbr_treatment(0.34, None, 0.035, CbrTreatment.UNKNOWN)
        is CbrTreatment.ON_TOP
    )


# -----------------------------------------------------------------------------
# attach_cbr — end-to-end integration with km2_wide
# -----------------------------------------------------------------------------


def _fact(lei: str, template: str, row: str, col: str, value: float,
          date: str, unit: str) -> dict:
    return {
        "entity_lei": lei,
        "entity_name": f"bank-{lei}",
        "country": "Italy",
        "reference_date": pd.Timestamp(date),
        "template": template,
        "row_code": row,
        "row_name": "",
        "col_code": col,
        "col_name": "",
        "open_key": "",
        "raw_value": value,
        "value": value,
        "unit": unit,
        "source": Source.EBA_EXPORT.value,
        "ingested_at": pd.Timestamp.now("UTC").tz_localize(None),
    }


def test_attach_cbr_produces_both_surplus_columns_for_bpm_synth():
    """BPM-shaped data: ON_TOP, cushion vs OCR should be positive."""
    rows = [
        # Banco BPM LEI
        _fact("815600E4E6DCD2D25E30", Template.KM2.value,
              "0040", "0010", 0.3402, "2025-06-30", UnitType.RATIO.value),
        _fact("815600E4E6DCD2D25E30", Template.KM2.value,
              "0120", "0010", 0.226, "2025-06-30", UnitType.RATIO.value),
    ]
    wide = km2_wide(pd.DataFrame(rows))
    assert len(wide) == 1
    r = wide.iloc[0]
    assert r["cbr_treatment"] == "on_top"
    # req_ex_cbr = 22.6%; req_with_cbr = 22.6 + CBR (~3.55%)
    assert r["mrel_requirement_trea_ex_cbr"] == pytest.approx(0.226, abs=1e-5)
    assert r["mrel_requirement_trea_with_cbr"] > r["mrel_requirement_trea_ex_cbr"]
    # Capacity 34.02% handily beats both thresholds
    assert r["mrel_surplus_trea_ex_cbr_pp"] > 0
    assert r["mrel_surplus_trea_with_cbr_pp"] > 0


def test_attach_cbr_iccrea_strips_cbr_to_get_ex_cbr_base():
    """Iccrea: 26.03% INCLUDES 3.59% CBR -> ex-CBR = 22.44%, with-CBR = 26.03%."""
    rows = [
        _fact("NNVPP80YIZGEY2314M97", Template.KM2.value,
              "0040", "0010", 0.30, "2025-06-30", UnitType.RATIO.value),
        _fact("NNVPP80YIZGEY2314M97", Template.KM2.value,
              "0120", "0010", 0.2603, "2025-06-30", UnitType.RATIO.value),
    ]
    wide = km2_wide(pd.DataFrame(rows))
    r = wide.iloc[0]
    assert r["cbr_treatment"] == "included"
    assert r["cbr_pct_trea"] == pytest.approx(0.0359)
    assert r["mrel_requirement_trea_ex_cbr"] == pytest.approx(0.2244)
    assert r["mrel_requirement_trea_with_cbr"] == pytest.approx(0.2603)


def test_attach_cbr_uses_inference_for_unknown_bank():
    """Unknown LEI with capacity < req + default_cbr -> flipped to INCLUDED."""
    # Capacity 25%, req 24% — default CBR 3.5% -> 25 < 24+3.5=27.5 -> breach
    # under ON_TOP -> reclassified as INCLUDED.
    rows = [
        _fact("MYSTERY_BANK_LEI", Template.KM2.value,
              "0040", "0010", 0.25, "2025-06-30", UnitType.RATIO.value),
        _fact("MYSTERY_BANK_LEI", Template.KM2.value,
              "0120", "0010", 0.24, "2025-06-30", UnitType.RATIO.value),
    ]
    wide = km2_wide(pd.DataFrame(rows))
    r = wide.iloc[0]
    assert r["cbr_treatment"] == "included"
    # ex-CBR = 24% - 3.5% = 20.5%
    assert r["mrel_requirement_trea_ex_cbr"] == pytest.approx(0.205)


def test_disclosure_table_is_internally_consistent():
    """Every entry in the lookup table should have a non-None CBR value and a source string.

    UNKNOWN treatment is allowed ONLY for entries whose source string marks
    them as defaults (i.e. the scrape returned `not_found` for the bank).
    All other entries must declare either ON_TOP or INCLUDED explicitly.
    """
    for key, disc in CBR_DISCLOSURES.items():
        lei, date_iso = key
        assert lei, f"empty LEI in disclosure key {key}"
        pd.Timestamp(date_iso)  # must parse
        assert disc.cbr_pct_trea is not None, f"{key} has no CBR value"
        assert 0.0 <= disc.cbr_pct_trea <= 0.15, f"{key} CBR looks implausible: {disc.cbr_pct_trea}"
        assert disc.source, f"{key} has empty source"
        if disc.treatment is CbrTreatment.UNKNOWN:
            assert "default" in disc.source.lower() or "not_found" in disc.source.lower(), (
                f"{key} is UNKNOWN but source does not mark it as a default"
            )
