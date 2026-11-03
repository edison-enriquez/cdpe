"""Spot price process (Section 5.1).

The spot follows a log-Ornstein--Uhlenbeck process around a diurnal cycle:

    log p_WS(t) = log P0 + A sin(2 pi (h(t) - h_peak + 6) / 24) + X(t)
    X(t+1)      = (1 - kappa) X(t) + sigma eps(t),   eps ~ N(0, 1)

with A the diurnal amplitude, kappa the per-step mean reversion and sigma the
per-step log volatility.  The level P0 cancels out of every ratio that matters,
because rho(t) depends only on p_ref(t) / p_ref(0).

A permanent multiplicative shock to the price *target* (Section 5.3) multiplies
P0 by (1 + shock) from a given step onward; the OU deviation X is untouched, so
the price converges to the new target at the rate kappa.
"""

from __future__ import annotations

import numpy as np

from .params import Params


def diurnal_log_factor(step_index: np.ndarray, p: Params) -> np.ndarray:
    """Diurnal component of the log price for an array of step indices.

    The cycle peaks at ``p.diurnal_peak_h`` (19:00 by default) and troughs
    twelve hours earlier.  Step 0 is midnight of the first simulated day.
    """
    hour = (step_index * p.dt_h) % 24.0
    phase = 2.0 * np.pi * (hour - p.diurnal_peak_h) / 24.0
    return p.diurnal_amp * np.cos(phase)


def simulate_spot(
    seed: int,
    p: Params = Params(),
    shock: float = 0.0,
    shock_day: float = 3.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(t_h, spot)`` for one trajectory.

    ``t_h`` runs from ``-history_h`` to the end of the horizon in steps of
    ``dt_h``; index ``p.n_history`` is t = 0, the step at which the position
    is minted.  ``spot`` is in COP/kWh.

    The OU deviation starts at zero at ``-history_h``.  With a 48-hour history
    the start-up transient has decayed well before the averaging window that
    defines p_ref(0) (see footnote in Section 5.1).
    """
    rng = np.random.default_rng(seed)
    n_total = p.n_history + p.n_steps + 1
    idx = np.arange(n_total) - p.n_history           # step index relative to t = 0
    t_h = idx * p.dt_h

    eps = rng.standard_normal(n_total)
    x = np.empty(n_total)
    x[0] = 0.0
    for k in range(1, n_total):
        x[k] = (1.0 - p.kappa) * x[k - 1] + p.sigma * eps[k]

    target = np.full(n_total, p.P0)
    if shock != 0.0:
        shock_step = p.n_history + int(round(shock_day * p.steps_per_day))
        target[shock_step:] *= (1.0 + shock)

    spot = target * np.exp(diurnal_log_factor(idx, p) + x)
    return t_h, spot


def trajectory_seeds(p: Params = Params()) -> np.ndarray:
    """Seeds of the ``p.n_traj`` trajectories, drawn from the parent generator."""
    parent = np.random.default_rng(p.parent_seed)
    return parent.integers(0, 2**31 - 1, size=p.n_traj)
