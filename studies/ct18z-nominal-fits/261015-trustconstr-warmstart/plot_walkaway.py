#!/usr/bin/env python3
"""Loss vs iteration of trust-constr restarts on the toy (toy_warmstart.py,
seed 3, production tolerances): rabbit before this change (S0), scipy's start
with no row held (S1), and rabbit's warm start (S7 = centred barrier +
consistent slacks + no row held + dual-sign check).

  python plot_walkaway.py   (in the container, worktree on PYTHONPATH)
"""

import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import toy_grid as G  # noqa: E402
import toy_strategies as S  # noqa: E402
import toy_warmstart as T  # noqa: E402
from plot_output import save_plot  # noqa: E402


def history(p, x0, strat):
    if strat == "S7":
        from rabbit.constraints.warm_start import centred_barrier

        mu0 = centred_barrier(
            p["g"](x0),
            p["cval"](x0),
            p["cjac"](x0),
            p["lb"],
            np.full(len(p["lb"]), np.inf),
        )
        kw = dict(
            keep="none", slack="consistent", slack_floor=1e-3 * mu0, mu0=mu0, tol0=mu0
        )
        r, h = T.solve(p, x0, **G.PROD, **kw)
        ok, _ = S.dual_sign_ok(p, r.x)
        if not ok:
            r, h2 = T.solve(p, r.x, **G.PROD, **S.STRATS["S1 scipy-none"])
            h = h + h2
    else:
        r, h = T.solve(p, x0, **G.PROD, **S.STRATS[strat])
    return np.array([hh["fun"] for hh in h]), r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--outdir", default=os.path.dirname(os.path.abspath(__file__)))
    args = ap.parse_args()
    starts, info = G.build_starts(args.seed)
    panels = [
        ("at_min", "restart at the minimum"),
        ("on_face", "start exactly on the active faces"),
        ("toy0.1s_0", "start at the old minimum, data moved 0.1$\\sigma$"),
    ]
    labels = {
        "S0 rabbit-now": "before: rabbit keep_feasible rule, scipy start",
        "S1 scipy-none": "no row held, scipy start ($\\mu_0$=0.1, $s_0$=max(1.5(c-lb),1))",
        "S7": "warm start (this branch)",
    }
    colors = {"S0 rabbit-now": "#d62728", "S1 scipy-none": "#ff7f0e", "S7": "#1f77b4"}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), constrained_layout=True)
    meta = {"seed": args.seed, "cold": info}
    for ax, (sname, title) in zip(axes, panels):
        pseed, scale, itoy, x0 = starts[sname]
        p = (
            T.make_problem(seed=args.seed)
            if pseed is None
            else G.perturbed(pseed, scale, itoy)
        )
        (xs, fs), _ = G.reference(p, np.zeros(p["n"]))
        for strat in ("S0 rabbit-now", "S1 scipy-none", "S7"):
            f, r = history(p, x0, strat)
            y = np.concatenate([[p["f"](x0)], f]) - fs
            ax.plot(
                np.arange(len(y)), y, color=colors[strat], label=labels[strat], lw=1.6
            )
            meta[f"{sname}/{strat}"] = dict(
                nit=int(r.nit),
                status=int(r.status),
                f_end_minus_fstar=float(r.fun - fs),
            )
        ax.set_yscale("symlog", linthresh=1e-8)
        ax.axhline(0, color="k", lw=0.5)
        ax.set_xlabel("trust-constr iteration")
        ax.set_title(title, fontsize=11)
        ax.set_xlim(0, None)
    axes[0].set_ylabel("loss $-$ loss at the constrained minimum")
    axes[0].legend(fontsize=8, loc="upper right")
    fig.suptitle(
        "toy: 40 parameters, $\\kappa$=1e3, 8 rows (5 active); gtol 1e-8, xtol 1e-10, "
        "barrier_tol 1e-9",
        fontsize=10,
    )
    save_plot(
        outdir=args.outdir,
        basename="toy_restart_loss_vs_iteration",
        fig=fig,
        args=args,
        meta_info=meta,
    )


if __name__ == "__main__":
    main()
