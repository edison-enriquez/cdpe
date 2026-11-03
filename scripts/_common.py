"""Shared helpers for the scripts: paths and the parameter set."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "src"))

from cdpe import DEFAULT  # noqa: E402

P = DEFAULT
