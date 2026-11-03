"""Unit tests for the protocol components against the equations of Section 4."""

import math

import numpy as np
import pytest

from cdpe import Params, Battery, Oracle, Vault
from cdpe.oracle import RejectingBreaker
from cdpe.price import simulate_spot, trajectory_seeds

P = Params()


# --- Eq. 1: battery -------------------------------------------------------------
def test_battery_discharge_uses_efficiency():
    b = Battery(P)
    draw = b.step(P_d_kW=1.0)                       # 1 kW for 15 min
    assert draw == pytest.approx(0.25 / P.eta_d)
    assert b.stored_kWh == pytest.approx(5.0 - 0.25 / P.eta_d)


def test_battery_charge_uses_efficiency():
    b = Battery(P)
    b.step(P_c_kW=2.0)
    assert b.stored_kWh == pytest.approx(5.0 + P.eta_c * 0.5)


def test_capacity_fade_with_throughput():
    p = P.with_(delta_fade=1e-3)
    b = Battery(p)
    for _ in range(40):
        b.step(P_d_kW=4.0)
    assert b.soh < 1.0 and b.capacity == pytest.approx(p.C0_kWh * b.soh)


# --- Eqs. 2-3: oracle -----------------------------------------------------------
def test_breaker_follows_a_crash_at_the_rate_limit():
    o = Oracle(P)
    o.update(0.0, 400.0)
    tilde = o._admit(0.25, 100.0)                    # -75 % in one step
    assert tilde == pytest.approx(400.0 * (1 - P.breaker_rate * 0.25))


def test_breaker_passes_small_moves_unchanged():
    o = Oracle(P)
    o.update(0.0, 400.0)
    assert o._admit(0.25, 410.0) == pytest.approx(410.0)


def test_twap_needs_six_observations_and_clips_at_cap():
    o = Oracle(P)
    for k in range(5):
        assert math.isnan(o.update(0.25 * k, 400.0))
    assert o.update(1.25, 400.0) == pytest.approx(400.0)
    o2 = Oracle(P.with_(p_esc=300.0))
    for k in range(6):
        o2.update(0.25 * k, 400.0)
    assert o2.value == pytest.approx(300.0)


def test_twap_window_is_24_hours():
    o = Oracle(P)
    for k in range(200):
        o.update(0.25 * k, 400.0)
    assert o.n_obs == int(24 / 0.25)


def test_rejecting_breaker_locks_on_stale_value():
    r, o = RejectingBreaker(P), Oracle(P)
    series = [400.0] * 100 + [150.0] * 100            # a sustained -62 % move
    for k, s in enumerate(series):
        r.update(0.25 * k, s); o.update(0.25 * k, s)
    assert r.rejected == 100 and r.value == pytest.approx(400.0)
    assert o.value < 200.0


# --- Eqs. 4-6: vault ------------------------------------------------------------
def test_minting_sets_rho0():
    v = Vault(P)
    debt = v.open(5.0, 400.0, 1.5)
    assert debt == pytest.approx(5.0 * 400.0 / 1.5)
    assert v.rho(400.0) == pytest.approx(1.5)


def test_mint_check_uses_dynamic_threshold():
    v = Vault(P); v.open(5.0, 400.0, 2.0)
    assert v.can_mint(0.0, 400.0, soh=1.0)
    assert not v.can_mint(400.0, 400.0, soh=1.0)
    assert not v.can_mint(0.0, 400.0, soh=0.7)        # alpha = 1.5/0.7 = 2.14 > 2.0


def test_debt_index_growth_over_a_week():
    v = Vault(P); v.open(5.0, 400.0, 1.5)
    for _ in range(P.n_steps):
        v.accrue(P.dt_h)
    assert v.phi_D - 1.0 == pytest.approx(7.7e-4, rel=0.02)


def test_liquidation_recovery_and_shortfall():
    v = Vault(P); v.open(5.0, 400.0, 1.5)              # debt 1333.3
    rec = v.check_liquidation(1, 0.25, p_ref=400.0, spot=400.0)
    assert rec is None                                 # rho = 1.5 >= 1.25
    rec = v.check_liquidation(2, 0.5, p_ref=320.0, spot=280.0)   # rho = 1.2
    assert rec is not None and v.liquidated
    assert rec.E_rec == pytest.approx(min(5.0, 1333.33 * 1.1 / 320.0), rel=1e-4)
    assert rec.shortfall == 0.0 and rec.unprofitable   # 4.58 kWh * 280 = 1283 < 1333
    v2 = Vault(P); v2.open(5.0, 400.0, 1.5)
    rec2 = v2.check_liquidation(3, 0.75, p_ref=200.0, spot=200.0)  # collateral worth 1000 < debt
    assert rec2.shortfall == pytest.approx(1333.33 - 1000.0, rel=1e-4)
    assert v2.surplus < 0                              # I4 breached


def test_i8_clamp_releases_pledge_on_discharge():
    v = Vault(P); v.open(5.0, 400.0, 1.5)
    v.clamp_to_stored(4.0)
    assert v.E_col == 4.0 and v.rho(400.0) == pytest.approx(1.2)


# --- price process --------------------------------------------------------------
def test_spot_is_reproducible_and_positive():
    t1, s1 = simulate_spot(123, P); t2, s2 = simulate_spot(123, P)
    assert np.array_equal(s1, s2) and (s1 > 0).all()
    assert t1[P.n_history] == 0.0 and len(t1) == P.n_history + P.n_steps + 1


def test_shock_scales_the_target():
    _, s0 = simulate_spot(7, P); _, s1 = simulate_spot(7, P, shock=-0.2, shock_day=3.5)
    k = P.n_history + int(3.5 * P.steps_per_day)
    assert np.allclose(s1[:k], s0[:k]) and np.allclose(s1[k:], 0.8 * s0[k:])


def test_trajectory_seeds_are_those_of_the_paper():
    seeds = trajectory_seeds(P)
    assert len(seeds) == 500 and int(seeds[0]) == 464507548
