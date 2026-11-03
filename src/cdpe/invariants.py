"""Invariants I1--I8 (Section 3.2), checked at every step of a trajectory.

I2, I3, I5, I6 and I7 hold by construction for a single passive position;
their checks are regression guards.  I1, I4 and I8 are the ones the dynamics
can falsify: I1 by a fall in p_ref, I4 by a liquidation with a shortfall, I8
by discharge or capacity fade.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .params import Params

NAMES = {
    "I1": "global solvency      rho >= alpha_min while debt outstanding",
    "I2": "liquidator viability alpha_liq > 1 + beta_liq",
    "I3": "monotone debt index  phi_D non-decreasing",
    "I4": "surplus buffer       S >= 0",
    "I5": "dynamic threshold    alpha(SoH) >= alpha_min",
    "I6": "reserve floor        R >= R_min",
    "I7": "parity band          PSM idle while |p_T - 1| <= eps",
    "I8": "physical backing     E_col <= sigma C",
}


@dataclass
class InvariantTracker:
    p: Params = field(default_factory=Params)
    held: dict = field(default_factory=lambda: {k: True for k in NAMES})
    first_breach: dict = field(default_factory=dict)
    _phi_prev: float = 1.0

    def check(self, step: int, *, rho: float, debt: float, phi_D: float, surplus: float,
              soh: float, reserve: float, p_T: float, psm_active: bool,
              E_col: float, stored_kWh: float) -> None:
        p = self.p
        results = {
            "I1": debt <= 0 or rho >= p.alpha_min - 1e-12,
            "I2": p.alpha_liq > 1.0 + p.beta_liq,
            "I3": phi_D >= self._phi_prev - 1e-15,
            "I4": surplus >= -1e-9,
            "I5": p.alpha_min / soh >= p.alpha_min - 1e-12,
            "I6": reserve >= p.R_min_kWh - 1e-12,
            "I7": (not psm_active) or abs(p_T - 1.0) > p.eps_psm,
            "I8": E_col <= stored_kWh + 1e-9,
        }
        self._phi_prev = phi_D
        for k, ok in results.items():
            if not ok and self.held[k]:
                self.held[k] = False
                self.first_breach[k] = step
