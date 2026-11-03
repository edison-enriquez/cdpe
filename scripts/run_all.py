"""Reproduce every number and figure of Section 5 in one go (about 6 minutes; the oracle sweep is the long one)."""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for script in ("run_baseline.py", "run_shock_sweep.py", "run_discharge.py", "run_oracle_sweep.py", "make_figures.py"):
    print(f"\n=== {script} ===")
    subprocess.run([sys.executable, str(HERE / script)], check=True)
print("\nAll outputs are in", HERE.parent / "results")
