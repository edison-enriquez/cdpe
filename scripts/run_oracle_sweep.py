"""Appendix A -- sensitivity to the oracle window (referred to in Section 4.2).

Repeats the 500-trajectory batch at both leverages (rho0 = 1.50 and 2.327)
with averaging windows of 4, 8, 12, 24 and 48 hours, without a shock and
under permanent falls of the price target of 15 % and 30 % at day 3.5.  For each case it reports the share of
positions liquidated within the week and the lag of the reference price,
measured as the mean absolute deviation of p_ref from the spot over the week.
Writes results/oracle_sweep.csv.
"""

import numpy as np
import pandas as pd

from _common import P, RESULTS
from cdpe import run_batch

WINDOWS_H = [4.0, 8.0, 12.0, 24.0, 48.0]
SHOCKS = [0.0, -0.15, -0.30]


def main():
    rows = []
    for rho0 in (P.rho0, P.rho0_conservative):
      for w in WINDOWS_H:
        p = P.with_(twap_window_h=w)
        for s in SHOCKS:
            res = run_batch(p, rho0=rho0, shock=s, shock_day=3.5)
            liqs = [r.liquidation for r in res if r.liquidation]
            lag = np.mean([np.nanmean(np.abs(r.p_ref / r.spot - 1.0)) for r in res])
            lag_post = np.mean([np.nanmean(np.abs(r.p_ref[r.t_h >= 84] / r.spot[r.t_h >= 84] - 1.0)) for r in res])
            rows.append(dict(rho0=rho0, window_h=w, shock_pct=100 * s, n=len(res), liquidated=len(liqs),
                             liquidated_pct=100 * len(liqs) / len(res),
                             shortfalls=sum(l.shortfall > 0 for l in liqs),
                             unprofitable_pct_of_liq=(100 * sum(l.unprofitable for l in liqs) / len(liqs)) if liqs else 0.0,
                             lag_mean_abs_pct=100 * lag, lag_after_shock_pct=100 * lag_post,
                             rho_min_p05=float(np.percentile([r.min_rho for r in res], 5))))
            print(f"  rho0 {rho0:<5} window {w:>4.0f} h  shock {100*s:>4.0f} %: liquidated {len(liqs):>3}/500 "
                  f"({rows[-1]['liquidated_pct']:5.1f} %)  lag {100*lag:4.1f} %  shortfalls {rows[-1]['shortfalls']}")
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "oracle_sweep.csv", index=False)
    print("written:", RESULTS / "oracle_sweep.csv")


if __name__ == "__main__":
    main()
