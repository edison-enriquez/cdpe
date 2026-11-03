"""Battery dynamics (Section 4.1, Eq. 1).

    sigma(t+1) = sigma(t) + dt / C(t) * [eta_c P_c(t) - P_d(t) / eta_d]
    C(t)       = C0 [1 - delta D_thr(t) / (2 C0)]

with D_thr the cumulative throughput.  On the seven-day horizons of the paper
delta = 0, so C(t) = C0 and SoH = 1; the fade term is implemented so that the
dynamic threshold alpha(SoH) of Eq. 4 can be exercised on longer horizons.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .params import Params


@dataclass
class Battery:
    p: Params = field(default_factory=Params)
    soc: float = None
    throughput_kWh: float = 0.0

    def __post_init__(self):
        if self.soc is None:
            self.soc = self.p.soc0

    @property
    def capacity(self) -> float:
        return self.p.C0_kWh * (1.0 - self.p.delta_fade * self.throughput_kWh / (2.0 * self.p.C0_kWh))

    @property
    def soh(self) -> float:
        return self.capacity / self.p.C0_kWh

    @property
    def stored_kWh(self) -> float:
        return self.soc * self.capacity

    @property
    def usable_kWh(self) -> float:
        return max(0.0, (self.soc - self.p.soc_min) * self.capacity)

    def step(self, P_c_kW: float = 0.0, P_d_kW: float = 0.0) -> float:
        """Advance one step with charge and discharge powers (kW).

        Discharge is capped so that the state of charge does not fall below
        ``soc_min``.  Returns the energy actually drawn from the battery (kWh,
        before the discharge efficiency), which is what leaves the pledge.
        """
        dt, C = self.p.dt_h, self.capacity
        max_draw = self.usable_kWh
        draw = min(P_d_kW * dt / self.p.eta_d, max_draw)          # kWh removed from storage
        add = self.p.eta_c * P_c_kW * dt
        self.soc += (add - draw) / C
        self.soc = min(1.0, max(0.0, self.soc))
        self.throughput_kWh += add + draw
        return draw
