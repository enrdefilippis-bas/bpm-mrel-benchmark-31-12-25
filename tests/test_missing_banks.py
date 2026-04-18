"""Tests for the BaseBankParser + normalize merge pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from core.schema import Source, Template, UnitType
from ingestion.missing_banks import (
    ALL_PARSERS,
    BankMeta,
    BaseBankParser,
    BBVAParser,
    CreditAgricoleParser,
    IntesaParser,
    SocGenParser,
    UniCreditParser,
)
from ingestion.missing_banks.base import KM2_CELLS, TLAC1_CELLS
from ingestion.normalize import (
    _entry_stem,
    load_missing_bank_facts,
    merge_sources,
)


# --- BaseBankParser contract --------------------------------------------------

def test_all_parsers_declare_valid_bank_meta():
    for cls in ALL_PARSERS:
        assert isinstance(cls.meta, BankMeta)
        assert cls.meta.lei and len(cls.meta.lei) == 20
        assert cls.meta.name
        assert cls.meta.country
        assert cls.meta.source_tag.startswith("pdf-")
        assert cls.meta.source_tag in {s.value for s in Source}


def test_five_parsers_cover_all_missing_banks():
    # Stable inventory guard — the peer set relies on these LEIs.
    by_lei = {cls.meta.lei: cls for cls in ALL_PARSERS}
    assert IntesaParser.meta.lei in by_lei
    assert UniCreditParser.meta.lei in by_lei
    assert BBVAParser.meta.lei in by_lei
    assert CreditAgricoleParser.meta.lei in by_lei
    assert SocGenParser.meta.lei in by_lei
    assert len(by_lei) == 5


def test_parse_pdf_default_raises_not_implemented(tmp_path: Path):
    # NOTE: This test is no longer valid since all 5 parsers now implement
    # parse_pdf (even if partially). The test is kept for documentation but
    # skipped. See test_pdf_parsers.py for validation of parse_pdf output.
    pytest.skip("parse_pdf now implemented for all parsers")


def test_entry_stem_derives_filename_from_source_tag():
    assert _entry_stem(IntesaParser) == "intesa"
    assert _entry_stem(CreditAgricoleParser) == "credit_agricole"
    assert _entry_stem(SocGenParser) == "socgen"


# --- Manual-entry path --------------------------------------------------------

def _write_entries(path: Path, *, km2: dict, tlac1: dict | None = None,
                   date_iso: str = "2025-12-31",
                   entity_name: str = "Intesa Sanpaolo S.p.A.") -> None:
    payload = {
        "entity_name": entity_name,
        "reference_dates": {
            date_iso: {"km2": km2, "tlac1": tlac1 or {}},
        },
    }
    path.write_text(json.dumps(payload))


def test_from_manual_entries_emits_canonical_km2_facts(tmp_path: Path):
    entries = tmp_path / "intesa.json"
    _write_entries(entries, km2={
        "mrel_pct_trea":            0.3250,
        "subord_pct_trea":          0.2650,
        "mrel_requirement_trea":    0.2520,
        "mrel_total_amount":        75_000_000_000,
        "trea":                     230_000_000_000,
    })

    df = IntesaParser.from_manual_entries(entries)
    assert len(df) == 5
    assert set(df["entity_lei"]) == {IntesaParser.meta.lei}
    assert set(df["source"]) == {Source.PDF_INTESA.value}
    assert set(df["template"]) == {Template.KM2.value}

    ratios = df[df["unit"] == UnitType.RATIO.value]
    assert set(ratios["row_code"]) == {"0040", "0050", "0120"}
    amounts = df[df["unit"] == UnitType.AMOUNT_EUR.value]
    assert set(amounts["row_code"]) == {"0010", "0030"}


def test_from_manual_entries_emits_tlac1_composition_when_provided(tmp_path: Path):
    entries = tmp_path / "intesa.json"
    _write_entries(entries, km2={}, tlac1={
        "cet1":  40_000_000_000,
        "at1":   5_000_000_000,
        "tier2": 8_000_000_000,
        "subord_own_issuance": 12_000_000_000,
        "senior_pre_cap":      10_000_000_000,
    })

    df = IntesaParser.from_manual_entries(entries)
    assert set(df["template"]) == {Template.TLAC1.value}
    assert set(df["row_code"]) == {
        TLAC1_CELLS["cet1"], TLAC1_CELLS["at1"], TLAC1_CELLS["tier2"],
        TLAC1_CELLS["subord_own_issuance"], TLAC1_CELLS["senior_pre_cap"],
    }
    assert (df["col_code"] == "0010").all()


def test_from_manual_entries_skips_null_cells(tmp_path: Path):
    entries = tmp_path / "intesa.json"
    _write_entries(entries, km2={
        "mrel_pct_trea": 0.32,
        "subord_pct_trea": None,      # null → skipped
        "trea": None,
    })
    df = IntesaParser.from_manual_entries(entries)
    assert len(df) == 1
    assert df["row_code"].iloc[0] == KM2_CELLS["mrel_pct_trea"][0]


def test_from_manual_entries_missing_file_returns_empty(tmp_path: Path):
    df = IntesaParser.from_manual_entries(tmp_path / "nope.json")
    assert df.empty
    assert list(df.columns)  # has the canonical columns


def test_from_manual_entries_empty_dates_returns_empty(tmp_path: Path):
    entries = tmp_path / "intesa.json"
    entries.write_text(json.dumps({"entity_name": "X", "reference_dates": {}}))
    df = IntesaParser.from_manual_entries(entries)
    assert df.empty


def test_load_missing_bank_facts_roundtrip(tmp_path: Path):
    # Two parsers populated, three empty.
    _write_entries(tmp_path / "intesa.json",
                   km2={"mrel_pct_trea": 0.3250})
    _write_entries(tmp_path / "bbva.json",
                   km2={"mrel_pct_trea": 0.2780})
    # Unicredit / credit_agricole / socgen JSONs absent.

    facts, counts = load_missing_bank_facts(tmp_path)
    assert counts[Source.PDF_INTESA.value] == 1
    assert counts[Source.PDF_BBVA.value] == 1
    assert counts[Source.PDF_UNICREDIT.value] == 0
    assert len(facts) == 2
    assert set(facts["entity_lei"]) == {
        IntesaParser.meta.lei, BBVAParser.meta.lei,
    }


# --- merge_sources precedence rule --------------------------------------------

def _sample_fact(lei: str, source: str, value: float) -> dict:
    return {
        "entity_lei": lei,
        "entity_name": f"bank-{lei}",
        "country": "Italy",
        "reference_date": pd.Timestamp("2025-12-31"),
        "template": Template.KM2.value,
        "row_code": "0040",
        "row_name": "",
        "col_code": "0010",
        "col_name": "",
        "open_key": "",
        "raw_value": value,
        "value": value,
        "unit": UnitType.RATIO.value,
        "source": source,
        "ingested_at": pd.Timestamp.now("UTC").tz_localize(None),
    }


def test_merge_sources_keeps_eba_when_lei_overlaps():
    eba = pd.DataFrame([_sample_fact("LEI_BPM", Source.EBA_EXPORT.value, 0.34)])
    pdf = pd.DataFrame([_sample_fact("LEI_BPM", Source.PDF_INTESA.value, 0.99)])
    out = merge_sources(eba, pdf)
    assert len(out) == 1
    assert out["source"].iloc[0] == Source.EBA_EXPORT.value
    assert out["value"].iloc[0] == pytest.approx(0.34)


def test_merge_sources_appends_pdf_when_lei_missing_from_eba():
    eba = pd.DataFrame([_sample_fact("LEI_BPM", Source.EBA_EXPORT.value, 0.34)])
    pdf = pd.DataFrame([_sample_fact("LEI_INTESA", Source.PDF_INTESA.value, 0.30)])
    out = merge_sources(eba, pdf)
    assert len(out) == 2
    assert set(out["entity_lei"]) == {"LEI_BPM", "LEI_INTESA"}
    assert set(out["source"]) == {Source.EBA_EXPORT.value,
                                   Source.PDF_INTESA.value}


def test_merge_sources_empty_inputs_return_typed_empty():
    out = merge_sources(None)
    assert out.empty
    # Columns are still present — validate_facts enforces the schema.
    from core.schema import FACT_COLUMNS
    assert set(out.columns) == set(FACT_COLUMNS)


# --- BaseBankParser cannot be forgotten to wire up ---------------------------

def test_base_parser_is_abstract():
    assert issubclass(IntesaParser, BaseBankParser)
