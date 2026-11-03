"""Protocol and simulation parameters.

Every symbol is the one used in the manuscript; the section that defines it is
given in the comment.  Changing a value here changes every experiment.
"""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Params:
    # --- time ---------------------------------------------------------------
    dt_h: float = 0.25            # step length [h]; 15-minute resolution (Sec. 5.1)
    horizon_days: float = 7.0     # one week (Sec. 5.1)
    history_h: float = 48.0       # spot history before t = 0 (Sec. 5.1, footnote)

    # --- battery (Sec. 4.1, 5.1) -------------------------------------------
    C0_kWh: float = 10.0          # nominal capacity
    soc0: float = 0.50            # initial state of charge
    soc_min: float = 0.0          # minimum state of charge for usable energy
    eta_c: float = 0.95           # charge efficiency
    eta_d: float = 0.95           # discharge efficiency
    delta_fade: float = 0.0       # capacity fade per unit throughput (delta = 0 on 7-day horizons)

    # --- spot price process (Sec. 5.1) -------------------------------------
    P0: float = 400.0             # long-run level [COP/kWh]
    diurnal_amp: float = 0.15     # diurnal amplitude of the log price
    kappa: float = 0.05           # mean reversion per step
    sigma: float = 0.025          # per-step log volatility
    diurnal_peak_h: float = 19.0  # hour of day at which the diurnal cycle peaks

    # --- oracle (Sec. 4.2) -------------------------------------------------
    twap_window_h: float = 24.0   # averaging window
    twap_min_obs: int = 6         # minimum observations for a valid average
    breaker_rate: float = 0.30    # b = 30 %/h rate limit (Eq. 3)
    p_esc: float = 1160.72        # scarcity cap [COP/kWh] (CREG 101 097 de 2026, May 2026)

    # --- collateralization and liquidation (Sec. 4.3, 4.5) -----------------
    alpha_min: float = 1.50       # minting threshold
    alpha_liq: float = 1.25       # liquidation threshold
    beta_liq: float = 0.10        # liquidation premium

    # --- debt index and savings (Sec. 4.4) ---------------------------------
    r_sf: float = 0.04            # stability fee [1/yr]
    r_esr: float = 0.015          # savings rate [1/yr]

    # --- parity module (Sec. 4.6) ------------------------------------------
    eps_psm: float = 0.05         # parity band
    K_p: float = 0.10             # proportional gain
    R_min_kWh: float = 0.0        # reserve floor (module inactive in Sec. 5)

    # --- simulation --------------------------------------------------------
    n_traj: int = 500             # Monte Carlo trajectories
    parent_seed: int = 20260527   # parent generator seed (Sec. 5.1)
    rho0: float = 1.50            # initial collateralization ratio of the baseline position
    rho0_conservative: float = 2.327

    @property
    def n_steps(self) -> int:
        return int(round(self.horizon_days * 24.0 / self.dt_h))

    @property
    def n_history(self) -> int:
        return int(round(self.history_h / self.dt_h))

    @property
    def steps_per_day(self) -> int:
        return int(round(24.0 / self.dt_h))

    def with_(self, **kw) -> "Params":
        return replace(self, **kw)


DEFAULT = Params()
