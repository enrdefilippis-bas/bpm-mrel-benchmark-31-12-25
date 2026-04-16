"""Merge the EBA export with the per-bank PDF / manual-entry parsers.

Precedence rule: if a bank appears in *both* the EBA export and a
bank-specific parser, the EBA fact wins — it is the authoritative
supervisory feed. The bank-specific source only contributes rows for
banks (LEIs) that are absent from the EBA export. This keeps the
peer-set coverage stable across quarters: once a bank joins the EBA
release, its PDF parser silently stops contributing.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.schema import empty_facts, validate_facts
from ingestion.missing_banks import ALL_PARSERS, BaseBankParser


def merge_sources(
    eba_facts: pd.DataFrame,
    *extra_frames: pd.DataFrame,
) -> pd.DataFrame:
    """Stack EBA facts with extra sources, enforcing EBA precedence by LEI."""
    if eba_facts is None or eba_facts.empty:
        eba_leis: set[str] = set()
        base = empty_facts()
    else:
        eba_leis = set(eba_facts["entity_lei"].unique())
        base = eba_facts

    pieces: list[pd.DataFrame] = [base]
    for frame in extra_frames:
        if frame is None or frame.empty:
            continue
        # Drop any LEI already covered by the EBA export — EBA wins.
        add = frame[~frame["entity_lei"].isin(eba_leis)]
        if add.empty:
            continue
        pieces.append(add)

    merged = pd.concat(pieces, ignore_index=True) if pieces else empty_facts()
    # Schema enforcement (also reorders columns).
    return validate_facts(merged)


def load_missing_bank_facts(
    entries_dir: Path | str,
    parsers: tuple[type[BaseBankParser], ...] = ALL_PARSERS,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Load facts from every parser's manual-entries JSON.

    Returns a long-format facts frame plus a per-parser fact-count
    dictionary (useful for the ingest log).
    """
    entries_dir = Path(entries_dir)
    parts: list[pd.DataFrame] = []
    counts: dict[str, int] = {}
    for cls in parsers:
        path = entries_dir / f"{_entry_stem(cls)}.json"
        df = cls.from_manual_entries(path)
        counts[cls.meta.source_tag] = int(len(df))
        if not df.empty:
            parts.append(df)
    merged = pd.concat(parts, ignore_index=True) if parts else empty_facts()
    return merged, counts


def _entry_stem(cls: type[BaseBankParser]) -> str:
    """Derive the JSON filename from the parser's source tag.

    ``pdf-intesa`` → ``intesa``; ``pdf-credit-agricole`` → ``credit_agricole``.
    Using source_tag keeps the JSON filename in sync with the Source enum.
    """
    return cls.meta.source_tag.removeprefix("pdf-").replace("-", "_")
