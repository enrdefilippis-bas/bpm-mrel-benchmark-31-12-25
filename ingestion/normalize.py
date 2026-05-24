"""Merge the EBA export with the per-bank PDF / manual-entry parsers.

Precedence rule: EBA wins per (LEI, template, reference_date). A
bank-specific parser can supplement templates or dates that the EBA
export does not cover for that bank (e.g. BBVA has KM2 at 2025-06-30
in EBA but the manual entry adds KM2 at 2025-12-31 and TLAC1).

Exception — MANUAL_OVERRIDE_KEYS: specific (LEI, template, date) triples
where the EBA export is known to be incomplete / aggregated and the
manual_entries JSON should take precedence. Example: BPM TLAC3 at
31-12-2025 — the EBA cell-level export collapses Rank 2 and Rank 4 under
a no-open_key line, while the BPM Pillar 3 PDF discloses the full
granular breakdown.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.schema import empty_facts, validate_facts
from ingestion.missing_banks import ALL_PARSERS, BaseBankParser


# (entity_lei, template, reference_date_iso) triples where the manual_entry
# should override the EBA export. The EBA row is dropped so the manual_entry
# row(s) are kept in the merge.
MANUAL_OVERRIDE_KEYS: set[tuple[str, str, str]] = {
    # BPM TLAC3 31-12-2025 — EBA aggregates Rank 2 + Rank 4 under no-open_key;
    # PDF discloses Rank 1 (Equity 12,672M), Rank 2 (Capital instr + Subord
    # 3,606M), Rank 4 (Senior Non-Preferred 3,250M), Rank 5 (Unsecured
    # 5,780M), Rank 6 (Deposits MREL eligible 281M).
    ("815600E4E6DCD2D25E30", "K_97.00", "2025-12-31"),
}


def _drop_override_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove rows in ``frame`` whose (LEI, template, date) matches a
    MANUAL_OVERRIDE_KEYS entry — but only if the source is NOT a pdf-*
    manual_entry. Used to prevent EBA / datahub from contributing rows
    that the manual_entries explicitly override.
    """
    if frame is None or frame.empty or not MANUAL_OVERRIDE_KEYS:
        return frame
    is_manual = frame["source"].astype(str).str.startswith("pdf-")
    keys = pd.Series(
        list(
            zip(
                frame["entity_lei"].astype(str),
                frame["template"].astype(str),
                frame["reference_date"].dt.strftime("%Y-%m-%d"),
            )
        ),
        index=frame.index,
    )
    override_match = keys.isin(MANUAL_OVERRIDE_KEYS)
    drop_mask = override_match & ~is_manual
    if drop_mask.any():
        return frame.loc[~drop_mask].copy()
    return frame


def merge_sources(
    eba_facts: pd.DataFrame,
    *extra_frames: pd.DataFrame,
) -> pd.DataFrame:
    """Stack EBA facts with extra sources, enforcing EBA precedence by LEI.

    Exception: rows matching ``MANUAL_OVERRIDE_KEYS`` are removed from any
    non-manual source (EBA, datahub) before the merge so the corresponding
    manual_entry row(s) are kept.
    """
    if eba_facts is None or eba_facts.empty:
        base = empty_facts()
    else:
        base = eba_facts.copy()

    # Drop overriding rows from EBA.
    base = _drop_override_rows(base)

    eba_keys: set[tuple[str, str, str]] = set()
    if not base.empty:
        eba_keys = set(
            zip(
                base["entity_lei"].astype(str),
                base["template"].astype(str),
                base["reference_date"].astype(str),
            )
        )

    pieces: list[pd.DataFrame] = [base]
    for frame in extra_frames:
        if frame is None or frame.empty:
            continue
        # Also drop overriding rows from non-manual extra sources (e.g. datahub).
        frame = _drop_override_rows(frame)
        keep_mask = ~pd.Series(
            list(
                zip(
                    frame["entity_lei"].astype(str),
                    frame["template"].astype(str),
                    frame["reference_date"].astype(str),
                )
            ),
            index=frame.index,
        ).isin(eba_keys)
        add = frame[keep_mask]
        if add.empty:
            continue
        pieces.append(add)

    merged = pd.concat(pieces, ignore_index=True) if pieces else empty_facts()
    # Schema enforcement (also reorders columns).
    return validate_facts(merged)


def load_missing_bank_facts(
    entries_dir: Path | str,
    parsers: tuple[type[BaseBankParser], ...] = ALL_PARSERS,
    pdfs_dir: Path | str | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Load facts for every missing bank, preferring PDF parsing when available.

    For each parser: if ``pdfs_dir`` is provided and a PDF exists at
    ``{pdfs_dir}/{stem}/pillar3_*.pdf``, try ``parse_pdf``. On success, use
    the PDF-extracted facts. On failure (or if no PDF), fall back to the
    manual-entries JSON at ``{entries_dir}/{stem}.json``.

    Returns a long-format facts frame plus a per-parser fact-count
    dictionary (useful for the ingest log).
    """
    entries_dir = Path(entries_dir)
    pdfs_dir = Path(pdfs_dir) if pdfs_dir is not None else None
    parts: list[pd.DataFrame] = []
    counts: dict[str, int] = {}
    for cls in parsers:
        stem = _entry_stem(cls)
        df = empty_facts()
        source_used = "manual"

        if pdfs_dir is not None:
            pdf_candidates = sorted((pdfs_dir / _pdf_stem(cls)).glob("pillar3_*.pdf")) \
                if (pdfs_dir / _pdf_stem(cls)).exists() else []
            for pdf_path in pdf_candidates:
                try:
                    df = cls.parse_pdf(pdf_path)
                    source_used = f"pdf:{pdf_path.name}"
                    break
                except Exception:
                    # PDF layout may have drifted; try next PDF or fall through
                    continue

        if df.empty:
            json_path = entries_dir / f"{stem}.json"
            df = cls.from_manual_entries(json_path)
            source_used = "manual"

        counts[cls.meta.source_tag] = int(len(df))
        counts[f"{cls.meta.source_tag}:origin"] = source_used  # for the ingest log
        if not df.empty:
            parts.append(df)
    merged = pd.concat(parts, ignore_index=True) if parts else empty_facts()
    return merged, counts


def _entry_stem(cls: type[BaseBankParser]) -> str:
    """Derive the manual-entries JSON filename from the parser's source tag.

    ``pdf-intesa`` → ``intesa``; ``pdf-credit-agricole`` → ``credit_agricole``.
    Using source_tag keeps the JSON filename in sync with the Source enum.
    """
    return cls.meta.source_tag.removeprefix("pdf-").replace("-", "_")


def _pdf_stem(cls: type[BaseBankParser]) -> str:
    """Derive the PDF subdirectory name for a parser.

    Matches the folder layout under ``data/raw/pdfs/``:
    ``pdf-credit-agricole`` → ``ca-sa``; ``pdf-intesa`` → ``intesa``.
    Crédit Agricole is a legacy alias; every other bank's folder is the
    parser stem as-is.
    """
    mapping = {
        "pdf-credit-agricole": "ca-sa",
    }
    return mapping.get(cls.meta.source_tag,
                       cls.meta.source_tag.removeprefix("pdf-"))
