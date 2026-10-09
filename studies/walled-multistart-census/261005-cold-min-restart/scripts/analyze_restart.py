#!/usr/bin/env python3
"""Cold-min restart analysis: CMR1A vs NOMSTIFF, CMR1B vs XWSTIFF (same objective as the reference, seed = C).

Per fit (pattern: 261001-census-nominal/scripts/analyze_census.py):
  * state (run_fit.sh [run] exit stamp, "Results written in file"); if no fitresult, the latest snapshot is described
    and marked NOT a certified minimum;
  * NLL (stored nllvalreduced = walled objective), dNLL vs reference, EDM from the fitresult;
  * d(alphaS)/sigma_ref -- BLINDED x differences only (same blinding offset, verified in blinding_check.py);
  * ||d theta/sigma_ref|| (all, by family), top-10 |d theta/sigma_ref|; also distance from the seed (did it move from C?);
  * physical NP lambdas (anchor + width*theta) and the armed wall faces at margin 0 (coeff < FACE_TOL = on the face);
  * minimiser: iterations, rejected steps, restarts, minimize()/Hessian time, wall time, start loss (iteration 0).
Writes analysis.json and the loss-trace plot via save_plot. No absolute alphaS is computed, printed or saved.
usage (container): analyze_restart.py [--plot]
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

import h5py
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
OUT = f"{A}/261005_cold_min_restart"
JOBS = {
    "CMR1A": (
        "NOMSTIFF",
        f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
        f"{OUT}/seeds/seed_1a_C_in_NOMSTIFF.hdf5",
    ),
    "CMR1B": (
        "XWSTIFF",
        f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
        f"{OUT}/seeds/seed_1b_C_in_XWSTIFF.hdf5",
    ),
}
YMAX, MARGIN, FACE_TOL = 2.5, 0.0, 1e-5
FAMILIES = [
    ("alphaS", r"alphaS"),
    ("NP lambda", r"(delta_)?lambda\d+(_nu)?"),
    ("resum TNP / transition / FO scale", r"resum.*"),
    ("PDF", r"(pdfEig\d+|pdfMSHT.*|mb_up)"),
    ("QCDscaleZ helicity", r"QCDscaleZ.*"),
    (
        "muon calib",
        r"(Scale_correction.*|ScaleClos.*|Resolution_correction.*|pixel_multiplicity.*)",
    ),
    ("eff stat", r"effStat_.*"),
    ("eff syst", r"effSyst_.*"),
    ("other", r".*"),
]
SHORT = {
    "lambda4_nu >= 0": "λ4_ν",
    "lambda2_nu >= 0": "λ2_ν",
    "at |Y|=0 (TMD small-b": "L2(0)",
    "at |Y|=2.5 (TMD small-b": "L2(2.5)",
    "at |Y|=0 (TMD large-b": "B(0)",
    "at |Y|=2.5 (TMD large-b": "B(2.5)",
}


def short(label):
    return next((v for k, v in SHORT.items() if k in label), label)


def family(n):
    return next(lab for lab, pat in FAMILIES if re.fullmatch(pat, n))


def load_fit(path):
    fr, meta = io_tools.get_fitresult(path, None, meta=True)
    h = fr["parms"].get()
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in h.axes[0]]
    return dict(
        names=names,
        x=np.asarray(h.values(), float),
        sig=np.sqrt(np.asarray(h.variances(), float)),
        nll=float(fr["nllvalreduced"]),
        edm=float(fr["edmval"]),
        meta=meta,
    )


def load_flat(path):
    with h5py.File(path, "r") as f:
        names = [
            n.decode() if isinstance(n, bytes) else str(n) for n in f["parms"][...]
        ]
        return dict(names=names, x=np.asarray(f["x"][...], float), attrs=dict(f.attrs))


def physical(fit, cfg, lam_names):
    phys, fitted = {}, []
    for n in lam_names:
        a = P.corr_anchor_value(cfg, n)
        rp = P.reparam(n)
        if n in fit["names"]:
            v = fit["x"][fit["names"].index(n)]
            phys[n] = (
                a + rp[1][0] * v if (rp is not None and rp[0] == "unit") else float(v)
            )
            fitted.append(n)
        else:
            phys[n] = a
    return phys, fitted


def faces(phys, fitted, np_model, np_model_nu):
    rows = []
    for c in W.damping_conditions(np_model, np_model_nu, ymax=YMAX, margin=MARGIN):
        if not any(n in fitted for n in c.names):
            continue
        v = float(np.min(np.atleast_1d(c.value(phys, W.numpy_relu2))))
        rows.append(dict(label=short(c.label), coeff=v, on=v < c.bound + FACE_TOL))
    return rows


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
    ap.add_argument("--plot", action="store_true")
    ap.add_argument("--json", default=f"{TASK}/analysis.json")
    args = ap.parse_args()
    out, traces = {}, {}
    for pf, (rname, rpath, seedp) in JOBS.items():
        ref = load_fit(rpath)
        cfg = R.corr_config_from_meta(ref["meta"])["config"]
        np_model, np_model_nu = W.forms_from_corr_config(cfg)
        lam_names = tuple(
            dict.fromkeys(W._TMD_LAMBDAS[np_model] + W._CS_LAMBDAS[np_model_nu])
        )
        names = ref["names"]
        ia = names.index("alphaS")
        fam = np.array([family(n) for n in names])
        seed = load_flat(seedp)
        assert seed["names"] == names
        log = f"{OUT}/{pf}.log"
        row = dict(postfix=pf, reference=rname, ref_nll=ref["nll"], ref_edm=ref["edm"])
        if not os.path.exists(log) or os.path.getsize(log) == 0:
            row["state"] = "not started"
            out[pf] = row
            continue
        lg = loghist.parse(log)
        t0, t1, rc = run_stamps(log)
        txt = open(log, errors="replace").read()
        timing = {}
        for m in re.finditer(
            r"\[timing\] (fitter\.minimize\(\)|loss_val_grad_hess\(\) \(postfit cov\)): ([0-9.]+) s",
            txt,
        ):
            timing.setdefault(m.group(1), float(m.group(2)))
        row.update(
            n_iter=lg["n_iter"],
            n_rejected=lg.get("n_rejected"),
            longest_rejected_run=lg.get("longest_rejected_run"),
            restarts=len(lg["restarts"]),
            scipy_message=lg["result"].get("message"),
            start_loss_minus_ref=(
                (float(lg["loss"][0]) - ref["nll"]) if lg["n_iter"] else None
            ),
            last_loss_minus_ref=(
                (float(lg["loss"][-1]) - ref["nll"]) if lg["n_iter"] else None
            ),
            t_minimize=timing.get("fitter.minimize()"),
            t_hessian=timing.get("loss_val_grad_hess() (postfit cov)"),
            t_wall=(t1 - t0).total_seconds() if (t0 and t1) else None,
            exit=rc,
            stall_stop="Minimizer still stalling" in txt,
        )
        traces[pf] = (lg["loss"] - ref["nll"], lg["elapsed"], rname)
        frp = f"{OUT}/fitresults_{pf}.hdf5"
        if rc == 0 and "Results written in file" in txt and os.path.exists(frp):
            fit = load_fit(frp)
            row.update(
                state="done",
                nll=fit["nll"],
                dnll=fit["nll"] - ref["nll"],
                edm=fit["edm"],
                sig_ratio=float(fit["sig"][ia] / ref["sig"][ia]),
            )
        else:
            snp = f"{OUT}/snapshot_fitresults_{pf}.hdf5"
            if not os.path.exists(snp):
                row["state"] = (
                    "running (no snapshot yet)" if rc is None else f"FAILED exit={rc}"
                )
                out[pf] = row
                continue
            fit = load_flat(snp)
            row.update(
                state=("running" if rc is None else f"exit={rc}")
                + ": SNAPSHOT, not a certified minimum",
                snapshot_attrs={k: str(v) for k, v in fit["attrs"].items()},
            )
        assert fit["names"] == names
        ph, fitted = physical(fit, cfg, lam_names)
        pr, _ = physical(ref, cfg, lam_names)
        ps, _ = physical(seed, cfg, lam_names)
        dx = (fit["x"] - ref["x"]) / ref["sig"]
        ds = (fit["x"] - seed["x"]) / ref["sig"]
        dsr = (seed["x"] - ref["x"]) / ref["sig"]
        order = np.argsort(-np.abs(dx))
        row.update(
            dalphaS_over_sigref=float(dx[ia]),
            seed_dalphaS_over_sigref=float(dsr[ia]),
            dtheta_sig=float(np.linalg.norm(dx)),
            dtheta_sig_from_seed=float(np.linalg.norm(ds)),
            seed_dtheta_sig=float(np.linalg.norm(dsr)),
            dtheta_sig_family={
                lab: float(np.linalg.norm(dx[fam == lab])) for lab, _ in FAMILIES
            },
            top10=[(names[k], float(dx[k])) for k in order[:10]],
            lambdas=ph,
            lambdas_ref=pr,
            lambdas_seed=ps,
            fitted=fitted,
            faces=faces(ph, fitted, np_model, np_model_nu),
            faces_ref=faces(pr, fitted, np_model, np_model_nu),
        )
        row["faces_on"] = [f["label"] for f in row["faces"] if f["on"]]
        row["faces_on_ref"] = [f["label"] for f in row["faces_ref"] if f["on"]]
        out[pf] = row

    for pf, r in out.items():
        print(f"===== {pf} vs {r['reference']}: {r['state']}")
        for k in (
            "nll",
            "dnll",
            "edm",
            "start_loss_minus_ref",
            "last_loss_minus_ref",
            "dalphaS_over_sigref",
            "seed_dalphaS_over_sigref",
            "sig_ratio",
            "dtheta_sig",
            "seed_dtheta_sig",
            "dtheta_sig_from_seed",
            "n_iter",
            "n_rejected",
            "longest_rejected_run",
            "restarts",
            "stall_stop",
            "scipy_message",
            "t_minimize",
            "t_hessian",
            "t_wall",
            "exit",
        ):
            if k in r:
                v = r[k]
                print(
                    f"   {k:28s} {v:.6g}" if isinstance(v, float) else f"   {k:28s} {v}"
                )
        if "top10" in r:
            print(
                "   top10 dth/sig:", ", ".join(f"{n} {v:+.3g}" for n, v in r["top10"])
            )
            print(
                "   by family:",
                {
                    k: float(f"{v:.3g}")
                    for k, v in r["dtheta_sig_family"].items()
                    if v > 0
                },
            )
            for lab, d in (
                ("fit", r["lambdas"]),
                ("ref", r["lambdas_ref"]),
                ("seed", r["lambdas_seed"]),
            ):
                print(
                    f"   lambdas {lab:4s}:",
                    {k: float(f"{v:.6g}") for k, v in d.items() if k in r["fitted"]},
                )
            print("   faces on (fit):", r["faces_on"], " (ref):", r["faces_on_ref"])
            print(
                "   face coeffs (fit):",
                {f["label"]: float(f"{f['coeff']:.3e}") for f in r["faces"]},
            )
    with open(args.json, "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", args.json)

    if args.plot and traces:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from plot_output import save_plot

        fig, ax = plt.subplots(figsize=(8, 5))
        for pf, (d, el, rname) in traces.items():
            if len(d):
                ax.plot(
                    el / 3600.0,
                    np.clip(d, 1e-9, None),
                    marker=".",
                    ms=3,
                    label=f"{pf}: loss − NLL({rname})",
                )
        ax.set_yscale("log")
        ax.set_xlabel("elapsed minimize() time [h]")
        ax.set_ylabel("walled loss − reference NLL")
        ax.set_title(
            "Restarts from the cold walled minimum C (τ 8, margin 0)", fontsize=10
        )
        ax.axhline(1e-4, color="gray", ls=":", lw=1)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        save_plot(
            outdir=TASK,
            basename="loss_trace",
            fig=fig,
            args=args,
            meta_info={
                "note": "loss is not blinded; reference = the fit's own configuration minimum"
            },
        )


if __name__ == "__main__":
    main()
