# Changelog

## v2.0.1 (2026-11-03)
- Added `scripts/run_oracle_sweep.py` and `results/oracle_sweep.csv`: sensitivity of the
  protocol to the reference-price window (4, 8, 12, 24, 48 h) at both leverages, without
  a shock and under -15 % and -30 % falls of the price target (Appendix A of the manuscript).
- `run_all.py` now runs the oracle sweep.
- Equation numbers in docstrings and README now follow the manuscript (Eq. 2 battery,
  Eqs. 3-4 oracle, Eqs. 5-7 position). No change to the code paths or to any result.

## v2.0.0 (2026-11-03)
- First public release: Section 5 simulator, scripts, tests, notebook, results.
