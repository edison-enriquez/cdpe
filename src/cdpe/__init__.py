"""cdpe_v2 -- single-position simulator for the Collateralized Debt Position of Energy (CDPE).

This package reproduces Section 5 ("Validation of a single position") of

    Enríquez Ceballos, E. F., Nieto Londoño, R. D., Revelo Fuelagán, J., Bautista Loza, O. D.
    Collateralized energy positions for community battery storage: mechanism design and assessment.

Modules
-------
params      Protocol and simulation parameters (Section 4 and Section 5.1).
price       Log-Ornstein--Uhlenbeck spot process with diurnal cycle (Section 5.1).
oracle      Rate-limiting circuit breaker and 24-hour reference price (Eqs. 3--4).
battery     State of charge, capacity fade (Eq. 2).
vault       Collateralization ratio, debt index, liquidation (Eqs. 5--7).
invariants  Per-step checks of I1--I8 (Section 3.2).
simulate    One trajectory of one position; experiment drivers.
"""

from .params import Params, DEFAULT
from .price import simulate_spot
from .oracle import Oracle
from .battery import Battery
from .vault import Vault, LiquidationRecord
from .invariants import InvariantTracker
from .simulate import run_trajectory, run_batch, TrajectoryResult

__version__ = "2.0.1"
__all__ = [
    "Params", "DEFAULT", "simulate_spot", "Oracle", "Battery", "Vault",
    "LiquidationRecord", "InvariantTracker", "run_trajectory", "run_batch",
    "TrajectoryResult",
]
