"""Regression tests on the headline figures of Section 5.

These pin the numbers the repository produces so that a change in the code
that alters a result is caught.  Tolerances are stated explicitly.
"""

import numpy as np
import pytest

from cdpe import Params, run_trajectory, run_batch
from cdpe.simulate import batch_summary, evening_discharge
from cdpe.price import trajectory_seeds

P = Params()


@pytest.fixture(scope="module")
def baseline():
    return run_batch(P, rho0=P.rho0)


def test_trajectory_zero_without_discharge(baseline):
    r = baseline[0]
    assert r.liquidated and r.liquidation.t_h / 24 == pytest.approx(4.6, abs=0.05)


def test_baseline_envelope(baseline):
    s = batch_summary(baseline, P)
    assert s["liquidated"] == 15                     # manuscript: 14 (see VERIFICATION.md)
    assert s["rho_min_p05"] == pytest.approx(1.265, abs=0.002)
    assert s["shortfalls"] == 0
    assert s["pref_fall_max"] == pytest.approx(0.208, abs=0.005)
    assert s["pref_fall_mean"] == pytest.approx(0.077, abs=0.002)
    lo, hi = s["rho_at_liq_range"]
    assert 1.24 < lo and hi < 1.2501
    for k in ("I2", "I3", "I4", "I5", "I6", "I7", "I8"):
        assert s["invariants_held"][k] == 500


def test_conservative_never_liquidates():
    s = batch_summary(run_batch(P, rho0=P.rho0_conservative), P)
    assert s["liquidated"] == 0 and s["rho_min_min"] > 1.84
    assert s["invariants_held"]["I1"] == 500


@pytest.mark.parametrize("kW, rho_liq, shortfall", [
    (0.5, 1.220, 0.0), (1.0, 1.178, 0.0), (2.0, 1.177, 0.0),
    (3.0, 1.020, 0.0), (5.0, 1.097, 0.0), (8.0, 0.862, 13.8),
])
def test_collateral_channel_table3(kW, rho_liq, shortfall):
    seed0 = int(trajectory_seeds(P)[0])
    r = run_trajectory(seed0, P, rho0=P.rho0, dispatch=evening_discharge(kW))
    assert r.liquidated and r.liquidation.t_h < 24.0        # first evening
    assert r.liquidation.rho == pytest.approx(rho_liq, abs=0.002)
    assert r.liquidation.shortfall_pct == pytest.approx(shortfall, abs=0.1)


def test_conservative_8kW_shortfall():
    seed0 = int(trajectory_seeds(P)[0])
    r = run_trajectory(seed0, P, rho0=P.rho0_conservative, dispatch=evening_discharge(8.0))
    assert r.liquidation.shortfall_pct == pytest.approx(63.5, abs=0.2)


def test_shock_sweep_point():
    res = run_batch(P, rho0=P.rho0, shock=-0.15, shock_day=3.5)
    liqs = [r.liquidation for r in res if r.liquidation]
    assert 0.70 < len(liqs) / 500 < 0.78                      # manuscript: 71.4 %
    assert all(l.shortfall == 0 for l in liqs)                # price channel never produces bad debt
    assert sum(l.unprofitable for l in liqs) / len(liqs) > 0.4
