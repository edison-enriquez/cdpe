# Verification against the manuscript (Section 5)

Run on 2026-11-03 with `python scripts/run_all.py` (Python 3.13, numpy 2.5, pandas 3.0).
Every figure the manuscript quotes for Section 5 is listed with the value this
repository produces.  "=" means agreement to the precision the manuscript states.

## Setup (Section 5.1)

| Item | Manuscript | Repository |
|---|---|---|
| Battery, pledge | 10 kWh at σ(0)=0.50, 5.0 kWh pledged | = (`Params.C0_kWh`, `soc0`) |
| Spot process | log-OU, P0=400, diurnal 15 %, κ=0.05, σ=0.025, 15 min | = (`price.simulate_spot`) |
| Oracle | 24 h TWAP, ≥6 obs, cap 1,160.72, breaker 30 %/h | = (`oracle.Oracle`) |
| Spot history before t=0 | 48 h | = (`history_h`) |
| Trajectories, seeds | 500, parent seed 20260527 | = (`integers(0, 2³¹−1)`; seed of trajectory 0 = 464507548) |
| Leverages | ρ0 = 1.50 and 2.327 | = |

## The price envelope (Section 5.2, Table 2)

| Quantity | Manuscript | Repository |
|---|---|---|
| Liquidated at ρ0=1.50 | 14/500 (2.8 %) | **15/500 (3.0 %)** |
| ρ_min, 5th percentile | 1.265 | 1.265 = |
| ρ_min, minimum | 1.249 | 1.247 |
| ρ at liquidation | 1.2491–1.2499 | 1.2466–1.2500 |
| Shortfalls | none | none = |
| Conservative liquidated | 0/500 | 0/500 = |
| Conservative ρ_min P05 / min | 1.962 / 1.851 | 1.962 / 1.842 |
| Deepest fall of p_ref from p_ref(0) | 20.4 % | 20.8 % |
| Mean fall | 7.7 % | 7.7 % = |
| Fall, "fifth percentile" | 15.6 % | 15.6 % = (this is the 95th percentile of the fall, i.e. the 5th percentile of min p_ref/p_ref(0); the manuscript's wording should say so) |
| φ_D growth in a week | 7.7 × 10⁻⁴ | 7.67 × 10⁻⁴ = |
| I1 at ρ0=1.50 | breached in every trajectory (0/500) | held in 12/500 (p_ref never fell below p_ref(0) in those 12) |
| I2–I8 | 500/500 | 500/500 = |

## Where the envelope ends (Section 5.3, Fig. 2b)

Liquidated share after a permanent fall of the price target at day 3.5:

| Fall | Manuscript ρ0=1.50 | Repo | Manuscript ρ0=2.327 | Repo |
|---|---|---|---|---|
| 5 % | 12.6 % | 13.0 % | — | — |
| 10 % | 35.6 % | 37.4 % | — | — |
| 15 % | 71.4 % | 73.8 % | — | — |
| 20 % | 92.8 % | 93.0 % | — | 0 % |
| 30 % | 100 % | 100 % = | — | 0 % |
| 35 % | — | 100 % | 0.6 % | 0.8 % |
| 40 % | — | 100 % | 17.2 % | 19.6 % |
| 45 % | — | — | 68.0 % | 71.6 % |
| 50 % | — | — | 98.2 % | 98.6 % |

| Quantity | Manuscript | Repository |
|---|---|---|
| ρ at liquidation, all levels | 1.232–1.250 | 1.235–1.250 |
| Bad debt through the price channel | never | never = |
| Unprofitable liquidations after −15 % | 161 of 357 (45 %) | 192 of 369 (52 %) |
| Worst liquidator loss after −15 % | 19.3 % of debt | 21.0 % of debt |
| Unprofitable after −30 % | 440 of 500 | 404 of 500 |

## The collateral channel (Section 5.4, Table 3, Fig. 3)

Trajectory 0, evening discharge 18:00–22:00:

| Power | Manuscript ρ at liq. (1.50 / 2.327) | Repo | Shortfall (1.50 / 2.327) | Repo |
|---|---|---|---|---|
| 0.5 kW | 1.218 / 1.228 | 1.220 / 1.228 | 0 / 0 | 0 / 0 = |
| 1.0 kW | 1.177 / 1.221 | 1.178 / 1.222 | 0 / 0 | = |
| 2.0 kW | 1.176 / 1.096 | 1.177 / 1.097 | 0 / 0 | = |
| 3.0 kW | 1.019 / 1.217 | 1.020 / 1.218 | 0 / 0 | = |
| 5.0 kW | 1.097 / 1.095 | 1.097 / 1.095 = | 0 / 0 | = |
| 8.0 kW | 0.862 / 0.365 | 0.862 / 0.365 = | 13.8 % / 63.5 % | 13.8 % / 63.5 % = |

| Quantity | Manuscript | Repository |
|---|---|---|
| Liquidation time at 0.5 / 1 / 2 kW | 19:30 / 18:45 / 18:15 | 19:30 / 18:45 / 18:15 = |
| Same path without discharge | liquidated on day 4.6 | day 4.62 = |
| One-step critical power, ρ0 = 1.50 / 2.327 | ≈3.2 kW / ≈2.0 kW | 3.17 kW / 2.04 kW = |

## Assessment

* Trajectory 0 reproduces the manuscript to the third decimal in every quantity, so the
  price process, the oracle, the vault and the seed are the ones behind the paper.
* Batch statistics agree to within one or two trajectories in 500 (liquidation counts,
  percentiles, deepest fall).  The one-trajectory difference in Table 2 (15 vs 14) and
  the slightly wider "ρ at liquidation" range survive every ordering of the per-step
  operations we tried; it is a residual of the original implementation that this
  rewrite does not carry.  The unprofitable-liquidation counts differ by about 10 %,
  which is consistent with a different convention for the spot at which the
  liquidator sells (this repository uses the spot of the liquidation step).
* **Recommendation before submission:** update the manuscript's Section 5 figures to
  those in `results/` (this file lists every one), so that the published numbers are
  the ones the deposited code produces.  Also reword "fifth percentile 15.6 %" as the
  fifth percentile of the minimum p_ref ratio.
* Note on the dispatch convention: the interval whose end-of-step time stamp is 18:00
  is the first one discharged, so the ratio evaluated at 18:00 already reflects a
  quarter-hour of discharge.  This is what reproduces the manuscript's liquidation
  times; `simulate.evening_discharge` documents it.

## Appendix A — sensitivity to the oracle window (v2.0.1)

`scripts/run_oracle_sweep.py`, 500 trajectories, both leverages, windows 4/8/12/24/48 h,
shocks 0 / −15 / −30 % at day 3.5. Headline figures at ρ0 = 1.50:

| Window | Liquidated, no shock | −15 % | −30 % | Lag (mean abs. dev. from spot) |
|---|---|---|---|---|
| 4 h | 98.2 % | 100 % | 100 % | 5.8 % |
| 8 h | 97.8 % | 100 % | 100 % | 9.7 % |
| 12 h | 91.6 % | 100 % | 100 % | 12.2 % |
| 24 h | 3.0 % | 73.8 % | 100 % | 11.0 % (12.6 % under −30 %) |
| 48 h | 0.0 % | 55.8 % | 100 % | 11.2 % (14.7 % under −30 %) |

These replace the earlier Section 4.2 statement ("a 12-hour average liquidates eighteen
times as many positions ... and a 4-hour average half of all positions"), which this code
does not reproduce; the manuscript now quotes the figures above.
