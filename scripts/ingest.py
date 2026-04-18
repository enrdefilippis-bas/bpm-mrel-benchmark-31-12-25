"""End-to-end ingestion: EBA export (+ PDF parsers in later phases) → parquet."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make the project root importable when the script is run directly.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.peers import (
    BPM_LEI,
    DEFAULT_BPM_PEERS,
    ITALIAN_OSII_RESOLUTION,
    EU_OSII_SIMILAR_SIZE,
    resolve_peer_set,
)
from core.schema import validate_facts
from ingestion.bank_dimension import build_bank_dimension
from ingestion.eba_export import parse_eba_export
from ingestion.normalize import load_missing_bank_facts, merge_sources
from ingestion.p3_datahub import parse_p3_datahub


DEFAULT_EXPORT = ROOT / "data" / "raw" / "p3mreldata_2025q4.xlsx"
DEFAULT_DATAHUB = ROOT / "p3datahuball copia.xlsx"
DEFAULT_ENTRIES = ROOT / "data" / "manual_entries"
DEFAULT_PDFS = ROOT / "data" / "raw" / "pdfs"
PROCESSED = ROOT / "data" / "processed"


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest MREL data sources.")
    parser.add_argument(
        "--eba-export",
        type=Path,
        default=DEFAULT_EXPORT,
        help="Path to the EBA Pillar 3 MREL/TLAC cell-level export (xlsx).",
    )
    parser.add_argument(
        "--datahub",
        type=Path,
        default=DEFAULT_DATAHUB,
        help="Path to the P3 datahub export (xlsx). Set to None to skip.",
    )
    parser.add_argument(
        "--manual-entries",
        type=Path,
        default=DEFAULT_ENTRIES,
        help="Directory of per-bank manual-entry JSONs (fallback when PDF parse fails).",
    )
    parser.add_argument(
        "--pdfs-dir",
        type=Path,
        default=DEFAULT_PDFS,
        help="Directory of per-bank Pillar 3 PDFs. Parsers run here first; JSONs are the fallback.",
    )
    parser.add_argument(
        "--no-pdfs",
        action="store_true",
        help="Skip PDF parsing; use manual-entry JSONs only (legacy behavior).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=PROCESSED,
        help="Directory where facts.parquet, banks.parquet and ingest_log.json are written.",
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    eba_facts = parse_eba_export(args.eba_export)
    validate_facts(eba_facts)

    missing_facts, missing_counts = load_missing_bank_facts(
        args.manual_entries,
        pdfs_dir=None if args.no_pdfs else args.pdfs_dir,
    )

    # Load datahub facts if available
    datahub_counts = {}
    datahub_facts = None
    if args.datahub and Path(args.datahub).exists():
        try:
            datahub_facts = parse_p3_datahub(args.datahub)
            datahub_counts["p3-datahub"] = int(len(datahub_facts))
            print(f"Loaded {len(datahub_facts):,} facts from datahub")
        except Exception as e:
            print(f"Warning: Failed to parse datahub ({e}); continuing without it")
            datahub_facts = None

    # Merge sources with precedence: EBA > missing_banks > datahub
    if datahub_facts is not None:
        facts = merge_sources(eba_facts, missing_facts, datahub_facts)
    else:
        facts = merge_sources(eba_facts, missing_facts)

    facts_path = args.out_dir / "facts.parquet"
    facts.to_parquet(facts_path, index=False)

    banks = build_bank_dimension(facts)
    banks_path = args.out_dir / "banks.parquet"
    banks.to_parquet(banks_path, index=False)

    bpm_peer_leis = resolve_peer_set(DEFAULT_BPM_PEERS, banks)
    italian_osii_leis = resolve_peer_set(ITALIAN_OSII_RESOLUTION, banks)
    eu_similar_leis = resolve_peer_set(EU_OSII_SIMILAR_SIZE, banks, facts=facts)

    has_bpm = BPM_LEI in set(banks["entity_lei"])
    present_by_source = (
        facts.groupby("source")["entity_lei"].nunique().to_dict()
    )
    ref_dates = sorted(d.isoformat() for d in facts["reference_date"].dt.date.unique())

    log = {
        "facts_rows": int(len(facts)),
        "banks": int(len(banks)),
        "sources": present_by_source,
        "manual_entry_counts": missing_counts,
        "datahub_counts": datahub_counts,
        "reference_dates": ref_dates,
        "bpm_present": bool(has_bpm),
        "bpm_peer_set_resolved": bpm_peer_leis,
        "bpm_peer_set_size": len(bpm_peer_leis),
        "italian_osii_resolved": italian_osii_leis,
        "italian_osii_size": len(italian_osii_leis),
        "eu_similar_size_resolved": eu_similar_leis,
        "eu_similar_size_count": len(eu_similar_leis),
    }
    (args.out_dir / "ingest_log.json").write_text(json.dumps(log, indent=2, default=str))

    print(f"Wrote {facts_path} ({len(facts):,} rows)")
    print(f"Wrote {banks_path} ({len(banks):,} banks)")
    print(f"BPM found: {has_bpm} · default peer set resolved to {len(bpm_peer_leis)} banks with data")
    print(f"Italian O-SIIs resolved: {len(italian_osii_leis)} banks")
    print(f"EU similar size (150-300B TEM) resolved: {len(eu_similar_leis)} banks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
