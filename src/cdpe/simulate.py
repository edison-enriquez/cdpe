"""One trajectory of one position, and the Monte Carlo batch (Section 5).

Timeline of a trajectory
------------------------
* The spot series starts ``history_h`` (48 h) before t = 0 and is fed through
  the oracle so that p_ref(0) is a full 24-hour average.
* At t = 0 the position pledges every kilowatt-hour the battery stores
  (E_col = sigma(0) C0, the largest pledge I8 admits) and mints debt at
  rho(0) = rho0.
* Every 15 minutes thereafter: the battery is dispatched (passive by default),
  the pledge is clamped to the stored energy (I8), the debt index accrues,
  the oracle admits the new spot observation, the ratio is evaluated and the
  position is liquidated if rho < alpha_liq.  Invariants are checked after
  every step.

The ``dispatch`` argument is a callable ``(step, t_h) -> (P_c_kW, P_d_kW)``;
``evening_discharge(power_kW)`` builds the prosumer of Section 5.4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .params import Params
from .price import simulate_spot, trajectory_seeds
from .oracle import Oracle
from .battery import Battery
from .vault import Vault, LiquidationRecord
from .invariants import InvariantTracker

Dispatch = Callable[[int, float], tuple[float, float]]


def passive(step: int, t_h: float) -> tuple[float, float]:
    return 0.0, 0.0


def evening_discharge(power_kW: float, start_h: float = 18.0, end_h: float = 22.0) -> Dispatch:
    """Prosumer who discharges at ``power_kW`` every evening between start and end."""
    def d(step: int, t_h: float) -> tuple[float, float]:
        hod = t_h % 24.0
        return (0.0, power_kW) if start_h <= hod < end_h else (0.0, 0.0)
    return d


@dataclass
class TrajectoryResult:
    seed: int
    rho0: float
    t_h: np.ndarray              # times from t = 0 (length n_steps + 1)
    spot: np.ndarray
    p_ref: np.ndarray
    rho: np.ndarray              # inf after liquidation, nan before a valid p_ref
    E_col: np.ndarray
    debt0: float
    p_ref0: float
    liquidation: LiquidationRecord | None
    invariants: dict
    first_breach: dict
    min_rho: float
    max_pref_fall: float         # deepest fall of p_ref from p_ref(0), as a fraction

    @property
    def liquidated(self) -> bool:
        return self.liquidation is not None


def run_trajectory(seed: int, p: Params = Params(), rho0: float | None = None,
                   dispatch: Dispatch = passive, shock: float = 0.0, shock_day: float = 3.5,
                   spot: np.ndarray | None = None, t_full: np.ndarray | None = None) -> TrajectoryResult:
    rho0 = p.rho0 if rho0 is None else rho0
    if spot is None:
        t_full, spot = simulate_spot(seed, p, shock=shock, shock_day=shock_day)
    n_h = p.n_history

    oracle = Oracle(p)
    for k in range(n_h):                       # warm the oracle on the history
        oracle.update(float(t_full[k]), float(spot[k]))

    battery = Battery(p)
    vault = Vault(p)
    tracker = InvariantTracker(p)

    p_ref0 = oracle.update(float(t_full[n_h]), float(spot[n_h]))
    assert np.isfinite(p_ref0), "oracle not warm at t = 0"
    E_col0 = battery.stored_kWh
    debt0 = vault.open(E_col0, p_ref0, rho0)

    n = p.n_steps
    t_out = t_full[n_h:n_h + n + 1]
    spot_out = spot[n_h:n_h + n + 1]
    p_ref = np.empty(n + 1); rho = np.empty(n + 1); E_col = np.empty(n + 1)
    p_ref[0], rho[0], E_col[0] = p_ref0, vault.rho(p_ref0), vault.E_col
    liq = None
    min_rho = rho[0]

    for k in range(1, n + 1):
        t = float(t_out[k])
        P_c, P_d = dispatch(k, t)
        battery.step(P_c, P_d)
        vault.clamp_to_stored(battery.stored_kWh)        # I8
        vault.accrue(p.dt_h)                             # Eq. 5
        pr = oracle.update(t, float(spot_out[k]))        # Eqs. 2-3
        p_ref[k] = pr
        if liq is None:
            r = vault.rho(pr)
            rho[k] = r
            min_rho = min(min_rho, r)
            liq = vault.check_liquidation(k, t, pr, float(spot_out[k]))
        else:
            rho[k] = np.inf
        E_col[k] = vault.E_col
        tracker.check(k, rho=rho[k], debt=vault.debt, phi_D=vault.phi_D, surplus=vault.surplus,
                      soh=battery.soh, reserve=p.R_min_kWh, p_T=1.0, psm_active=False,
                      E_col=vault.E_col, stored_kWh=battery.stored_kWh)

    return TrajectoryResult(
        seed=seed, rho0=rho0, t_h=t_out, spot=spot_out, p_ref=p_ref, rho=rho, E_col=E_col,
        debt0=debt0, p_ref0=p_ref0, liquidation=liq, invariants=dict(tracker.held),
        first_breach=dict(tracker.first_breach), min_rho=min_rho,
        max_pref_fall=float(1.0 - np.min(p_ref) / p_ref0),
    )


def run_batch(p: Params = Params(), rho0: float | None = None, shock: float = 0.0,
              shock_day: float = 3.5, dispatch: Dispatch = passive,
              seeds: np.ndarray | None = None, progress: bool = False) -> list[TrajectoryResult]:
    seeds = trajectory_seeds(p) if seeds is None else seeds
    out = []
    for i, s in enumerate(seeds):
        out.append(run_trajectory(int(s), p, rho0=rho0, dispatch=dispatch, shock=shock, shock_day=shock_day))
        if progress and (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(seeds)} trajectories")
    return out


# --------------------------------------------------------------------------- summaries
def batch_summary(results: list[TrajectoryResult], p: Params = Params()) -> dict:
    n = len(results)
    liqs = [r.liquidation for r in results if r.liquidation is not None]
    min_rho = np.array([r.min_rho for r in results])
    falls = np.array([r.max_pref_fall for r in results])
    inv = {k: sum(r.invariants[k] for r in results) for k in results[0].invariants}
    return {
        "n": n,
        "rho0": results[0].rho0,
        "liquidated": len(liqs),
        "liquidated_pct": 100.0 * len(liqs) / n,
        "shortfalls": sum(1 for l in liqs if l.shortfall > 0),
        "unprofitable": sum(1 for l in liqs if l.unprofitable),
        "rho_min_p05": float(np.percentile(min_rho, 5)),
        "rho_min_min": float(min_rho.min()),
        "rho_at_liq_range": (min(l.rho for l in liqs), max(l.rho for l in liqs)) if liqs else (None, None),
        "pref_fall_max": float(falls.max()),
        "pref_fall_mean": float(falls.mean()),
        "pref_fall_p95": float(np.percentile(falls, 95)),
        "invariants_held": inv,
        "phi_D_growth": p.r_sf * p.horizon_days * 24.0 / 8760.0,
    }
