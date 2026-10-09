#!/usr/bin/env python3
"""RSS vs time of the instrumented MEMNOM job, with phase bands from the in-process [memmark] lines,
and the predicted component stack (from walk_rules.py) as horizontal reference lines.
PRIMARY curve = VmRSS from /proc/<pid>/status (external sampler, 5 s). smaps_rollup is NOT used (unreliable on 5.14).
"""
import argparse, csv, json, os, re, sys
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot

O = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_memory_breakdown"
ap = argparse.ArgumentParser()
ap.add_argument("--log", default=f"{O}/MEMNOM.log")
ap.add_argument("--csv", default=f"{O}/sample_MEMNOM.csv")
ap.add_argument("--walk", default=f"{O}/walk_y35.json")
ap.add_argument(
    "--outdir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
ap.add_argument("--basename", default="rss_vs_time_MEMNOM")
a = ap.parse_args()
GB = 1024 / 1e9  # kB -> GB(1e9)
rows = [r for r in csv.DictReader(open(a.csv)) if (r["vmrss_kb"] or "").isdigit()]
marks = []
for line in open(a.log):
    m = re.search(
        r"\[memmark\] t=([\d.]+) unix=(\d+) phase=(\S+) rss=([\d.]+) hwm=([\d.]+)", line
    )
    if m:
        marks.append(
            (
                int(m.group(2)),
                m.group(3),
                float(m.group(4)) * 2**30 / 1e9,
                float(m.group(5)) * 2**30 / 1e9,
            )
        )
t0 = marks[0][0]
t = [int(r["t_unix"]) - t0 for r in rows]
rss = [int(r["vmrss_kb"]) * GB for r in rows]
hwm = [int(r["vmhwm_kb"]) * GB for r in rows]


def span(name):
    b = [m[0] for m in marks if m[1] == f"{name}:begin"]
    e = [m[0] for m in marks if m[1] == f"{name}:end"]
    return (b[0] - t0, e[0] - t0) if b and e else None


phases = [
    ("ScetlibADXsec_init#0", "cache load (rules + fo)", "tab:blue"),
    (
        "sl.values_and_jacobian#0",
        "1st value+jacobian (muF fit caches allocated)",
        "tab:orange",
    ),
    ("scale_envelope#0", "scale envelope", "tab:green"),
    ("Fitter.loss_val_grad_hess#0", "postfit Hessian", "tab:red"),
]
fig, ax = plt.subplots(figsize=(10, 5.5))
for key, lab, c in phases:
    s = span(key)
    if s:
        ax.axvspan(s[0], max(s[1], s[0] + 2), color=c, alpha=0.15, label=lab)
ax.plot(t, rss, "k-", lw=1.5, label="VmRSS (/proc/pid/status, 5 s)")
ax.plot(
    [m[0] - t0 for m in marks],
    [m[2] for m in marks],
    "k.",
    ms=3,
    label="in-process phase marks",
)
w = json.load(open(a.walk))
blob = w["total_bytes"] / 1e9
S = sum(p["nsites"] for p in w["per_rule"])
SV = sum(p["nsites"] * p["nv"] for p in w["per_rule"])
nom = S * 736 * 6 * 8 / 1e9
var = SV * 460 * 4 * 4 / 1e9
base = 1.0
lv = [
    (base + blob, f"pred: baseline + rules blob ({blob:.1f} GB)"),
    (base + blob + nom, f"+ nominal muF fits ({nom:.1f} GB)"),
    (base + blob + nom + var, f"+ member-row muF fits ({var:.1f} GB)"),
]
for y, lab in lv:
    ax.axhline(y, ls="--", lw=1, color="gray")
    ax.text(
        ax.get_xlim()[1] if False else t[-1] * 0.55,
        y + 3,
        lab,
        fontsize=8,
        color="dimgray",
    )
ax.set_xlabel("time since start [s]")
ax.set_ylabel("resident memory [GB = 1e9 B]")
ax.set_title(
    "SCETlibADParamModel, pdf62_y35_260921/merged_full_bin0xzero, --noFit + Hessian (NOMSTIFF card)",
    fontsize=10,
)
ax.set_ylim(0, max(rss) * 1.15)
ax.legend(loc="lower right", fontsize=8)
ax.grid(alpha=0.3)
save_plot(
    outdir=a.outdir,
    basename=a.basename,
    fig=fig,
    args=a,
    meta_info={
        "note": "VmRSS from /proc/pid/status; smaps_rollup unreliable on kernel 5.14 for allocating processes",
        "predicted_rules_GB": blob,
        "predicted_nominal_muf_GB": nom,
        "predicted_member_muf_GB": var,
    },
)
print("peak VmRSS GB", max(rss), "final", rss[-1])
