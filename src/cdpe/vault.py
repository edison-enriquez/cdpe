"""A single collateralized position (Sections 4.3--4.6).

    rho(t)     = E_col(t) p_ref(t) / l$(t)                       (Eq. 5)
    alpha(t)   = alpha_min / SoH(t)                              (Eq. 5)
    phi_D(t+d) = phi_D(t) (1 + r_SF d)                           (Eq. 6)
    E_rec      = min{ E_col, l$ (1 + beta) / p_ref }             (Eq. 7)

The position is liquidated when rho < alpha_liq.  The liquidator repays l$,
receives E_rec, and the shortfall l$ - E_col p_ref (if positive) is bad debt
charged to the surplus buffer S (invariant I4).

Invariant I8 (physical backing) binds the pledge to the energy the battery
holds: E_col <= sigma C.  When the battery discharges, the pledge falls with
it -- the *collateral channel* of Section 5.4.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .params import Params

HOURS_PER_YEAR = 8760.0


@dataclass
class LiquidationRecord:
    step: int
    t_h: float
    rho: float
    p_ref: float
    spot: float
    debt: float
    E_col: float
    E_rec: float
    shortfall: float          # bad debt in COP (0 if none)
    liquidator_pnl: float     # E_rec * spot - debt  (what the liquidator realises at the spot)

    @property
    def unprofitable(self) -> bool:
        return self.liquidator_pnl < 0.0

    @property
    def shortfall_pct(self) -> float:
        return 100.0 * self.shortfall / self.debt if self.debt > 0 else 0.0


@dataclass
class Vault:
    p: Params = field(default_factory=Params)
    E_col: float = 0.0            # pledged energy [kWh]
    debt_shares: float = 0.0      # l_sh
    phi_D: float = 1.0            # debt index
    surplus: float = 0.0          # S [COP]
    liquidated: bool = False
    record: LiquidationRecord | None = None

    # -- minting ---------------------------------------------------------------
    def open(self, E_col: float, p_ref: float, rho0: float) -> float:
        """Pledge ``E_col`` kWh and mint debt so that rho(0) = rho0.  Returns l$."""
        self.E_col = E_col
        debt = E_col * p_ref / rho0
        self.debt_shares = debt / self.phi_D
        return debt

    @property
    def debt(self) -> float:
        return self.debt_shares * self.phi_D

    # -- Eq. 4 -----------------------------------------------------------------
    def rho(self, p_ref: float) -> float:
        d = self.debt
        return float("inf") if d <= 0 else self.E_col * p_ref / d

    def alpha(self, soh: float) -> float:
        return self.p.alpha_min / soh

    def can_mint(self, dT: float, p_ref: float, soh: float) -> bool:
        return self.E_col * p_ref >= self.alpha(soh) * (self.debt + dT)

    # -- Eq. 5 -----------------------------------------------------------------
    def accrue(self, dt_h: float) -> None:
        self.phi_D *= 1.0 + self.p.r_sf * dt_h / HOURS_PER_YEAR
        # stability fee credited to the buffer, savings rate debited (worst case T_locked = T_tot)
        self.surplus += self.debt * (self.p.r_sf - self.p.r_esr) * dt_h / HOURS_PER_YEAR

    # -- I8: pledge follows the stored energy ----------------------------------
    def clamp_to_stored(self, stored_kWh: float) -> None:
        if self.E_col > stored_kWh:
            self.E_col = max(0.0, stored_kWh)

    # -- Eq. 6 -----------------------------------------------------------------
    def check_liquidation(self, step: int, t_h: float, p_ref: float, spot: float) -> LiquidationRecord | None:
        if self.liquidated or self.debt <= 0:
            return None
        rho = self.rho(p_ref)
        if rho >= self.p.alpha_liq:
            return None
        debt = self.debt
        E_rec = min(self.E_col, debt * (1.0 + self.p.beta_liq) / p_ref)
        shortfall = max(0.0, debt - self.E_col * p_ref)
        self.surplus -= shortfall
        rec = LiquidationRecord(step, t_h, rho, p_ref, spot, debt, self.E_col, E_rec,
                                shortfall, E_rec * spot - debt)
        self.E_col -= E_rec
        self.debt_shares = 0.0
        self.liquidated = True
        self.record = rec
        return rec
