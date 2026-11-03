"""Section 5.2 -- the price envelope.

500 seven-day trajectories at the permitted leverage (rho0 = 1.50) and for a
conservative position (rho0 = 2.327) on the same price paths.  Writes

    results/baseline_summary.json       Table 2 and the figures quoted in the text
    results/baseline_trajectories.csv   per-trajectory seed, min rho, p_ref fall, liquidation
    results/baseline_rho_paths.npz      rho(t) of every trajectory, both leverages (for Fig. 2a)
"""

import json
import numpy as np
import pandas as pd

from _common import P, RESULTS
from cdpe import run_batch
from cdpe.simulate import batch_summary


def main():
    out = {}
    paths = {}
    rows = []
    for label, rho0 in (("baseline", P.rho0), ("conservative", P.rho0_conservative)):
        print(f"[{label}] rho0 = {rho0}: {P.n_traj} trajectories ...")
        res = run_batch(P, rho0=rho0, progress=True)
        s = batch_summary(res, P)
        out[label] = s
        paths[label] = np.array([r.rho for r in res])
        paths["t_h"] = res[0].t_h
        for r in res:
            l = r.liquidation
            rows.append(dict(config=label, seed=r.seed, p_ref0=r.p_ref0, debt_COP=r.debt0,
                             min_rho=r.min_rho, pref_fall=r.max_pref_fall,
                             liquidated=r.liquidated,
                             liq_day=(l.t_h / 24.0) if l else np.nan,
                             rho_at_liq=(l.rho if l else np.nan),
                             shortfall_pct=(l.shortfall_pct if l else 0.0),
                             liquidator_pnl_pct=(100 * l.liquidator_pnl / l.debt if l else np.nan),
                             **{k: v for k, v in r.invariants.items()}))
        print(f"  liquidated {s['liquidated']}/{s['n']} ({s['liquidated_pct']:.1f} %), "
              f"rho_min P05 {s['rho_min_p05']:.3f}, min {s['rho_min_min']:.3f}, "
              f"p_ref fall max {100*s['pref_fall_max']:.1f} % mean {100*s['pref_fall_mean']:.1f} % "
              f"P95 {100*s['pref_fall_p95']:.1f} %")
        print("  invariants held:", s["invariants_held"])

    # Fig. 2a also shows the baseline under a permanent -15 % shock at day 3.5
    print("[baseline, -15 % shock at day 3.5] ...")
    res = run_batch(P, rho0=P.rho0, shock=-0.15, shock_day=3.5)
    paths["baseline_shock15"] = np.array([r.rho for r in res])
    out["baseline_shock15"] = batch_summary(res, P)

    (RESULTS / "baseline_summary.json").write_text(json.dumps(out, indent=2, default=str))
    pd.DataFrame(rows).to_csv(RESULTS / "baseline_trajectories.csv", index=False)
    np.savez_compressed(RESULTS / "baseline_rho_paths.npz", **paths)
    print("written:", RESULTS / "baseline_summary.json")


if __name__ == "__main__":
    main()
