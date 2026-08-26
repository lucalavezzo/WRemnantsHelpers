#!/usr/bin/env python3
"""Busy-core trace of a cache build, stage by stage.

Not a histogram, so wums.plot_tools does not apply: this is a 1 Hz time series of
running threads / CPU rate sampled from /proc.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def load(p):
    t, c = [], []
    for line in open(p).read().splitlines()[1:]:
        f = line.split(",")
        if len(f) < 4 or not f[3]:
            continue
        t.append(float(f[0])); c.append(float(f[3]))
    return np.array(t), np.array(c)


runs = [
    (sys.argv[1], "A: 50 bins, qT 20-100 (uniform cost)",
     [(0, 71, "node set"), (71, 583, "bin rules"),
      (583, 859, "resummed members (20)"), (859, 1753, "fixed-order members (20)")]),
    (sys.argv[2], "B: 50 bins, qT 1-2 / 5-6 / 10-11 / 16-18 / 44-100 (3.3x cost spread)",
     [(0, 215, "node set"), (215, 889, "bin rules"),
      (889, 1183, "resummed members (20)"), (1186, None, "fixed-order members (20)")]),
]
NT = 48
fig, axes = plt.subplots(len(runs), 1, figsize=(11, 7.2), sharex=False)
for ax, (path, title, stages) in zip(np.atleast_1d(axes), runs):
    t, c = load(path)
    ax.plot(t, c, lw=0.8, color="#1f4e79")
    ax.axhline(NT, ls="--", lw=0.9, color="#888", label=f"--threads {NT}")
    cols = ["#dfeaf4", "#f4ead6", "#e6f0dd", "#f7dede"]
    for i, (a, b, lab) in enumerate(stages):
        b = t[-1] if b is None else b
        m = (t >= a) & (t <= b)
        if not m.any():
            continue
        ax.axvspan(a, b, color=cols[i % 4], zorder=0)
        ax.text((a + min(b, t[-1])) / 2, NT * 1.12,
                f"{lab}\n{c[m].mean()/NT*100:.0f}% of pool",
                ha="center", va="bottom", fontsize=7.5)
    ax.set_ylim(0, NT * 1.42)
    ax.set_xlim(0, t[-1])
    ax.set_ylabel("busy cores")
    ax.set_title(title, fontsize=9.5, loc="left")
    ax.legend(fontsize=7, loc="lower right")
    ax.grid(alpha=0.25, lw=0.4)
np.atleast_1d(axes)[-1].set_xlabel("seconds since build start")
fig.suptitle(
    "SCETlib autodiff cache build: where the thread pool actually idles\n"
    "one pool drain per member in BOTH member stages -- 8 s of a 14 s resummed step, "
    "2 s of a 45 s fixed-order step;\nweighted by cost that is ~7%, not the inferred 27%. "
    "A bin-cost spread costs more, and it costs it in the NODE-SET stage (B, 87%).",
    fontsize=9.5)
fig.tight_layout(rect=[0, 0, 1, 0.93])
for ext in ("png", "pdf"):
    fig.savefig(f"{sys.argv[3]}/build_utilisation.{ext}", dpi=140)
print("saved")
