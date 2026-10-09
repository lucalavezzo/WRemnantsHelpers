#!/usr/bin/env python3
"""Thread-scaling table + plots from the timestamped logs (run_ts.sh) and the /proc samples (sample_proc.sh).

Phases (all wall-clock from the per-line unix timestamps):
  load   "[scetlib_ad] loading cache" -> "cache loaded in"
  build  "cache loaded in" -> "[minimize] method="   (model build, priors, wall, first loss evaluation =
         the muF-cache build; checked against the RSS step)
  iters  "[minimize] method=" -> last "Iteration N:" line  (5 trust-krylov iterations, each = loss+grad + CG HVPs)
  hess   rabbit's own "[timing] loss_val_grad_hess() (postfit cov): X s"
CPU % = d(utime+stime)/CLK_TCK/dt*100 over each phase (100 % = one core), interpolated from the 5 s samples.
Usage: analyze.py PF [PF ...]   (outputs: table.json, table.md and the plots in the task dir)
"""
import argparse, csv, json, os, re, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_thread_scaling"
G = 1024 / 1e9  # kB -> GB(1e9)

ap = argparse.ArgumentParser()
ap.add_argument("pfs", nargs="+")
ap.add_argument("--outdir", default=TASK)
ap.add_argument("--noplot", action="store_true")
a = ap.parse_args()


def parse(pf):
    L = [l.rstrip("\n") for l in open(f"{O}/{pf}.log")]
    ts = lambda pat: [
        float(l.split()[0])
        for l in L
        if re.match(r"^\d{10}\.\d+ ", l) and re.search(pat, l)
    ]
    r = {
        "pf": pf,
        "threads": int(
            re.search(r"threads=(\d+)", open(f"{TASK}/cmds/{pf}.cmd").read()).group(1)
        ),
    }
    t0 = float(
        re.search(r"t0=([\d.]+)", next(l for l in L if "python pid" in l)).group(1)
    )
    r["load_start"], r["load_end"] = (
        ts(r"\[scetlib_ad\] loading cache")[0],
        ts(r"cache loaded in")[0],
    )
    r["min_start"] = ts(r"\[minimize\] method=")[0]
    it = [
        (float(l.split()[0]), int(m.group(1)), float(m.group(2)), float(m.group(3)))
        for l in L
        for m in [re.search(r"Iteration (\d+): loss (\S+)\s+\[dt=([\d.]+)s", l)]
        if m
    ]
    r["n_iter"] = len(it)
    r["iter_dt"] = [x[3] for x in it]
    r["iter_loss_rel"] = [
        x[2] - it[0][2] for x in it
    ]  # loss differences only (no absolute values)
    r["iter_end"] = it[-1][0]
    h = [l for l in L if "loss_val_grad_hess() (postfit cov)" in l]
    r["hess_s"] = float(re.search(r"cov\): ([\d.]+) s", h[0]).group(1)) if h else None
    r["hess_end"] = float(h[0].split()[0]) if h else None
    tot = [l for l in L if "seconds total time" in l]
    r["total_s"] = (
        float(re.search(r"([\d.]+) seconds total", tot[0]).group(1)) if tot else None
    )
    r["t0"] = t0
    # wall from python start to the end of the Hessian (rabbit's "total time" is missing when the job dies after
    # the Hessian: at the kicked start the Hessian is not positive-definite and the covariance step raises)
    r["wall_to_hess_end_s"] = (r["hess_end"] - t0) if h else None
    r["load_s"] = r["load_end"] - r["load_start"]
    r["start_to_load_s"] = r["load_start"] - t0
    r["build_s"] = r["min_start"] - r["load_end"]
    r["iters_s"] = r["iter_end"] - r["min_start"]
    r["per_iter_s"] = r["iters_s"] / max(1, r["n_iter"])
    # /proc samples
    rows = [
        x
        for x in csv.DictReader(open(f"{O}/{pf}.proc.csv"))
        if (x.get("vmrss_kb") or "").isdigit()
    ]
    t = np.array([float(x["t_unix"]) for x in rows])
    rss = np.array([int(x["vmrss_kb"]) for x in rows]) * G
    hwm = np.array([int(x["vmhwm_kb"]) for x in rows]) * G
    thr = np.array([int(x["threads"]) for x in rows])
    tick = np.array([float(x["cpu_ticks"]) for x in rows])
    load = np.array([float(x["load1"]) for x in rows])
    r["peak_rss_GB"] = float(hwm.max())

    def window(a_, b_):
        return (t >= a_) & (t <= b_)

    hs = r["hess_end"] - r["hess_s"] if h else None
    w = window(r["min_start"], r["hess_end"] if h else t[-1])
    r["steady_rss_GB"] = float(np.median(rss[w])) if w.any() else None
    r["rss_after_load_GB"] = float(np.interp(r["load_end"], t, rss))
    r["rss_at_min_start_GB"] = float(np.interp(r["min_start"], t, rss))
    r["nlwp_max"] = int(thr.max())
    r["nlwp_steady"] = int(np.median(thr[w])) if w.any() else None
    r["load_mean"] = float(load.mean())
    r["load_range"] = [float(load.min()), float(load.max())]

    def cpu(a_, b_):
        if a_ is None or b_ is None or b_ - a_ < 5:
            return None
        return float(
            (np.interp(b_, t, tick) - np.interp(a_, t, tick)) / 100.0 / (b_ - a_) * 100
        )

    def lavg(a_, b_):
        w_ = window(a_, b_)
        return float(load[w_].mean()) if w_.any() else float(np.interp(a_, t, load))

    r["load_build"] = lavg(r["load_end"], r["min_start"])
    r["load_iters"] = lavg(r["min_start"], r["iter_end"])
    r["load_hess"] = lavg(hs, r["hess_end"]) if h else None
    r["cpu_load"] = cpu(r["load_start"], r["load_end"])
    r["cpu_build"] = cpu(r["load_end"], r["min_start"])
    r["cpu_iters"] = cpu(r["min_start"], r["iter_end"])
    r["cpu_hess"] = cpu(hs, r["hess_end"]) if h else None
    r["coresec_iters"] = r["cpu_iters"] / 100 * r["iters_s"]
    r["coresec_hess"] = r["cpu_hess"] / 100 * r["hess_s"] if h else None
    r["_series"] = {
        "t": (t - t0).tolist(),
        "rss": rss.tolist(),
        "thr": thr.tolist(),
        "cpu": (np.gradient(tick, t) if len(t) > 2 else np.zeros_like(t)).tolist(),
    }
    return r


R = [parse(pf) for pf in a.pfs]
R.sort(key=lambda r: (r["threads"], r["pf"]))
f = lambda v, fmt: "n/a" if v is None else format(v, fmt)
hdr = (
    "| run | threads= | load avg build / iters / Hessian | cache load [s] | build + 1st eval [s] | 5 iters [s] (per iter) "
    "| Hessian [s] | start -> Hessian done [s] | peak / steady RSS [GB] | nlwp | cores busy build / iters / Hessian "
    "| core-s iters / Hessian |"
)
lines = [hdr, "|" + "---|" * (hdr.count("|") - 1)]
for r in R:
    lines.append(
        f"| {r['pf']} | {r['threads']} | {r['load_build']:.0f} / {r['load_iters']:.0f} / {f(r['load_hess'], '.0f')} "
        f"| {r['load_s']:.0f} | {r['build_s']:.0f} "
        f"| {r['iters_s']:.0f} ({r['per_iter_s']:.0f}) | {f(r['hess_s'], '.0f')} | {f(r['wall_to_hess_end_s'], '.0f')} "
        f"| {r['peak_rss_GB']:.1f} / {f(r['steady_rss_GB'], '.1f')} | {r['nlwp_max']} "
        f"| {r['cpu_build']/100:.0f} / {r['cpu_iters']/100:.0f} / {f(r['cpu_hess'] and r['cpu_hess']/100, '.0f')} "
        f"| {r['coresec_iters']:.0f} / {f(r['coresec_hess'], '.0f')} |"
    )
md = "\n".join(lines)
print(md)
for r in R:
    print(
        r["pf"],
        "iter dt:",
        r["iter_dt"],
        "dloss:",
        ["%.3g" % x for x in r["iter_loss_rel"]],
        "cpu load/build:",
        f(r["cpu_load"], ".0f"),
        f(r["cpu_build"], ".0f"),
        "rss@load_end/min_start:",
        "%.1f %.1f" % (r["rss_after_load_GB"], r["rss_at_min_start_GB"]),
    )
json.dump(
    [{k: v for k, v in r.items() if k != "_series"} for r in R],
    open(f"{a.outdir}/table.json", "w"),
    indent=1,
)
open(f"{a.outdir}/table.md", "w").write(md + "\n")
if a.noplot:
    sys.exit()

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from plot_output import save_plot

# Not histograms: scalar-vs-threads and time series, so bare matplotlib (wums plot_tools is for hists).
meta = {
    "inputs": " ".join(f"{O}/{r['pf']}.log" for r in R),
    "caveat": "shared node (load avg in the table); one run per point except the repeat; cache load is I/O bound",
}
Rm = [r for r in R if r["pf"] == f"TS{r['threads']}"]  # the scan
Rr = [
    r for r in R if r["pf"] != f"TS{r['threads']}"
]  # repeats: hollow markers, not joined
th = np.array([r["threads"] for r in Rm])
ticks = sorted(set(r["threads"] for r in R))


def series(ax_, key, lab, mk, c, scale=1.0):
    y = np.array([np.nan if r[key] is None else r[key] * scale for r in Rm], float)
    ax_.plot(th, y, mk + "-", color=c, label=lab)
    for r in Rr:
        if r[key] is not None:
            ax_.plot([r["threads"]], [r[key] * scale], mk, mfc="none", color=c, ms=9)


def axfmt(ax_, ylab, title, logy=True, base=10):
    ax_.set_xscale("log", base=2)
    ax_.set_xticks(ticks)
    ax_.set_xticklabels(ticks)
    if logy:
        ax_.set_yscale("log", base=base)
    ax_.set_xlabel("param-model threads=")
    ax_.set_ylabel(ylab)
    ax_.grid(alpha=0.3, which="both")
    ax_.legend(fontsize=7)
    ax_.set_title(title, fontsize=10)


C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))
for k, (key, lab, mk) in enumerate(
    (
        ("load_s", "cache load (TS128: cold page cache)", "s"),
        ("build_s", "build + first eval", "^"),
        ("iters_s", "5 trust-krylov iterations", "o"),
        ("hess_s", "postfit Hessian", "D"),
        ("wall_to_hess_end_s", "python start -> Hessian done", "x"),
    )
):
    series(ax[0], key, lab, mk, C[k])
ax[0].plot(
    ticks,
    [223 * 128 / t for t in ticks],
    ":",
    color=C[3],
    lw=1,
    label="Hessian, ideal 1/threads from TS128",
)
axfmt(ax[0], "wall time [s]", "wall time (hollow = TS128r repeat, node load 530-630)")
for k, (key, lab, mk) in enumerate(
    (
        ("cpu_build", "build+1st eval", "^"),
        ("cpu_iters", "iterations", "o"),
        ("cpu_hess", "Hessian", "D"),
    )
):
    series(ax[1], key, lab, mk, C[k + 1], 0.01)
ax[1].plot(ticks, ticks, "k:", lw=1, label="= threads")
axfmt(ax[1], "cores busy (CPU time / wall)", "CPU utilisation per phase", base=2)
for k, (key, lab, mk) in enumerate(
    (("coresec_iters", "5 iterations", "o"), ("coresec_hess", "Hessian", "D"))
):
    series(ax[2], key, lab, mk, C[k + 2])
axfmt(ax[2], "CPU core-seconds", "cost = CPU time per phase (flat = perfect scaling)")
fig.suptitle(
    "SCETlib-AD rabbit fit (NOMSTIFF card, |Y|<=2.5 subset cache, shared 384-core / 768-thread node): "
    "scaling with threads=",
    fontsize=10,
)
fig.tight_layout()
save_plot(outdir=a.outdir, basename="time_vs_threads", fig=fig, args=a, meta_info=meta)

plt.rcdefaults()  # wums (imported inside save_plot) switches on its own style; keep both figures alike
fig, ax = plt.subplots(1, 2, figsize=(12, 4.8))
for r in R:
    s = r["_series"]
    ax[0].plot(s["t"], s["rss"], lw=1.2, label=f"{r['pf']} (threads={r['threads']})")
ax[0].set_xlabel("time since python start [s]")
ax[0].set_ylabel("VmRSS [GB = 1e9 B]")
ax[0].grid(alpha=0.3)
ax[0].legend(fontsize=8)
ax[0].set_title("VmRSS vs time (/proc/pid/status)", fontsize=10)
series(ax[1], "peak_rss_GB", "peak (VmHWM)", "o", C[0])
series(ax[1], "steady_rss_GB", "steady (median over iterations + Hessian)", "s", C[1])
axfmt(ax[1], "RSS [GB = 1e9 B]", "", logy=False)
lo = min(r["steady_rss_GB"] or r["peak_rss_GB"] for r in R)
ax[1].set_ylim(lo - 20, max(r["peak_rss_GB"] for r in R) + 20)
ax[1].set_title("RSS vs threads=", fontsize=10)
fig.tight_layout()
save_plot(outdir=a.outdir, basename="rss_vs_threads", fig=fig, args=a, meta_info=meta)
