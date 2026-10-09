#!/usr/bin/env python3
"""Where does the projected-ptll saturated sub-fit spend its time?  Pure log parsing, no TF, no cache.

For SATB8 (relu2, unseeded), SATB8SA (relu2, --saturatedSeed scope all) and SATC2 (C2 wall, unseeded, may be live):
  * per iteration: loss, dt, accepted (loss strictly decreased), fresh (the previous iteration was accepted, or it is
    iteration 0, so scipy built a NEW trlib subproblem and paid its Lanczos HVPs; after a rejection the subproblem is
    hot-started and dt ~ one loss+grad).
  * t_f  = median dt of hot-started iterations (one loss+grad);  t_h = (sum dt - n_f t_f) / n_hvp with n_f, n_hvp from
    scipy's final counters (nfev, nhev) where the run has finished; estimated HVPs per fresh iteration = (dt - t_f)/t_h.
  * time spent by "q still to go" = 2 (loss - final) bands, the quantity that matters for a p-value.
Writes cost_breakdown.json and prints a markdown table.
"""
import json
import os
import re

import numpy as np

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
LOGS = {
    "SATB8": f"{C}/261007_lattice_term_native/SATB8.log",
    "SATB8SA": f"{C}/261007_lattice_term_native/SATB8SA.log",
    "SATC2": f"{C}/261008_c2_wall_test/SATC2.log",
    "SATP": f"{C}/261008_saturated_subfit_diag/SATP.log",
}
START = {
    "SATB8": 376.6751,
    "SATB8SA": 376.6751,
    "SATC2": 376.6751,
    "SATP": 376.6751,
}  # main (LATB8) loss = sub-fit warm start
ANSI = re.compile(r"\x1b\[[0-9;]*m")
IT = re.compile(
    r"Iteration (\d+): loss ([-+0-9.eE]+)\s+\[dt=([0-9.]+)s elapsed=([0-9.]+)s\]"
)
CNT = re.compile(r"^\s+(nfev|nhev|njev|nit):\s+(\d+)")


def parse(path):
    rows, cnt = [], {}
    for line in open(path, errors="replace"):
        line = ANSI.sub("", line)
        m = IT.search(line)
        if m:
            rows.append(
                dict(
                    it=int(m.group(1)),
                    loss=float(m.group(2)),
                    dt=float(m.group(3)),
                    el=float(m.group(4)),
                )
            )
            continue
        m = CNT.search(line)
        if m:
            cnt[m.group(1)] = int(m.group(2))
    return rows, cnt


def analyse(name, final_ref=None):
    rows, cnt = parse(LOGS[name])
    loss = np.array([r["loss"] for r in rows])
    dt = np.array([r["dt"] for r in rows])
    n = len(rows)
    acc = np.r_[
        True, loss[1:] < loss[:-1]
    ]  # iteration 0 is the first accepted step from the warm start (376.675)
    fresh = np.r_[True, acc[:-1]]
    t_f = float(np.median(dt[~fresh])) if (~fresh).any() else np.nan
    done = "nhev" in cnt
    final = float(loss.min()) if final_ref is None else final_ref
    n_f = cnt.get("nfev", n)
    if done:
        t_h = (dt.sum() - n_f * t_f) / cnt["nhev"]
    else:
        t_h = np.nan
    out = dict(
        name=name,
        finished=done,
        counters=cnt,
        n_iter=n,
        wall_s=float(dt.sum()),
        t_f=t_f,
        t_h=t_h,
        n_rejected=int((~acc).sum()),
        n_fresh=int(fresh.sum()),
        final=final,
    )
    if done:
        hv = np.where(fresh, np.maximum(dt - t_f, 0) / t_h, 0.0)
        out["hvp_est_sum"] = float(hv.sum())
        out["time_in_hvp_frac"] = float(cnt["nhev"] * t_h / dt.sum())
        out["max_hvp_one_iter"] = float(hv.max())
        # expensive fresh solves whose step was then rejected (Krylov work thrown away)
        wasted = fresh & np.r_[~acc[:]]
        out["fresh_then_rejected_s"] = float(dt[wasted].sum())
        out["n_fresh_then_rejected"] = int(wasted.sum())
    # q-to-go bands (q = 2 * NLL)
    qtg = 2 * (
        np.r_[START[name], loss[:-1]] - final
    )  # q still to go at the START of each iteration
    bands = [(10, np.inf), (1, 10), (0.1, 1), (0.01, 0.1), (1e-3, 0.01), (0, 1e-3)]
    out["bands"] = []
    for lo, hi in bands:
        sel = (qtg >= lo) & (qtg < hi)
        out["bands"].append(
            dict(
                q_to_go=f"[{lo},{hi})",
                n_iter=int(sel.sum()),
                wall_s=float(dt[sel].sum()),
                frac=float(dt[sel].sum() / dt.sum()),
            )
        )
    # time / iteration to reach q-to-go thresholds
    el = np.cumsum(dt)
    out["reach"] = {}
    for thr in [1.0, 0.1, 0.02, 0.01, 2e-3, 2e-6]:
        k = np.nonzero(2 * (loss - final) < thr)[0]
        out["reach"][f"q<{thr:g}"] = (
            dict(it=int(k[0]), wall_s=float(el[k[0]])) if len(k) else None
        )
    out["rows"] = [
        dict(it=r["it"], loss=r["loss"], dt=r["dt"], acc=bool(a), fresh=bool(f))
        for r, a, f in zip(rows, acc, fresh)
    ]
    return out


def main():
    res = {}
    res["SATB8"] = analyse("SATB8")
    res["SATB8SA"] = analyse("SATB8SA")
    res["SATC2"] = analyse("SATC2")
    res["SATP"] = analyse("SATP")
    json.dump(res, open(f"{T}/cost_breakdown.json", "w"), indent=1)
    for k, r in res.items():
        print(
            f"\n### {k}  finished={r['finished']} iters={r['n_iter']} wall={r['wall_s']:.0f}s "
            f"t_f={r['t_f']:.1f}s t_h={r['t_h']:.2f}s rejected={r['n_rejected']} counters={r['counters']}"
        )
        for kk in [
            "hvp_est_sum",
            "time_in_hvp_frac",
            "max_hvp_one_iter",
            "fresh_then_rejected_s",
            "n_fresh_then_rejected",
        ]:
            if kk in r:
                print(f"  {kk}: {r[kk]:.3g}")
        print("  | q to go | iters | wall s | frac |")
        for b in r["bands"]:
            print(
                f"  | {b['q_to_go']} | {b['n_iter']} | {b['wall_s']:.0f} | {b['frac']:.2f} |"
            )
        print("  reach:", r["reach"])


if __name__ == "__main__":
    main()
