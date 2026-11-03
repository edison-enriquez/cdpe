# cdpe — Collateralized Debt Position of Energy: single-position simulator

Code for **Section 5, "Validation of a single position"**, of

> E. F. Enríquez Ceballos, R. D. Nieto Londoño, J. Revelo Fuelagán, O. D. Bautista Loza.
> *Collateralized energy positions for community battery storage: mechanism design and assessment.*
> Submitted to the Journal of Energy Storage, 2026.

CDPE adapts the overcollateralized debt position of decentralized finance to the energy a battery stores.
This repository contains the flat Monte Carlo harness of the paper: one position on one battery,
one price path, the rate-limiting oracle, the eight protocol invariants, and the three experiments of
Section 5 — the price envelope over 500 trajectories, the permanent-shock sweep, and the evening-discharge
collateral channel. The community co-simulation of Section 6 (mosaik + pandapower) is not part of this package.

## Quick start

```bash
git clone https://github.com/edison-enriquez/cdpe.git
cd cdpe
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/run_all.py      # ~2 min: Table 2, Fig. 2, Table 3, Fig. 3 -> results/
pytest                         # 27 tests, ~15 s
jupyter notebook notebooks/section5_walkthrough.ipynb
```

No installation of the package is needed: the scripts and tests add `src/` to the path.
`pip install -e .` also works.

## What is where

```
src/cdpe/
  params.py      every symbol of Sections 4-5 with its value          (Params)
  price.py       log-OU spot with diurnal cycle; shock to the target   (simulate_spot)
  oracle.py      rate-limiting breaker + 24 h TWAP, Eqs. 2-3          (Oracle, RejectingBreaker)
  battery.py     state of charge and capacity fade, Eq. 1             (Battery)
  vault.py       rho, alpha(SoH), debt index, liquidation, Eqs. 4-6   (Vault)
  invariants.py  I1-I8 checked at every step                          (InvariantTracker)
  simulate.py    one trajectory, the batch, evening-discharge prosumer
scripts/
  run_baseline.py      Section 5.2  -> results/baseline_*.{json,csv,npz}
  run_shock_sweep.py   Section 5.3  -> results/shock_sweep.csv
  run_discharge.py     Section 5.4  -> results/discharge_*.{csv,npz}
  make_figures.py      Fig. 2 (fig_envelope) and Fig. 3 (fig_collateral), PDF and PNG
  run_all.py           the four above in order
tests/                 unit tests of each equation + regression tests on the Section 5 figures
notebooks/             section5_walkthrough.ipynb (executed), build_notebook.py (its generator)
results/               outputs of run_all.py as committed
VERIFICATION.md        every number of Section 5, manuscript vs. this code
```

## Reproducibility

* Seeds: the 500 trajectory seeds are drawn from `numpy.random.default_rng(20260527).integers(0, 2**31 - 1)`;
  trajectory 0 has seed 464507548. Every result is deterministic given the seed.
* Timeline: the spot series starts 48 h before the position is minted so that the 24-hour reference price
  is a full average at t = 0 (see the footnote in Section 5.1 of the paper on why 24 h is not enough).
* Dispatch convention for the collateral channel: the 15-minute interval ending at 18:00 is the first one
  discharged, so the ratio evaluated at 18:00 already reflects it.
* `VERIFICATION.md` lists, quantity by quantity, how the committed results compare with the manuscript.

## Experiments in one paragraph each

**Price envelope (5.2).** 500 seven-day paths. Minted at the permitted leverage ρ0 = 1.50, about 3 % of
positions are liquidated in an ordinary week, the fifth-percentile minimum ratio is 1.265, every liquidation
clears just below α_ℓ = 1.25 and none leaves a shortfall. A conservative position at ρ0 = 2.327 is never
liquidated.

**Shock sweep (5.3).** A permanent fall of the price target at day 3.5. Liquidation needs a fall of
1 − α_ℓ/α_min = 16.7 % of the reference price; the conservative position needs falls three times as large.
The price channel never produces bad debt, but because the premium is stated at the 24-hour average while
the liquidator sells at the spot, about half of the liquidations after a 15 % fall are unprofitable for the
liquidator.

**Collateral channel (5.4).** Invariant I8 ties the pledge to the energy the battery holds. A prosumer who
discharges every evening loses a position minted at ρ0 = 1.50 on the first evening at every power from
0.5 kW up; above about 3.2 kW one 15-minute step can carry ρ from above α_ℓ to below 1, i.e. liquidation
with bad debt (13.8 % of the debt at 8 kW).

## Citing

See `CITATION.cff`. Archived releases are deposited on Zenodo (`.zenodo.json` carries the metadata).

## License

MIT — see `LICENSE`.
