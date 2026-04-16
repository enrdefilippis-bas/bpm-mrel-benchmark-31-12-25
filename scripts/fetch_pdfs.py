"""Fetch Pillar 3 PDFs for the five EBA-missing banks.

Idempotent: skips files already present under ``data/raw/pdfs/<bank>/``.
By default the script is **dry-run** — it only prints the URLs it would
download. Pass ``--execute`` to actually fetch. This is deliberate:
banks often shift PDF URLs each quarter, so a blind fetch can easily
download a wrong file. Eyeball the URLs first.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.missing_banks import ALL_PARSERS, BaseBankParser


DEFAULT_YEAR = 2025
DEFAULT_QUARTER = "Q4"
DEFAULT_MONTH = 3       # issuance month for the Q4 disclosure (≈ March next yr)
DEFAULT_YEAR_SHORT = DEFAULT_YEAR % 100


@dataclass(frozen=True)
class FetchPlan:
    parser: type[BaseBankParser]
    url: str
    dest: Path


def _build_plan(parser: type[BaseBankParser], *, year: int, quarter: str,
                month: int, year_short: int, out_root: Path) -> FetchPlan:
    try:
        url = parser.meta.pillar3_url_pattern.format(
            year=year,
            quarter=quarter,
            year_short=year_short,
            month=month,
            # credit_agricole needs a per-release document id — user edits
            # the URL pattern locally or fills the JSON directly.
            doc_id="UNKNOWN",
        )
    except KeyError as exc:
        url = f"[template-gap] {parser.meta.ir_page} (missing placeholder: {exc})"
    sub = out_root / f"{parser.__name__.removesuffix('Parser').lower()}"
    dest = sub / f"pillar3_{year}_{quarter}.pdf"
    return FetchPlan(parser=parser, url=url, dest=dest)


def _fetch(plan: FetchPlan, *, timeout: float = 60.0) -> bool:
    plan.dest.parent.mkdir(parents=True, exist_ok=True)
    if plan.dest.exists():
        return False  # skip — already present
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        r = client.get(plan.url)
        r.raise_for_status()
        plan.dest.write_bytes(r.content)
    return True


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute", action="store_true",
                   help="Actually download; default is dry-run (print URLs).")
    p.add_argument("--year", type=int, default=DEFAULT_YEAR)
    p.add_argument("--quarter", default=DEFAULT_QUARTER,
                   help="Pillar 3 reporting quarter tag (Q2/Q3/Q4/H1/H2).")
    p.add_argument("--month", type=int, default=DEFAULT_MONTH,
                   help="Issuance month (some IR sites encode it in the URL).")
    p.add_argument("--out", type=Path, default=ROOT / "data" / "raw" / "pdfs")
    args = p.parse_args()

    plans = [
        _build_plan(cls, year=args.year, quarter=args.quarter,
                    month=args.month, year_short=args.year % 100,
                    out_root=args.out)
        for cls in ALL_PARSERS
    ]

    print(f"Plan ({'EXECUTE' if args.execute else 'dry-run'}):")
    for plan in plans:
        status = "present" if plan.dest.exists() else "missing"
        print(f"  · {plan.parser.meta.name}")
        print(f"      url:  {plan.url}")
        print(f"      dest: {plan.dest}  [{status}]")

    if not args.execute:
        print()
        print("Dry-run only. Re-run with --execute to download. If URLs look "
              "wrong, update the pattern on the parser's BankMeta or drop the "
              "PDF into data/raw/pdfs/<bank>/ manually.")
        return 0

    for plan in plans:
        if plan.url.startswith("[template-gap]"):
            print(f"skip (template gap): {plan.parser.meta.name}")
            continue
        try:
            downloaded = _fetch(plan)
            print(f"{'downloaded' if downloaded else 'already present'}: "
                  f"{plan.dest.name}")
        except httpx.HTTPError as exc:
            print(f"ERROR fetching {plan.parser.meta.name}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
