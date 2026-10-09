#!/usr/bin/env python3
"""Diagnosis 2/3 from the logs alone: accept/reject structure, gain ratios, per-iteration time split.

Reads logs_parsed.json (scripts/parse_logs.py). For trust-krylov fits:
  * n accepted / rejected, longest rejection run;
  * the ratio of successive accepted gains with no rejection in between: ~2.0 means the
    trust radius doubled and the step is radius-limited in the LINEAR regime (gain ~ |g|*Delta);
  * dt after a rejected step (scipy reuses the trlib Krylov space: ~ one loss+grad) vs after an
    accepted step (fresh Lanczos: loss+grad + n_HVP * t_HVP);
  * "crawl" windows: >= 30 iterations whose total gain is < 1e-3 while the loss is still
    > 1e-3 above the fit's final loss.
For trust-constr fits: barrier stages (iterations at each mu), tr_radius, optimality, dt.
Writes log_analysis.json and prints a summary.
"""
import json
import os

import numpy as np

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(f"{TASK}/logs_parsed.json"))


def runs(mask):
    out, n = [], 0
    for m in mask:
        if m:
            n += 1
        elif n:
            out.append(n)
            n = 0
    if n:
        out.append(n)
    return out


def krylov(name, rows):
    rows = (
        [r for r in rows if r["restart"] == rows[-1]["restart"]]
        if name != "CENS03R"
        else rows
    )
    it = np.array([r["it"] for r in rows])
    loss = np.array([r["loss"] for r in rows])
    dt = np.array([r["dt"] for r in rows])
    acc = np.array([r["accepted"] for r in rows])
    final = loss.min()
    rej = ~acc[1:]
    rej_runs = runs(rej)
    # dt classified by the PREVIOUS iteration's outcome (what the solve at this iteration reuses)
    prev_acc = np.r_[
        True, acc[1:-1]
    ]  # iteration k>=1: was k-1 accepted (k-1 = 0 counts as fresh)
    dt1 = dt[1:]
    dt_after_rej = dt1[~prev_acc]
    dt_after_acc = dt1[prev_acc]
    # successive accepted gains with no rejection between
    gains = np.r_[0, -np.diff(loss)]
    ratios = []
    for k in range(2, len(loss)):
        if acc[k] and acc[k - 1] and gains[k - 1] > 0:
            ratios.append(gains[k] / gains[k - 1])
    ratios = np.array(ratios)
    # crawl windows
    W = 30
    crawl = []
    k = 1
    while k + W < len(loss):
        if loss[k] - loss[k + W] < 1e-3 and loss[k + W] - final > 1e-3:
            j = k + W
            while (
                j + 1 < len(loss)
                and loss[k] - loss[j + 1] < 1e-3 * (j + 1 - k) / W
                and loss[j + 1] - final > 1e-3
            ):
                j += 1
            seg = slice(k, j + 1)
            crawl.append(
                dict(
                    start=int(it[k]),
                    end=int(it[j]),
                    above_final=float(loss[k] - final),
                    gain_per_it=float((loss[k] - loss[j]) / (j - k)),
                    frac_rejected=float(np.mean(~acc[seg])),
                    frac_doubling=float(
                        np.mean(
                            np.abs(
                                np.log2(
                                    np.clip(
                                        [
                                            gains[m] / gains[m - 1]
                                            for m in range(k + 1, j + 1)
                                            if acc[m]
                                            and acc[m - 1]
                                            and gains[m - 1] > 0
                                        ]
                                        or [1.0],
                                        1e-12,
                                        None,
                                    )
                                )
                            )
                            - 1
                            < 0.15
                        )
                    ),
                    hours=float(dt[seg].sum() / 3600),
                )
            )
            k = j + 1
        else:
            k += 1
    return dict(
        n=len(loss),
        accepted=int(acc[1:].sum()),
        rejected=int(rej.sum()),
        longest_rej_run=int(max(rej_runs) if rej_runs else 0),
        rej_run_hist=(
            {str(n): int(c) for n, c in zip(*np.unique(rej_runs, return_counts=True))}
            if rej_runs
            else {}
        ),
        dt_after_rej_median=(
            float(np.median(dt_after_rej)) if len(dt_after_rej) else None
        ),
        dt_after_acc_median=(
            float(np.median(dt_after_acc)) if len(dt_after_acc) else None
        ),
        dt_after_rej_p10=(
            float(np.percentile(dt_after_rej, 10)) if len(dt_after_rej) else None
        ),
        dt_after_acc_p90=(
            float(np.percentile(dt_after_acc, 90)) if len(dt_after_acc) else None
        ),
        hours=float(dt.sum() / 3600),
        frac_time_after_acc=float(dt_after_acc.sum() / dt1.sum()),
        gain_ratio_frac_near2=(
            float(np.mean(np.abs(ratios - 2) < 0.2)) if len(ratios) else None
        ),
        gain_ratio_frac_near1=(
            float(np.mean(np.abs(ratios - 1) < 0.2)) if len(ratios) else None
        ),
        n_ratios=len(ratios),
        crawl=crawl,
        start_above_final=float(loss[0] - final),
    )


def tconstr(name, rows):
    mu = np.array([r.get("mu", np.nan) for r in rows])
    tr = np.array([r.get("tr", np.nan) for r in rows])
    opt = np.array([r.get("opt", np.nan) for r in rows])
    dt = np.array([r["dt"] for r in rows])
    loss = np.array([r["loss"] for r in rows])
    stages = []
    for m in np.unique(mu[~np.isnan(mu)])[::-1]:
        sel = mu == m
        idx = np.where(sel)[0]
        stages.append(
            dict(
                mu=float(m),
                iters=int(sel.sum()),
                first=int(idx[0]),
                last=int(idx[-1]),
                opt_end=float(opt[idx[-1]]),
                hours=float(dt[sel].sum() / 3600),
                dt_median=float(np.median(dt[sel])),
                tr_end=float(tr[idx[-1]]),
                loss_end=float(loss[idx[-1]]),
            )
        )
    return dict(
        n=len(rows),
        stages=stages,
        dt_median=float(np.median(dt[1:])),
        hours=float(dt.sum() / 3600),
        dt_first50_median=float(np.median(dt[1:51])),
        dt_last100_median=float(np.median(dt[-100:])),
        tr_min=float(np.nanmin(tr)),
        tr_max=float(np.nanmax(tr)),
    )


out = {}
for name, d in D.items():
    rows = d["rows"]
    if name.startswith("TC"):
        out[name] = tconstr(name, rows)
    else:
        out[name] = krylov(name, rows)
json.dump(out, open(f"{TASK}/log_analysis.json", "w"), indent=1)
print(
    "| fit | iters | acc | rej | longest rej run | h | dt|rej (s) | dt|acc (s) | time after acc | gain ratio ~2 | ~1 | crawls (start-end: above final, gain/it, rej frac, doubling frac, h) |"
)
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for name, r in out.items():
    if name.startswith("TC"):
        continue
    cr = "; ".join(
        f"{c['start']}-{c['end']}: +{c['above_final']:.3g}, {c['gain_per_it']:.1e}/it, rej {c['frac_rejected']:.2f}, dbl {c['frac_doubling']:.2f}, {c['hours']:.1f} h"
        for c in r["crawl"]
    )
    print(
        f"| {name} | {r['n']} | {r['accepted']} | {r['rejected']} | {r['longest_rej_run']} | {r['hours']:.1f} | "
        f"{r['dt_after_rej_median']:.0f} | {r['dt_after_acc_median']:.0f} | {r['frac_time_after_acc']:.2f} | "
        f"{r['gain_ratio_frac_near2'] or 0:.2f} | {r['gain_ratio_frac_near1'] or 0:.2f} | {cr} |"
    )
for name, r in out.items():
    if not name.startswith("TC"):
        continue
    print(
        f"\n{name}: {r['n']} it, {r['hours']:.1f} h, dt median {r['dt_median']:.0f} s (first 50: {r['dt_first50_median']:.0f}, last 100: {r['dt_last100_median']:.0f}), tr in [{r['tr_min']:.3g},{r['tr_max']:.3g}]"
    )
    for s in r["stages"]:
        print(
            f"   mu={s['mu']:.2e}: {s['iters']} it ({s['first']}-{s['last']}), {s['hours']:.1f} h, dt med {s['dt_median']:.0f} s, opt_end {s['opt_end']:.3g}, tr_end {s['tr_end']:.3g}, loss_end {s['loss_end']:.4f}"
        )
