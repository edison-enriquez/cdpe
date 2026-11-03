"""Figures 2 and 3 of the manuscript, from the outputs of the run_* scripts.

    results/fig_envelope.pdf|png    (a) median and 5-95 % band of rho(t) at the permitted
                                    leverage, without and with a -15 % shock at day 3.5, and
                                    the conservative median; (b) liquidated share vs shock at
                                    both leverages, and the share of liquidations unprofitable
                                    at the spot (rho0 = 1.50).
    results/fig_collateral.pdf|png  rho on the first evening for a prosumer discharging from
                                    18:00 at 1, 3 and 8 kW; solid = permitted leverage,
                                    dashed = conservative.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from _common import P, RESULTS

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.labelsize": 9, "legend.fontsize": 8,
    "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150,
})
C_BASE, C_SHOCK, C_CONS, C_UNPROF = "#1f4e79", "#c0504d", "#4f8a4f", "#7f7f7f"


def fig_envelope():
    paths = np.load(RESULTS / "baseline_rho_paths.npz")
    sweep = pd.read_csv(RESULTS / "shock_sweep.csv")
    t_d = paths["t_h"] / 24.0

    def band(arr):
        # a liquidated position keeps the ratio at which it was liquidated, so that
        # the band reflects liquidations instead of dropping them out of the sample
        a = arr.copy()
        for row in a:
            k = np.flatnonzero(np.isinf(row))
            if k.size:
                row[k] = row[k[0] - 1]
        return (np.percentile(a, 5, axis=0), np.median(a, axis=0), np.percentile(a, 95, axis=0))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.9))

    lo, med, hi = band(paths["baseline"])
    ax1.fill_between(t_d, lo, hi, color=C_BASE, alpha=0.18, lw=0)
    ax1.plot(t_d, med, color=C_BASE, lw=1.4, label=r"$\rho_0=1.50$, median and 5–95 %")
    lo, med, hi = band(paths["baseline_shock15"])
    ax1.fill_between(t_d, lo, hi, color=C_SHOCK, alpha=0.15, lw=0)
    ax1.plot(t_d, med, color=C_SHOCK, lw=1.4, label=r"$\rho_0=1.50$, $-15\,\%$ shock at day 3.5")
    _, med, _ = band(paths["conservative"])
    ax1.plot(t_d, med, color=C_CONS, lw=1.4, label=r"$\rho_0=2.327$, median")
    ax1.axhline(P.alpha_min, color="k", lw=0.7, ls=":")
    ax1.axhline(P.alpha_liq, color="k", lw=0.7, ls="--")
    ax1.text(7.05, P.alpha_min, r"$\alpha_{\min}$", va="center", fontsize=8)
    ax1.text(7.05, P.alpha_liq, r"$\alpha_\ell$", va="center", fontsize=8)
    ax1.set_xlim(0, 7); ax1.set_xlabel("day"); ax1.set_ylabel(r"collateralization ratio $\rho$")
    ax1.set_ylim(1.0, 3.0)
    ax1.legend(loc="upper left", frameon=False)
    ax1.set_title("(a) price envelope, 500 trajectories", loc="left", fontsize=9)

    for rho0, c, lab in ((P.rho0, C_BASE, r"$\rho_0=1.50$"), (P.rho0_conservative, C_CONS, r"$\rho_0=2.327$")):
        d = sweep[np.isclose(sweep.rho0, rho0)].sort_values("shock_pct")
        ax2.plot(-d.shock_pct, d.liquidated_pct, "o-", color=c, lw=1.4, ms=3.5, label=f"liquidated, {lab}")
    d = sweep[np.isclose(sweep.rho0, P.rho0)].sort_values("shock_pct")
    ax2.plot(-d.shock_pct, d.unprofitable_pct_of_liq, "s--", color=C_UNPROF, lw=1.2, ms=3,
             label=r"unprofitable at spot, % of liq. ($\rho_0=1.50$)")
    ax2.set_xlabel("permanent fall of the price target at day 3.5 [%]")
    ax2.set_ylabel("share [%]"); ax2.set_xlim(0, 50); ax2.set_ylim(0, 102)
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), frameon=False, ncol=1)
    ax2.set_title("(b) where the envelope ends", loc="left", fontsize=9)

    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(RESULTS / f"fig_envelope.{ext}", bbox_inches="tight")
    plt.close(fig)


def fig_collateral():
    paths = np.load(RESULTS / "discharge_paths.npz")
    t_h = paths["t_h"]
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    colors = {1.0: C_BASE, 3.0: C_CONS, 8.0: C_SHOCK}
    for kW, c in colors.items():
        for label, ls in (("baseline", "-"), ("conservative", "--")):
            r = np.where(np.isinf(paths[f"{label}_{kW}"]), np.nan, paths[f"{label}_{kW}"])
            ax.plot(t_h, r, ls=ls, color=c, lw=1.4,
                    label=(f"{kW:g} kW" if label == "baseline" else None))
    ax.axhline(P.alpha_liq, color="k", lw=0.7, ls="--"); ax.axhline(1.0, color="k", lw=0.7, ls=":")
    ax.text(22.1, P.alpha_liq, r"$\alpha_\ell$", va="center", fontsize=8)
    ax.text(22.1, 1.0, r"$\rho=1$", va="center", fontsize=8)
    ax.axvspan(18, 22, color="0.92", lw=0, zorder=0)
    ax.set_xlim(17, 22); ax.set_ylim(0.3, 2.5)
    ax.set_xticks(range(17, 23)); ax.set_xticklabels([f"{h}:00" for h in range(17, 23)])
    ax.set_xlabel("first evening"); ax.set_ylabel(r"collateralization ratio $\rho$")
    h, l = ax.get_legend_handles_labels()
    from matplotlib.lines import Line2D
    h += [Line2D([], [], color="k", ls="-"), Line2D([], [], color="k", ls="--")]
    l += [r"$\rho_0=1.50$", r"$\rho_0=2.327$"]
    ax.legend(h, l, loc="upper right", frameon=False, ncol=2)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(RESULTS / f"fig_collateral.{ext}", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_envelope(); print("written:", RESULTS / "fig_envelope.pdf")
    fig_collateral(); print("written:", RESULTS / "fig_collateral.pdf")
