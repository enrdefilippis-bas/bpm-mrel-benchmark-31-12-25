from __future__ import annotations
from pathlib import Path
import pdfplumber
import re


def extract_text(pdf_path: Path | str) -> str:
    pdf_path = Path(pdf_path)
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_tables(pdf_path: Path | str) -> list[list[list[str | None]]]:
    pdf_path = Path(pdf_path)
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables


def extract_text_page(pdf_path: Path | str, page_idx: int) -> str:
    """Extract text from a single page (0-indexed)."""
    pdf_path = Path(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        if page_idx < 0 or page_idx >= len(pdf.pages):
            return ""
        page = pdf.pages[page_idx]
        return page.extract_text() or ""


def extract_tables_page(pdf_path: Path | str, page_idx: int) -> list[list[list[str | None]]]:
    """Extract tables from a single page (0-indexed)."""
    pdf_path = Path(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        if page_idx < 0 or page_idx >= len(pdf.pages):
            return []
        page = pdf.pages[page_idx]
        return page.extract_tables() or []


def parse_number(s: str | None, european: bool = False) -> float | None:
    """Parse a number from PDF text, handling both European (1.234,56) and
    Anglo (1,234.56) formats.

    Args:
        s: String to parse (may contain "%", spaces, or be None).
        european: If True, expect "." as thousands sep and "," as decimal.
                 If False, expect "," as thousands sep and "." as decimal.

    Returns:
        Parsed float or None if parsing fails.
    """
    if s is None or not isinstance(s, str):
        return None

    s = s.strip()
    if not s:
        return None

    # Remove percentage sign and whitespace
    s = s.replace("%", "").strip()
    if not s:
        return None

    # Detect which separator is decimal and which is thousands
    last_comma_idx = s.rfind(",")
    last_dot_idx = s.rfind(".")

    # If european format (dots as thousands, comma as decimal)
    if european:
        s = s.replace(".", "").replace(",", ".")
    else:
        # Anglo format (commas as thousands, dot as decimal)
        s = s.replace(",", "")

    try:
        return float(s)
    except ValueError:
        return None
