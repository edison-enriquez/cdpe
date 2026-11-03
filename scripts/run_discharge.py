"""Section 5.4 -- the collateral channel (Table 3, Fig. 3).

A prosumer who discharges the pledged battery every evening from 18:00 to
22:00 on the price path of trajectory 0, at several powers and at both
leverages.  Writes

    results/discharge_table.csv     Table 3
    results/discharge_paths.npz     rho(t) on the first evening at each power (Fig. 3)
"""

import numpy as np
import pandas as pd

from _common import P, RESULTS
from cdpe import run_trajectory
from cdpe.simulate import evening_discharge
from cdpe.price import trajectory_seeds

POWERS_KW = [0.5, 1.0, 2.0, 3.0, 5.0, 8.0]


def fmt_clock(t_h):
    d, h = divmod(t_h, 24.0)
    return f"day {int(d)+1} {int(h):02d}:{int(round((h % 1) * 60)):02d}"


def main():
    seed0 = int(trajectory_seeds(P)[0])
    rows, paths = [], {}
    ref = run_trajectory(seed0, P, rho0=P.rho0)
    print(f"trajectory 0 (seed {seed0}) without discharge: "
          f"{'liquidated on day %.1f' % (ref.liquidation.t_h/24) if ref.liquidation else 'not liquidated'}")
    paths["t_h"] = ref.t_h
    for rho0, label in ((P.rho0, "baseline"), (P.rho0_conservative, "conservative")):
        for kW in POWERS_KW:
            r = run_trajectory(seed0, P, rho0=rho0, dispatch=evening_discharge(kW))
            l = r.liquidation
            rows.append(dict(config=label, rho0=rho0, power_kW=kW,
                             kWh_per_step=kW * P.dt_h / P.eta_d,
                             liquidated=r.liquidated,
                             liq_time=(fmt_clock(l.t_h) if l else ""),
                             liq_t_h=(l.t_h if l else np.nan),
                             rho_at_liq=(l.rho if l else np.nan),
                             shortfall_pct=(l.shortfall_pct if l else 0.0)))
            paths[f"{label}_{kW}"] = r.rho
            print(f"  {label:<13} {kW:>4.1f} kW: {rows[-1]['liq_time'] or 'no liquidation':<16} "
                  f"rho {rows[-1]['rho_at_liq']:.3f}  shortfall {rows[-1]['shortfall_pct']:.1f} %")
    # critical power at which one step removes (alpha_liq - 1) * debt / p_ref
    crit = {}
    for rho0, label in ((P.rho0, "baseline"), (P.rho0_conservative, "conservative")):
        debt = ref.E_col[0] * ref.p_ref0 / rho0
        kWh = (P.alpha_liq - 1.0) * debt / ref.p_ref0
        crit[label] = kWh * P.eta_d / P.dt_h
        print(f"  one-step critical power ({label}): {crit[label]:.2f} kW")
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "discharge_table.csv", index=False)
    np.savez_compressed(RESULTS / "discharge_paths.npz", **paths)
    print("written:", RESULTS / "discharge_table.csv")


if __name__ == "__main__":
    main()
