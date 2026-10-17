#!/usr/bin/env python3
"""q still to go (= 2*(loss - final)) vs wall time and vs iteration, for saturated ptll sub-fits.

Each run = NAME=LOG[:leg][@final]. leg defaults to the LAST minimisation leg in the log (the sub-fit),
final defaults to the lowest loss seen (a running fit is then measured against its own best so far).
Run in the container (needs wums):  python3 plot_subfits.py --runs LAT=/path/LAT.log ... --outdir <taskdir>
"""
import argparse, os, sys
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_tc_log import parse
from plot_output import save_plot

ap = argparse.ArgumentParser()
ap.add_argument("--runs", nargs="+", required=True)
ap.add_argument("--outdir", required=True)
ap.add_argument("--basename", default="subfit_progress")
ap.add_argument("--title", default="")
args = ap.parse_args()

fig, axs = plt.subplots(1, 3, figsize=(19, 5.5))
for spec in args.runs:
    name, rest = spec.split("=", 1)
    final = None
    if "@" in rest:
        rest, final = rest.rsplit("@", 1)
        final = float(final)
    leg = -1
    if ":" in rest.split("/")[-1]:
        rest, leg = rest.rsplit(":", 1)
        leg = int(leg)
    legs = parse(rest)
    if not legs:
        print("no legs in", rest)
        continue
    L = legs[leg]
    loss = np.array([r["loss"] for r in L])
    el = np.array([r["el"] for r in L]) / 3600.0
    it = np.array([r["it"] for r in L])
    dt = np.array([r["dt"] for r in L])
    f = final if final is not None else loss.min()
    q = np.maximum(2 * (loss - f), 1e-7)
    (l,) = axs[0].plot(
        el, q, "-", lw=1.4, label=f"{name} ({len(L)-1} it, {el[-1]:.2f} h)"
    )
    axs[1].plot(it, q, "-", lw=1.4, color=l.get_color())
    axs[2].plot(it, dt, ".", ms=4, color=l.get_color())
    if "mu" in L[0]:
        mu = np.array([r.get("mu", np.nan) for r in L])
        cuts = np.where(np.diff(mu) < 0)[0] + 1
        if len(cuts):
            axs[1].plot(it[cuts], q[cuts], "|", ms=12, color=l.get_color())
for a in axs[:2]:
    a.set_yscale("log")
    a.set_ylabel("q still to go = 2 (loss - final)")
    a.grid(alpha=0.3)
axs[0].set_xlabel("wall time [h]")
axs[1].set_xlabel("iteration")
axs[1].text(
    0.02,
    0.02,
    "| = barrier parameter cut (trust-constr)",
    transform=axs[1].transAxes,
    fontsize=9,
)
axs[2].set_yscale("log")
axs[2].set_xlabel("iteration")
axs[2].set_ylabel("dt per iteration [s]")
axs[2].grid(alpha=0.3)
axs[0].legend(fontsize=8)
if args.title:
    fig.suptitle(args.title, fontsize=10)
fig.tight_layout()
save_plot(
    outdir=args.outdir,
    basename=args.basename,
    fig=fig,
    args=args,
    meta_info={
        "note": "wall times depend on node load; compare HVP counts for like-for-like"
    },
)
