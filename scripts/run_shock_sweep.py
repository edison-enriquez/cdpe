"""Section 5.3 -- where the envelope ends, and who bears the oracle lag.

A permanent multiplicative shock to the price target at day 3.5, repeated over
the 500 trajectories at both leverages.  Writes results/shock_sweep.csv with,
per (rho0, shock): liquidated share, share of liquidations unprofitable for the
liquidator at the spot, worst liquidator loss, rho at liquidation range,
shortfalls.
"""

import numpy as np
import pandas as pd

from _common import P, RESULTS
from cdpe import run_batch

SHOCKS_BASELINE = [0.0, -0.05, -0.10, -0.15, -0.20, -0.25, -0.30, -0.35, -0.40]
SHOCKS_CONSERVATIVE = [0.0, -0.20, -0.30, -0.35, -0.40, -0.45, -0.50]


def sweep(rho0, shocks):
    rows = []
    for s in shocks:
        res = run_batch(P, rho0=rho0, shock=s, shock_day=3.5)
        liqs = [r.liquidation for r in res if r.liquidation]
        n = len(res)
        unprof = [l for l in liqs if l.unprofitable]
        rows.append(dict(
            rho0=rho0, shock_pct=100 * s, n=n,
            liquidated=len(liqs), liquidated_pct=100 * len(liqs) / n,
            unprofitable=len(unprof),
            unprofitable_pct_of_liq=(100 * len(unprof) / len(liqs)) if liqs else 0.0,
            worst_liquidator_loss_pct=(min(100 * l.liquidator_pnl / l.debt for l in liqs)) if liqs else np.nan,
            rho_at_liq_min=(min(l.rho for l in liqs)) if liqs else np.nan,
            rho_at_liq_max=(max(l.rho for l in liqs)) if liqs else np.nan,
            shortfalls=sum(1 for l in liqs if l.shortfall > 0),
        ))
        print(f"  rho0={rho0:<6} shock {100*s:>5.0f} %: liquidated {len(liqs):>3}/{n} "
              f"({rows[-1]['liquidated_pct']:5.1f} %), unprofitable {len(unprof):>3}, "
              f"shortfalls {rows[-1]['shortfalls']}")
    return rows


def main():
    print("[shock sweep, rho0 = 1.50]")
    rows = sweep(P.rho0, SHOCKS_BASELINE)
    print("[shock sweep, rho0 = 2.327]")
    rows += sweep(P.rho0_conservative, SHOCKS_CONSERVATIVE)
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "shock_sweep.csv", index=False)
    print("written:", RESULTS / "shock_sweep.csv")


if __name__ == "__main__":
    main()
