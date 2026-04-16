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

from core.peers import BPM_LEI, DEFAULT_BPM_PEERS, resolve_peer_set
from core.schema import validate_facts
from ingestion.bank_dimension import build_bank_dimension
from ingestion.eba_export import parse_eba_export
from ingestion.normalize import load_missing_bank_facts, merge_sources


DEFAULT_EXPORT = ROOT / "data" / "raw" / "p3mreldata_2025q4.xlsx"
DEFAULT_ENTRIES = ROOT / "data" / "manual_entries"
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
        "--manual-entries",
        type=Path,
        default=DEFAULT_ENTRIES,
        help="Directory of per-bank manual-entry JSONs (for banks missing from the EBA export).",
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

    missing_facts, missing_counts = load_missing_bank_facts(args.manual_entries)
    facts = merge_sources(eba_facts, missing_facts)
    facts_path = args.out_dir / "facts.parquet"
    facts.to_parquet(facts_path, index=False)

    banks = build_bank_dimension(facts)
    banks_path = args.out_dir / "banks.parquet"
    banks.to_parquet(banks_path, index=False)

    bpm_peer_leis = resolve_peer_set(DEFAULT_BPM_PEERS, banks)
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
        "reference_dates": ref_dates,
        "bpm_present": bool(has_bpm),
        "bpm_peer_set_resolved": bpm_peer_leis,
        "bpm_peer_set_size": len(bpm_peer_leis),
    }
    (args.out_dir / "ingest_log.json").write_text(json.dumps(log, indent=2, default=str))

    print(f"Wrote {facts_path} ({len(facts):,} rows)")
    print(f"Wrote {banks_path} ({len(banks):,} banks)")
    print(f"BPM found: {has_bpm} · default peer set resolved to {len(bpm_peer_leis)} banks with data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
