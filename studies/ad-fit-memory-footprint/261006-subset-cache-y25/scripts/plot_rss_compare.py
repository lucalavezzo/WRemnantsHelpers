#!/usr/bin/env python3
"""VmRSS vs time: the |Y|<=2.5 subset cache (SUBY25, plain rabbit_fit.py) against the full y35 cache (MEMNOM,
same command under memprobe.py, ../261006-memory-breakdown). Both: NOMSTIFF card, --noFit + postfit Hessian.
PRIMARY = VmRSS from /proc/<pid>/status (smaps_rollup is unreliable on kernel 5.14). MEMNOM's external sampler has a
60-130 s gap, filled by its in-process [memmark] rss values. Dashed = header-based steady-state predictions
(walk_pred.json). Time series, so bare matplotlib (wums plot_tools is for histograms).
"""
import argparse, csv, json, os, re, sys
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_memory_breakdown"
ap = argparse.ArgumentParser()
ap.add_argument("--sub-csv", default=f"{TASK}/logs/SUBY25.mem.csv")
ap.add_argument("--full-csv", default=f"{O}/sample_MEMNOM.csv")
ap.add_argument("--full-log", default=f"{O}/MEMNOM.log")
ap.add_argument("--pred", default=f"{TASK}/walk_pred.json")
ap.add_argument("--outdir", default=TASK)
ap.add_argument("--basename", default="rss_vs_time_subset_vs_full")
a = ap.parse_args()
G = 1024 / 1e9


def rows(p):
    return [r for r in csv.DictReader(open(p)) if (r["vmrss_kb"] or "").isdigit()]


rs = rows(a.sub_csv)
ts0 = int(rs[0]["t_unix"])
ts = [int(r["t_unix"]) - ts0 for r in rs]
ys = [int(r["vmrss_kb"]) * G for r in rs]
marks = [
    (int(m.group(1)), float(m.group(2)) * 2**30 / 1e9)
    for m in (
        re.search(r"\[memmark\] t=[\d.]+ unix=(\d+) phase=\S+ rss=([\d.]+)", l)
        for l in open(a.full_log)
    )
    if m
]
tf0 = marks[0][0]
rf = rows(a.full_csv)
pts = sorted(
    [(int(r["t_unix"]) - tf0, int(r["vmrss_kb"]) * G) for r in rf]
    + [(t - tf0, y) for t, y in marks]
)
P = json.load(open(a.pred))
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.plot(
    [p[0] for p in pts],
    [p[1] for p in pts],
    "-",
    color="tab:red",
    lw=1.5,
    label=f"full cache, 1050 bins (MEMNOM): steady 330.9, peak 335.3 GB",
)
ax.plot(
    ts,
    ys,
    "-",
    color="tab:blue",
    lw=1.5,
    label=f"|Y|<=2.5 subset, 770 bins (SUBY25): steady {ys[-2]:.1f}, peak {max(ys):.1f} GB",
)
for k, c in (("full", "tab:red"), ("y25", "tab:blue")):
    ax.axhline(P[k]["pred_total_GB"], ls="--", lw=1, color=c, alpha=0.6)
    ax.text(
        5,
        P[k]["pred_total_GB"] + 3,
        f"header prediction {P[k]['pred_total_GB']:.0f} GB "
        f"(rules {P[k]['blob_GB']:.1f} + muF caches {P[k]['nominal_muf_GB'] + P[k]['member_muf_GB']:.1f})",
        fontsize=8,
        color=c,
    )
ax.set_xlabel("time since process start [s]")
ax.set_ylabel("VmRSS [GB = 1e9 B]")
ax.set_title(
    "SCETlibADParamModel, NOMSTIFF card, --noFit + postfit Hessian: full y35 cache vs |Y|<=2.5 subset",
    fontsize=10,
)
ax.set_ylim(0, 380)
ax.grid(alpha=0.3)
ax.legend(loc="lower right", fontsize=8)
save_plot(
    outdir=a.outdir,
    basename=a.basename,
    fig=fig,
    args=a,
    meta_info={
        "note": "VmRSS from /proc/pid/status; MEMNOM under memprobe.py (marks fill its sampler gap), "
        "SUBY25 plain rabbit_fit.py; the two ran at different times with different node load"
    },
)
print("SUBY25 peak", max(ys), "last", ys[-1], "end t", ts[-1])
print("MEMNOM end t", pts[-1][0])
