"""Shared pytest fixtures for the benchmark tests."""
from __future__ import annotations

import sys
from pathlib import Path

# Make the package imports work when running `pytest` from the repo root.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
