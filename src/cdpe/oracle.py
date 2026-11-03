"""Reference price oracle (Section 4.2, Eqs. 2--3).

Each spot observation is admitted through a rate-limiting circuit breaker,

    p~_k = min{ max{ p_WS(tau_k), p~_{k-1} (1 - b dtau_k) },  p~_{k-1} (1 + b dtau_k) },

so that a crash is *followed* at the maximum rate b = 30 %/h rather than
rejected.  The reference price is the 24-hour time-weighted average of the
admitted observations, clipped at the scarcity cap:

    p_ref(t) = min{ mean_{k in K(t)} p~_k,  p_esc },   K(t) = {k : t - 24 h < tau_k <= t},

valid when the window holds at least ``twap_min_obs`` observations.

``RejectingBreaker`` is the first implementation discussed in Section 6.2,
which rejects any observation more than b away from the last accepted one
without scaling by the elapsed time.  It is kept for the comparison in that
section and in the tests; the protocol specifies the rate-limiting breaker.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from .params import Params


class Oracle:
    """Rate-limiting breaker + 24-hour TWAP, fed one observation at a time."""

    def __init__(self, p: Params = Params()):
        self.p = p
        self._admitted: deque[float] = deque()
        self._times: deque[float] = deque()
        self._last: float | None = None
        self._last_t: float | None = None

    # -- Eq. 3 ---------------------------------------------------------------
    def _admit(self, t_h: float, p_ws: float) -> float:
        if self._last is None:
            tilde = p_ws
        else:
            dtau = t_h - self._last_t
            lo = self._last * (1.0 - self.p.breaker_rate * dtau)
            hi = self._last * (1.0 + self.p.breaker_rate * dtau)
            tilde = min(max(p_ws, lo), hi)
        self._last, self._last_t = tilde, t_h
        return tilde

    # -- Eq. 2 ---------------------------------------------------------------
    def update(self, t_h: float, p_ws: float) -> float:
        """Admit one observation at time ``t_h`` and return p_ref(t_h)."""
        tilde = self._admit(t_h, p_ws)
        self._admitted.append(tilde)
        self._times.append(t_h)
        cutoff = t_h - self.p.twap_window_h
        while self._times and self._times[0] <= cutoff:
            self._times.popleft()
            self._admitted.popleft()
        return self.value

    @property
    def value(self) -> float:
        if len(self._admitted) < self.p.twap_min_obs:
            return float("nan")
        return min(float(np.mean(self._admitted)), self.p.p_esc)

    @property
    def n_obs(self) -> int:
        return len(self._admitted)


class RejectingBreaker(Oracle):
    """Breaker that rejects observations outside +-b of the last accepted one
    and averages the last N accepted observations (N = window / dt).

    This is the implementation Section 6.2 shows locking onto stale values on
    historical prices.  Not used by the protocol.
    """

    def __init__(self, p: Params = Params(), n_avg: int | None = None):
        super().__init__(p)
        self.n_avg = n_avg or int(round(p.twap_window_h / p.dt_h))
        self.rejected = 0

    def update(self, t_h: float, p_ws: float) -> float:
        if self._last is not None and abs(p_ws / self._last - 1.0) > self.p.breaker_rate:
            self.rejected += 1
        else:
            self._last, self._last_t = p_ws, t_h
            self._admitted.append(p_ws)
            self._times.append(t_h)
            while len(self._admitted) > self.n_avg:
                self._admitted.popleft()
                self._times.popleft()
        return self.value


def reference_price_series(t_h: np.ndarray, spot: np.ndarray, p: Params = Params(),
                           oracle_cls=Oracle) -> np.ndarray:
    """Vectorised convenience: p_ref for a whole spot series."""
    o = oracle_cls(p)
    return np.array([o.update(float(t), float(s)) for t, s in zip(t_h, spot)])
