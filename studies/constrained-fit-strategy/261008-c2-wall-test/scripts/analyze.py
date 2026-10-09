#!/usr/bin/env python3
"""Log-level comparison: C2A / R2A / CENS03R (main fit) and SATC2 / SATB8 (saturated sub-fit).

Pure text parsing (no TF, no cache). Uses the 261006-diagnosis parser (scripts/parse_logs.py: parse) and a verbatim
copy of its crawl analysis (scripts/analyze_logs.py: krylov), so the crawl signature is the same test the diagnosis
used: fraction of consecutive accepted pairs with gain ratio ~1 (the period-2 lock; 40-44 % in CENS03/CMR1A, 1-9 % in
normal fits), and >= 30-iteration windows gaining < 1e-3 while > 1e-3 above the final loss.

Per fit: iterations / wall time / CPU-seconds until the loss is within 1e-3 and 1e-6 of its OWN final loss (and, for
the main fits, of NOMSTIFF's 376.6146329237086), number of minimiser restarts (Iteration 0 lines), final loss.
CPU-seconds come from logs/<PF>.cpu.csv (utime+stime of the python process, sampled every 30 s), at the first sample
whose last logged iteration is >= the iteration in question (so +-30 s resolution). For the saturated fits only the
SUB-FIT is analysed (the iterations after the 'saturated' sub-fit starts, i.e. after the main --noFit part).

Usage: python3 analyze.py   -> analysis.json + a markdown table on stdout
"""
import csv
import importlib.util
import json
import os
import re

import numpy as np

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAG = os.path.join(os.path.dirname(T), "261006-diagnosis", "scripts")
spec = importlib.util.spec_from_file_location(
    "parse_logs", os.path.join(DIAG, "parse_logs.py")
)
PL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PL)

C = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NOM_LOSS = 376.6146329237086
FITS = {
    "C2A": dict(log=f"{T}/logs/C2A.log", cpu=f"{T}/logs/C2A.cpu.csv", kind="main"),
    "R2A": dict(log=f"{T}/logs/R2A.log", cpu=f"{T}/logs/R2A.cpu.csv", kind="main"),
    "CENS03R": dict(
        log=f"{C}/261001_census_nominal/CENS03R.log", cpu=None, kind="main"
    ),
    "SATC2": dict(log=f"{T}/logs/SATC2.log", cpu=f"{T}/logs/SATC2.cpu.csv", kind="sat"),
    "SATB8": dict(
        log=f"{C}/261007_lattice_term_native/SATB8.log", cpu=None, kind="sat"
    ),
}


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


def krylov(rows):
    """Copy of 261006-diagnosis/scripts/analyze_logs.py krylov(), over ALL rows (restarts concatenated, as it does
    for CENS03R); the gain at a restart boundary is 0 and counts as not accepted."""
    it = np.array([r["it"] for r in rows])
    loss = np.array([r["loss"] for r in rows])
    dt = np.array([r["dt"] for r in rows])
    acc = np.array([r["accepted"] for r in rows])
    final = loss.min()
    rej = ~acc[1:]
    rej_runs = runs(rej)
    gains = np.r_[0, -np.diff(loss)]
    ratios = []
    for k in range(2, len(loss)):
        if acc[k] and acc[k - 1] and gains[k - 1] > 0:
            ratios.append(gains[k] / gains[k - 1])
    ratios = np.array(ratios)
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
        gain_ratio_frac_near2=(
            float(np.mean(np.abs(ratios - 2) < 0.2)) if len(ratios) else None
        ),
        gain_ratio_frac_near1=(
            float(np.mean(np.abs(ratios - 1) < 0.2)) if len(ratios) else None
        ),
        n_ratios=len(ratios),
        crawl=crawl,
    )


def sub_fit_rows(path, rows):
    """Rows of the saturated sub-fit: a --noFit main logs no iterations, so every Iteration line belongs to the
    sub-fit; refuse if a main minimisation is present (rows before the 'saturated' marker).
    """
    txt = open(path, errors="replace").read()
    m = re.search(r"[Ss]aturated", txt)
    return rows


def load_cpu(path):
    if not path or not os.path.exists(path):
        return None
    out = []
    with open(path) as f:
        for r in csv.DictReader(f):
            if r["cpu_s"] in ("", "EXIT") or r["last_it"] in ("", None):
                continue
            out.append((float(r["t_unix"]), float(r["cpu_s"]), int(r["last_it"])))
    return out


def cpu_at(cpu, rows, idx):
    """CPU-seconds at the first sample after row idx was logged. The csv's last_it is per-restart; match the
    (restart-local) iteration number in order of appearance."""
    if not cpu:
        return None
    # walk the samples, tracking the restart count by drops in last_it
    restart, prev = 0, -1
    target_r, target_it = rows[idx]["restart"], rows[idx]["it"]
    for t, c, li in cpu:
        if li < prev:
            restart += 1
        prev = li
        if restart > target_r or (restart == target_r and li >= target_it):
            return c
    return None


def first_within(rows, ref, tol):
    loss = np.array([r["loss"] for r in rows])
    hit = np.where(loss - ref <= tol)[0]
    return int(hit[0]) if len(hit) else None


def main():
    out = {}
    for name, f in FITS.items():
        if not os.path.exists(f["log"]):
            continue
        rows, timing = PL.parse(f["log"])
        if not rows:
            out[name] = dict(n=0)
            continue
        txt = open(f["log"], errors="replace").read()
        finished = "Results written" in txt
        cpu = load_cpu(f["cpu"])
        loss = np.array([r["loss"] for r in rows])
        el = np.cumsum(
            [r["dt"] for r in rows]
        )  # wall time of the minimisation, restarts included
        res = dict(
            log=f["log"],
            finished=finished,
            n_rows=len(rows),
            restarts=int(rows[-1]["restart"]),
            start_loss=float(loss[0]),
            final_loss=float(loss[-1]),
            min_loss=float(loss.min()),
            wall_s=float(el[-1]),
            timing=timing,
            n_dt_ge_300=int(sum(r["dt"] >= 300 for r in rows)),
            above_nomstiff_end=(
                float(loss[-1] - NOM_LOSS) if f["kind"] == "main" else None
            ),
        )
        if cpu:
            res["cpu_s_total"] = cpu[-1][1]
            res["cpu_per_wall"] = (cpu[-1][1] - cpu[0][1]) / max(
                1.0, cpu[-1][0] - cpu[0][0]
            )
        refs = {"own_final": float(loss.min())}
        if f["kind"] == "main":
            refs["NOMSTIFF"] = NOM_LOSS
        for rn, ref in refs.items():
            for tol in (1e-3, 1e-6):
                i = first_within(rows, ref, tol)
                key = f"to_{rn}_{tol:g}"
                res[key] = (
                    None
                    if i is None
                    else dict(
                        iter_index=i,
                        iters=i,
                        wall_s=float(el[i]),
                        cpu_s=cpu_at(cpu, rows, i),
                        cpu_s_rel=(
                            None
                            if not cpu or cpu_at(cpu, rows, i) is None
                            else cpu_at(cpu, rows, i) - cpu[0][1]
                        ),
                    )
                )
        res["crawl_sig"] = krylov(rows)
        out[name] = res
    json.dump(out, open(f"{T}/analysis.json", "w"), indent=1)
    print(
        "| fit | start loss | final loss | rows (restarts) | to own final-1e-3: it / wall h | to -1e-6: it / wall h "
        "| to NOMSTIFF+1e-6 | dt>=300s steps | gain-ratio ~1 / ~2 | crawl windows | finished |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for n, r in out.items():
        if not r.get("n_rows"):
            continue

        def fm(d):
            return "—" if not d else f"{d['iters']} / {d['wall_s'] / 3600:.2f}"

        cs = r["crawl_sig"]
        cw = (
            "; ".join(
                f"{c['start']}-{c['end']} (+{c['above_final']:.2g}, {c['hours']:.1f} h)"
                for c in cs["crawl"]
            )
            or "none"
        )
        print(
            f"| {n} | {r['start_loss']:.6f} | {r['final_loss']:.10f} | {r['n_rows']} ({r['restarts']}) | "
            f"{fm(r.get('to_own_final_0.001'))} | {fm(r.get('to_own_final_1e-06'))} | "
            f"{fm(r.get('to_NOMSTIFF_1e-06'))} | {r['n_dt_ge_300']} | {cs['gain_ratio_frac_near1'] or 0:.2f} / "
            f"{cs['gain_ratio_frac_near2'] or 0:.2f} | {cw} | {r['finished']} |"
        )


if __name__ == "__main__":
    main()
