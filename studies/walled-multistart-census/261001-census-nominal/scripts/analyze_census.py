#!/usr/bin/env python3
"""T4 census analysis: every CENS<NN> fit vs NOMSTIFF (same objective: card A + lattice, tau 8, margin 0).

Per fit:
  * status (log exit code, fitresult present), NLL (= stored nllvalreduced, walled objective), dNLL vs NOMSTIFF,
    EDM from io_tools.get_fitresult(path, None)["edmval"];
  * d(alphaS)/sigma_NOMSTIFF -- BLINDED x differences only (same parameter, same integer-count data family, so the
    additive offset cancels). No absolute alphaS is computed, printed or saved;
  * physical NP lambdas (anchor + width*theta, anchors from the card's correction runcard via the fitresult meta chain)
    and the wall's armed conditions at margin 0 (coefficient; a face is "on" when coeff < FACE_TOL);
  * ||d theta|| to NOMSTIFF per parameter family, raw (fit coordinates) and in units of sigma_NOMSTIFF;
  * minimiser metrics from the log (loghist.py): iterations, rejected steps, restarts, minimize()/Hessian time,
    wall time from the run_fit.sh [run] stamps.
Then pairwise dNLL and ||d theta/sigma|| among all finished fits + NOMSTIFF and a single-linkage clustering:
same minimum if |dNLL| < --dnll-tol AND ||d theta/sigma_ref|| < --floor.

A fit that is not finished / failed is LISTED with its state, never dropped.

usage (in the container): analyze_census.py [--json analysis.json] [--floor F] [--plot]
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime

import numpy as np
from rabbit import io_tools

from wremnants.postprocessing.scetlib_ad import np_damping_wall as W
from wremnants.postprocessing.scetlib_ad import params as P
from wremnants.postprocessing.scetlib_ad import response as R

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import loghist  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
REF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
OUT = f"{A}/261001_census_nominal"
YMAX = 2.5  # binding |Y| (card absYVGen), as logged by the wall and by make_random_starts.py
MARGIN = 0.0
FACE_TOL = 1e-5  # coefficient below this (incl. the tau-8 overshoot of ~1e-6) = sitting on the face

FAMILIES = [
    ("alphaS", r"alphaS"),
    ("NP lambda", r"(delta_)?lambda\d+(_nu)?"),
    ("resum TNP / transition / FO scale", r"resum.*"),
    ("PDF (eig + mb/mc)", r"(pdfEig\d+|pdfMSHT.*|mb_up)"),
    ("QCDscaleZ helicity", r"QCDscaleZ.*"),
    (
        "muon calib",
        r"(Scale_correction.*|ScaleClos.*|Resolution_correction.*|pixel_multiplicity.*)",
    ),
    ("eff stat", r"effStat_.*"),
    ("eff syst", r"effSyst_.*"),
    ("other (EW, lumi, bkg, prefire, ...)", r".*"),
]


def family(n):
    for lab, pat in FAMILIES:
        if re.fullmatch(pat, n):
            return lab


def load_fit(path):
    fr, meta = io_tools.get_fitresult(path, None, meta=True)
    h = fr["parms"].get()
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in h.axes[0]]
    return dict(
        names=names,
        x=np.asarray(h.values(), dtype=float),
        sig=np.sqrt(np.asarray(h.variances(), dtype=float)),
        nll=float(fr["nllvalreduced"]),
        edm=float(fr["edmval"]),
        meta=meta,
    )


def load_snapshot(path, nll):
    import h5py

    with h5py.File(path, "r") as f:
        names = [
            n.decode() if isinstance(n, bytes) else str(n) for n in f["parms"][...]
        ]
        x = np.asarray(f["x"][...], dtype=float)
        reason = f.attrs.get("reason")
    return dict(names=names, x=x, sig=None, nll=nll, edm=None, meta=None, reason=reason)


# Fits whose result is not simply fitresults_<pf>.hdf5 (orchestrator, 2026-10-01; see the task logbook):
#  * CENS09 was SIGTERM'd after minimize() converged (snapshot reason "converged"); the SIGTERM handler snapshots and
#    exits, so its Hessian/EDM come from the --noFit pass CENS09PF on that snapshot.
#  * CENS03 crawled at +430 on the wall face; SIGTERM'd, restarted as CENS03R from the snapshot, SIGTERM'd again.
#    Its last snapshot is described (NOT a minimum); its NLL is the one-load evaluation in cens03_hybrid_eval.json.
CHAINS = {"CENS09": ["CENS09", "CENS09PF"], "CENS03": ["CENS03", "CENS03R"]}
RESULT_FROM = {"CENS09": "CENS09PF"}
NOT_CONVERGED = {"CENS03": "CENS03R"}


def physical(fit, cfg, lam_names):
    phys, fitted = {}, []
    for n in lam_names:
        a = P.corr_anchor_value(cfg, n)
        rp = P.reparam(n)
        if n in fit["names"]:
            i = fit["names"].index(n)
            phys[n] = (
                a + rp[1][0] * fit["x"][i]
                if (rp is not None and rp[0] == "unit")
                else float(fit["x"][i])
            )
            fitted.append(n)
        else:
            phys[n] = a
    return phys, fitted


def faces(phys, fitted, np_model, np_model_nu):
    rows = []
    for c in W.damping_conditions(np_model, np_model_nu, ymax=YMAX, margin=MARGIN):
        if not any(n in fitted for n in c.names):
            continue  # held-only: dropped by the wall
        v = float(np.min(np.atleast_1d(c.value(phys, W.numpy_relu2))))
        rows.append(dict(label=c.label, coeff=v, on=v < c.bound + FACE_TOL))
    return rows


SHORT = {
    "lambda2_nu >= 0": "λ2_ν",
    "at |Y|=0 (TMD small-b": "L2(0)",
    "at |Y|=2.5 (TMD small-b": "L2(2.5)",
    "at |Y|=0 (TMD large-b": "B(0)",
    "at |Y|=2.5 (TMD large-b": "B(2.5)",
}


def short(label):
    for k, v in SHORT.items():
        if k in label:
            return v
    return label


def run_stamps(log):
    t0 = t1 = rc = None
    for line in open(log, errors="replace"):
        if line.startswith("[run]") and "postfix=" in line:
            t0 = datetime.fromisoformat(line.split()[1])
        m = re.match(r"\[run\] (\S+) exit=(\d+)", line)
        if m:
            t1, rc = datetime.fromisoformat(m.group(1)), int(m.group(2))
    return t0, t1, rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=f"{TASK}/analysis.json")
    ap.add_argument("--dnll-tol", type=float, default=1e-4)
    ap.add_argument(
        "--floor",
        type=float,
        default=None,
        help="||dtheta/sigma_ref|| threshold for 'same minimum' (default: printed distribution only)",
    )
    ap.add_argument("--plot", action="store_true")
    args = ap.parse_args()

    seedmap = dict(csv.reader(open(f"{TASK}/cmds/seedmap.csv")))
    seedmap.pop("postfix", None)
    man = {}
    for f in ("manifest_pert.csv", "manifest_cold.csv"):
        for r in csv.DictReader(open(f"{TASK}/seeds/{f}")):
            man[r["file"]] = r
    step0 = json.load(open(f"{TASK}/step0_seed_cost.json"))

    ref = load_fit(REF)
    cfg = R.corr_config_from_meta(ref["meta"])["config"]
    np_model, np_model_nu = W.forms_from_corr_config(cfg)
    lam_names = tuple(
        dict.fromkeys(W._TMD_LAMBDAS[np_model] + W._CS_LAMBDAS[np_model_nu])
    )
    names = ref["names"]
    ia = names.index("alphaS")
    fam = np.array([family(n) for n in names])
    pr, fitted = physical(ref, cfg, lam_names)

    def describe(fit):
        ph, _ = physical(fit, cfg, lam_names)
        fc = faces(ph, fitted, np_model, np_model_nu)
        dx = fit["x"] - ref["x"]
        dxs = dx / ref["sig"]
        famn = {
            lab: dict(
                raw=float(np.linalg.norm(dx[fam == lab])),
                sig=float(np.linalg.norm(dxs[fam == lab])),
            )
            for lab, _ in FAMILIES
        }
        return dict(
            lambdas={n: float(ph[n]) for n in fitted},
            faces=fc,
            faces_on=[short(r["label"]) for r in fc if r["on"]],
            dtheta_raw=float(np.linalg.norm(dx)),
            dtheta_sig=float(np.linalg.norm(dxs)),
            dtheta_family=famn,
            dalphaS_over_sig=float(dxs[ia]),
            sig_ratio=(
                float(fit["sig"][ia] / ref["sig"][ia])
                if fit["sig"] is not None
                else None
            ),
            max_pull=(names[int(np.argmax(np.abs(dxs)))], float(np.max(np.abs(dxs)))),
        )

    rows, fits = [], {"NOMSTIFF": ref}
    for pf in sorted(seedmap):
        seed = os.path.basename(seedmap[pf])
        m = man[seed]
        row = dict(
            postfix=pf,
            seed=seed,
            mode=m["mode"],
            u_start=float(m["u"]),
            start_lambdas={n: float(m[n]) for n in fitted},
            start_dnll=step0.get(seed, {}).get("d_nll"),
        )
        chain = CHAINS.get(pf, [pf])
        logs = [f"{OUT}/{c}.log" for c in chain]
        if not os.path.exists(logs[0]) or os.path.getsize(logs[0]) == 0:
            row["state"] = "not started"
            rows.append(row)
            continue
        lgs = [loghist.parse(lp) for lp in logs]
        stamps = [run_stamps(lp) for lp in logs]
        t_wall = sum((t1 - t0).total_seconds() for t0, t1, _ in stamps if t0 and t1)
        rc = stamps[-1][2]
        timing = (
            {}
        )  # parsed directly: loghist only reads timings after a scipy result dump (absent on a stall stop / --noFit)
        for lp in logs:
            for line in open(lp, errors="replace"):
                m = re.search(
                    r"\[timing\] (fitter\.minimize\(\)|loss_val_grad_hess\(\) \(postfit cov\)): ([0-9.]+) s",
                    line,
                )
                if m:
                    timing[m.group(1)] = timing.get(m.group(1), 0.0) + float(m.group(2))
        txt0 = open(logs[0], errors="replace").read()
        stop = (
            "stall early-stop (maxRestarts 0)"
            if "Minimizer still stalling" in txt0
            else (
                "SIGTERM"
                if any(r == 143 for _, _, r in stamps) and pf not in RESULT_FROM
                else (
                    lgs[0]["result"].get("message", "")[:40] if lgs[0]["result"] else ""
                )
            )
        )
        row.update(
            chain=chain,
            n_iter=sum(lg["n_iter"] for lg in lgs),
            n_rejected=sum(lg.get("n_rejected", 0) for lg in lgs),
            longest_rejected_run=max(lg.get("longest_rejected_run", 0) for lg in lgs),
            n_increase=sum(lg.get("n_increase", 0) for lg in lgs),
            restarts=sum(len(lg["restarts"]) for lg in lgs),
            stop=stop,
            t_minimize=timing.get("fitter.minimize()"),
            t_hessian=timing.get("loss_val_grad_hess() (postfit cov)"),
            t_wall=t_wall or None,
            exit=[r for _, _, r in stamps],
            last_loss=float(
                next(lg["loss"][-1] for lg in reversed(lgs) if lg["n_iter"])
            ),
        )
        if pf in NOT_CONVERGED:
            ev = json.load(open(f"{TASK}/cens03_hybrid_eval.json"))["snap03R.hdf5"]
            fit = load_snapshot(
                f"{OUT}/snapshot_fitresults_{NOT_CONVERGED[pf]}.hdf5",
                ref["nll"] + ev["d_nll"],
            )
            assert fit["names"] == names
            row.update(
                state="NOT CONVERGED (crawl on the wall face, SIGTERM x2)",
                snapshot_reason=fit["reason"],
                nll=fit["nll"],
                dnll=ev["d_nll"],
                dnll_split=dict(
                    data=ev["d_ln"], constraints=ev["d_lc"], bbstat=ev["d_lbeta"]
                ),
                grad_max=ev["grad_max"],
                edm=None,
                **describe(fit),
            )
            rows.append(row)
            continue
        rpf = RESULT_FROM.get(pf, pf)
        fr = f"{OUT}/fitresults_{rpf}.hdf5"
        rlog = f"{OUT}/{rpf}.log"
        rstamp = run_stamps(rlog)
        finished = (
            rstamp[2] == 0
            and "Results written in file" in open(rlog, errors="replace").read()
        )
        if not (finished and os.path.exists(fr)):
            row["state"] = "running" if rc is None else f"FAILED exit={rc}"
            rows.append(row)
            continue
        fit = load_fit(fr)
        assert fit["names"] == names
        fits[pf] = fit
        row.update(
            state="done" + (f" (result from {rpf})" if rpf != pf else ""),
            result_file=fr,
            nll=fit["nll"],
            dnll=fit["nll"] - ref["nll"],
            edm=fit["edm"],
            **describe(fit),
        )
        rows.append(row)

    # pairwise among finished fits + NOMSTIFF
    keys = list(fits)
    n = len(keys)
    D = np.zeros((n, n))
    DN = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            D[i, j] = np.linalg.norm(
                (fits[keys[i]]["x"] - fits[keys[j]]["x"]) / ref["sig"]
            )
            DN[i, j] = fits[keys[i]]["nll"] - fits[keys[j]]["nll"]
    clusters = None
    if args.floor is not None:
        lab = list(range(n))

        def find(a):
            while lab[a] != a:
                a = lab[a]
            return a

        for i in range(n):
            for j in range(i + 1, n):
                if abs(DN[i, j]) < args.dnll_tol and D[i, j] < args.floor:
                    lab[find(j)] = find(i)
        roots = {}
        for i in range(n):
            roots.setdefault(find(i), []).append(keys[i])
        # order minima by NLL, NOMSTIFF's own cluster is "M0"
        cl = sorted(roots.values(), key=lambda ks: min(fits[k]["nll"] for k in ks))
        clusters = {}
        for c in cl:
            name = (
                "M0 (NOMSTIFF)"
                if "NOMSTIFF" in c
                else f"M{len([v for v in clusters if not v.startswith('M0')]) + 1}"
            )
            clusters[name] = c
        for r in rows:
            for cname, members in clusters.items():
                if r["postfix"] in members:
                    r["minimum"] = cname

    # ---- print
    print(
        f"reference NOMSTIFF: NLL {ref['nll']:.10f}  EDM {ref['edm']:.2e}  forms {np_model}/{np_model_nu}  fitted {fitted}"
    )
    print("   ref lambdas:", {k: round(v, 6) for k, v in pr.items()})
    for r in rows:
        if "nll" not in r:
            print(
                f"{r['postfix']} [{r['seed']}] {r['state']}  iters {r.get('n_iter')}  last loss {r.get('last_loss')}"
            )
            continue
        if not r["state"].startswith("done"):
            print(
                f"{r['postfix']} [{r['seed']}] {r['state']}: dNLL {r['dnll']:+.3f} {r['dnll_split']} |grad|max {r['grad_max']:.3g}"
                f"  dalphaS/sig {r['dalphaS_over_sig']:+.4f}  ||dth/sig|| {r['dtheta_sig']:.3g}  faces {r['faces_on']}"
                f"  iters {r['n_iter']}  t_wall {r['t_wall']:.0f} s"
            )
            print(
                "      lambdas",
                {k: round(v, 6) for k, v in r["lambdas"].items()},
                " max pull",
                r["max_pull"][0],
                f"{r['max_pull'][1]:.3g}",
            )
            print(
                "      ||dth/sig|| by family",
                {
                    k: float(f"{v['sig']:.3g}")
                    for k, v in r["dtheta_family"].items()
                    if v["sig"] > 0
                },
            )
            continue
        print(
            f"{r['postfix']} [{r['seed']}, u0 {r['u_start']:+.2f}, start dNLL {r['start_dnll']:+.0f}]  "
            f"dNLL {r['dnll']:+.3e}  EDM {r['edm']:.1e}  dalphaS/sig {r['dalphaS_over_sig']:+.4f}  sig ratio {r['sig_ratio']:.4f}  "
            f"||dth/sig|| {r['dtheta_sig']:.3e} (raw {r['dtheta_raw']:.3e})  faces {r['faces_on']}  "
            f"iters {r['n_iter']} rej {r['n_rejected']} (run {r['longest_rejected_run']}) restarts {r['restarts']} stop '{r['stop']}'  t_min {r['t_minimize']} s  t_hess {r['t_hessian']} s  t_wall {r['t_wall']} s"
            + (f"  -> {r.get('minimum')}" if clusters else "")
        )
        print(
            "      lambdas",
            {k: round(v, 6) for k, v in r["lambdas"].items()},
            " max pull",
            r["max_pull"][0],
            f"{r['max_pull'][1]:.3g}",
        )
        print(
            "      ||dth/sig|| by family",
            {
                k: float(f"{v['sig']:.3g}")
                for k, v in r["dtheta_family"].items()
                if v["sig"] > 0
            },
        )
    print("\npairwise ||dtheta/sigma_ref|| (upper) and dNLL row-col (lower):")
    print("        " + " ".join(f"{k[-6:]:>9s}" for k in keys))
    for i in range(n):
        print(
            f"{keys[i][-6:]:>8s}"
            + " ".join(
                (
                    f"{D[i, j]:9.2e}"
                    if j > i
                    else (f"{DN[i, j]:+9.1e}" if j < i else f"{'-':>9s}")
                )
                for j in range(n)
            )
        )
    if clusters:
        print(f"\nclusters (|dNLL| < {args.dnll_tol}, ||dth/sig|| < {args.floor}):")
        for c, m in clusters.items():
            print(
                f"  {c}: {m}  NLL-NLL_ref = {min(fits[k]['nll'] for k in m) - ref['nll']:+.3e}"
            )
    out = dict(
        reference=REF,
        ref_nll=ref["nll"],
        ref_edm=ref["edm"],
        ref_lambdas=pr,
        rows=rows,
        pair_keys=keys,
        pair_dtheta_sig=D.tolist(),
        pair_dnll=DN.tolist(),
        clusters=clusters,
        floor=args.floor,
        dnll_tol=args.dnll_tol,
        face_tol=FACE_TOL,
    )
    with open(args.json, "w") as f:
        json.dump(out, f, indent=1, default=float)
    print(f"wrote {args.json}")
    if args.plot and clusters:
        make_plot(rows, clusters, args)


def make_plot(rows, clusters, args):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.stats import spearmanr

    from plot_output import save_plot

    plt.rcdefaults()
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.6))
    pal = {c: f"C{i}" for i, c in enumerate(clusters)}
    nc = "not converged"
    pal[nc] = "C3"
    pts = [r for r in rows if "nll" in r]
    for r in pts:
        c = r.get("minimum", nc)
        mk = "s" if r["mode"].startswith("cold") else "o"
        kw = dict(color=pal[c], marker=mk, s=55, zorder=3, label=c)
        axs[0].scatter(r["dtheta_sig"], max(abs(r["dnll"]), 1e-13), **kw)
        axs[0].annotate(
            r["postfix"][-2:],
            (r["dtheta_sig"], max(abs(r["dnll"]), 1e-13)),
            textcoords="offset points",
            xytext=(4, 3),
            fontsize=7,
        )
        axs[1].scatter(int(r["postfix"][-2:]), r["dalphaS_over_sig"], **kw)
        axs[2].scatter(r["start_dnll"], r["n_iter"], **kw)
        axs[2].annotate(
            r["postfix"][-2:],
            (r["start_dnll"], r["n_iter"]),
            textcoords="offset points",
            xytext=(4, 3),
            fontsize=7,
        )
    ax = axs[0]
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.axvline(args.floor, color="0.4", ls="--", lw=0.8)
    ax.axhline(args.dnll_tol, color="0.4", ls="--", lw=0.8)
    ax.text(args.floor, 1e-12, " floor", fontsize=7, color="0.3")
    ax.set_xlabel(
        r"$\|\Delta\theta/\sigma_{\rm NOMSTIFF}\|$ to NOMSTIFF (all 3719 parameters)"
    )
    ax.set_ylabel(r"|NLL $-$ NLL(NOMSTIFF)|  (walled objective)")
    ax.set_title("(a) distance to NOMSTIFF; dashed = same-minimum cuts", fontsize=9)
    h, lab = ax.get_legend_handles_labels()
    ax.legend(
        dict(zip(lab, h)).values(),
        dict(zip(lab, h)).keys(),
        fontsize=7,
        title="circle = perturbed, square = cold start",
        title_fontsize=7,
        loc="center left",
    )
    ax = axs[1]
    ax.axhline(0, color="0.6", lw=0.6)
    ax.set_xlabel("census start CENS<NN>")
    ax.set_ylabel(r"$\Delta\alpha_S/\sigma_{\rm NOMSTIFF}$ (blinded difference)")
    ax.set_title(
        "(b) " + r"$\alpha_S$" + " shift per start (CENS03 = unconverged point)",
        fontsize=9,
    )
    ax.set_xticks(range(1, 11))
    ax = axs[2]
    conv = [r for r in pts if "minimum" in r]
    rho, pv = spearmanr([r["start_dnll"] for r in conv], [r["n_iter"] for r in conv])
    ax.set_xlabel("start NLL $-$ NLL(NOMSTIFF)  (step 0)")
    ax.set_ylabel("minimiser iterations (CENS03: both runs, SIGTERM)")
    ax.set_title(
        f"(c) cost vs start distance; converged starts: Spearman $\\rho$ = {rho:.2f} (p = {pv:.2f})",
        fontsize=9,
    )
    fig.suptitle(
        "Census of the nominal walled fit (card A + lattice, $\\lambda_4^\\nu$ = 0, margin 0, $\\tau$ = 8, "
        "bin0xzero cache), real data, blinded",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save_plot(
        outdir=TASK,
        basename="census_summary",
        fig=fig,
        args=args,
        meta_info={
            "reference": REF,
            "floor": args.floor,
            "dnll_tol": args.dnll_tol,
            "spearman_iters_vs_start": [rho, pv],
        },
    )
    print(
        f"[plot] census_summary; Spearman(start dNLL, iters) over converged = {rho:.3f} (p {pv:.3f})"
    )
    for key in ("t_minimize",):
        r2, p2 = spearmanr([r["start_dnll"] for r in conv], [r[key] for r in conv])
        print(f"[plot] Spearman(start dNLL, {key}) = {r2:.3f} (p {p2:.3f})")


if __name__ == "__main__":
    main()
