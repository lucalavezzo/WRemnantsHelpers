#!/usr/bin/env python3
"""T2 analysis: stiff-wall (margin 0, tau 8) refits vs their references (default margin 5e-3, tau 5).

Per fit:
  * NLL (new objective), dNLL decomposition:
      nll = base + exp(2 tau) * pen_margin(lambda),  base = the unwalled loss (data + constraints + lattice term)
      stored nllvalreduced INCLUDES the wall (T1 gate: diff 0.0), so base is recovered exactly from the penalty.
    -> ref vector under the NEW objective (no fit needed), new vector under the REF objective,
       and d(base) = the pure data/constraint movement.
  * EDM from io_tools.get_fitresult(path, None)["edmval"].
  * d(alphaS)/sigma_ref -- BLINDED theta differences only, never an absolute value.
  * physical NP lambdas (anchor + width*theta, anchor from the card's correction runcard), armed conditions (the
    wall's own rule: a condition reading only HELD lambdas is dropped), coefficients, active faces at margin 0/5e-3.
  * largest parameter shifts in units of the reference sigma.
  * minimiser metrics from the logs (loghist.py).
Falls back to the converged snapshot (x only; NLL from the log) while the Hessian is still running.

usage: analyze.py [--json out.json] [--md out.md]
"""

import argparse
import json
import os
import sys

import h5py
import numpy as np
from rabbit import io_tools

from wremnants.postprocessing.scetlib_ad import np_damping_wall as W
from wremnants.postprocessing.scetlib_ad import params as P
from wremnants.postprocessing.scetlib_ad import response as R

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loghist  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NEW = f"{A}/260930_stiff_wall_fits"
FITS = [
    # label, new postfix, ref fitresult, ref log(s), ref tau, new tau
    (
        "NOM",
        "NOMSTIFF",
        f"{A}/260928_lattice_y35_fits/fitresults_LATL4ZY35WALLWARM.hdf5",
        [f"{A}/260928_lattice_y35_fits/LATL4ZY35WALLWARM.log"],
    ),
    (
        "XW",
        "XWSTIFF",
        f"{A}/260924_y35_bin0xzero_fits/fitresults_Y35ZWALLWARM.hdf5",
        [f"{A}/260924_y35_bin0xzero_fits/Y35ZWALLWARM.log"],
    ),
    (
        "XL4Z",
        "XL4ZSTIFF",
        f"{A}/260929_l4zero_fits/fitresults_Y35ZWALLL4ZR.hdf5",
        [
            f"{A}/260929_l4zero_fits/Y35ZWALLL4Z.log",
            f"{A}/260929_l4zero_fits/Y35ZWALLL4ZR.log",
        ],
    ),
]
TAU_REF, TAU_NEW = 5.0, 8.0
M_REF, M_NEW = W.NP_DAMPING_MARGIN, 0.0
YMAX = 2.5  # binding |Y| the wall logs for these cards ("Binding |Y| = 2.5 from ... absYVGen")


def names_of(h):
    return [n.decode() if isinstance(n, bytes) else str(n) for n in h.axes[0]]


def load_fit(path):
    fr, meta = io_tools.get_fitresult(path, None, meta=True)
    h = fr["parms"].get()
    return dict(
        kind="fitresult",
        names=names_of(h),
        x=np.asarray(h.values()),
        sig=np.sqrt(np.asarray(h.variances())),
        nll=float(fr["nllvalreduced"]),
        edm=float(fr["edmval"]),
        meta=meta,
    )


def load_snapshot(path):
    with h5py.File(path, "r") as f:
        reason = f.attrs.get("reason")
        names = [
            n.decode() if isinstance(n, bytes) else str(n) for n in f["parms"][...]
        ]
        x = np.asarray(f["x"][...])
    return dict(
        kind=f"snapshot({reason})",
        names=names,
        x=x,
        sig=None,
        nll=None,
        edm=None,
        meta=None,
    )


def physical(fit, cfg, lam_names):
    phys, fitted, held = {}, [], {}
    for n in lam_names:
        a = P.corr_anchor_value(cfg, n)
        rp = P.reparam(n)
        if n in fit["names"] and rp is not None and rp[0] == "unit":
            i = fit["names"].index(n)
            phys[n] = a + rp[1][0] * fit["x"][i]
            fitted.append(n)
        elif n in fit["names"]:
            phys[n] = float(fit["x"][fit["names"].index(n)])
            fitted.append(n)
        else:
            phys[n] = a
            held[n] = a
    return phys, fitted, held


def wall_eval(phys, fitted, np_model, np_model_nu, margin):
    rows, tot = [], 0.0
    for c in W.damping_conditions(np_model, np_model_nu, ymax=YMAX, margin=margin):
        if not any(n in fitted for n in c.names):
            continue  # dropped by the wall as a held-only constant
        v = float(np.min(np.atleast_1d(c.value(phys, W.numpy_relu2))))
        pen = float(np.sum(c.penalty(phys, W.numpy_relu2)))
        tot += pen
        rows.append(
            dict(label=c.label, coeff=v, bound=c.bound, pen=pen, active=v < c.bound)
        )
    return rows, tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument(
        "--peek",
        action="store_true",
        help="use the latest (possibly periodic) snapshot of a RUNNING fit; NLL = last logged loss "
        "(the snapshot can lag it by up to --snapshotInterval) -- progress only, not a result",
    )
    args = ap.parse_args()
    out = {}
    for label, pf, ref_path, ref_logs in FITS:
        if args.only and label not in args.only:
            continue
        new_fr = f"{NEW}/fitresults_{pf}.hdf5"
        new_snap = f"{NEW}/snapshot_fitresults_{pf}.hdf5"
        new_log = f"{NEW}/{pf}.log"
        if not os.path.exists(new_log):
            print(f"== {label}: not started")
            continue
        ref = load_fit(ref_path)
        entry = R.corr_config_from_meta(ref["meta"])
        cfg = entry["config"]
        np_model, np_model_nu = W.forms_from_corr_config(cfg)
        lam_names = tuple(
            dict.fromkeys(W._TMD_LAMBDAS[np_model] + W._CS_LAMBDAS[np_model_nu])
        )
        lg_new = loghist.parse(new_log)
        finished = "Results written in file" in open(new_log, errors="replace").read()
        if finished and os.path.exists(
            new_fr
        ):  # rabbit creates/locks the file while running: never open it early
            new = load_fit(new_fr)
        elif (lg_new["result"] or args.peek) and os.path.exists(new_snap):
            new = load_snapshot(new_snap)
            if not new["kind"].startswith("snapshot(converged"):
                print(f"== {label}: snapshot is {new['kind']}, fit not converged yet")
            new["nll"] = (
                float(lg_new["result"]["fun"])
                if lg_new["result"]
                else float(lg_new["loss"][-1])
            )
            new["edm"] = lg_new["edm_log"]
        else:
            print(
                f"== {label}: running, {lg_new['n_iter']} iterations so far"
                + (f", last loss {lg_new['loss'][-1]:.10g}" if lg_new["n_iter"] else "")
            )
            continue
        assert new["names"] == ref["names"], "parameter lists differ"
        names = ref["names"]

        pr, fitted, held = physical(ref, cfg, lam_names)
        pn, fitted_n, _ = physical(new, cfg, lam_names)
        assert fitted == fitted_n
        wr5, pen_r5 = wall_eval(pr, fitted, np_model, np_model_nu, M_REF)
        wr0, pen_r0 = wall_eval(pr, fitted, np_model, np_model_nu, M_NEW)
        wn5, pen_n5 = wall_eval(pn, fitted, np_model, np_model_nu, M_REF)
        wn0, pen_n0 = wall_eval(pn, fitted, np_model, np_model_nu, M_NEW)
        e_r, e_n = np.exp(2 * TAU_REF), np.exp(2 * TAU_NEW)
        base_ref = ref["nll"] - e_r * pen_r5
        base_new = new["nll"] - e_n * pen_n0
        ref_under_new = base_ref + e_n * pen_r0
        new_under_ref = base_new + e_r * pen_n5

        ia = names.index("alphaS")
        d_as = (
            new["x"][ia] - ref["x"][ia]
        )  # blinded offsets cancel (same parameter, same data family)
        s_ref = ref["sig"][ia]
        s_new = new["sig"][ia] if new["sig"] is not None else float("nan")

        pulls = (new["x"] - ref["x"]) / np.where(ref["sig"] > 0, ref["sig"], np.nan)
        order = np.argsort(-np.nan_to_num(np.abs(pulls)))[:8]
        lam_rows = []
        for n in lam_names:
            lam_rows.append(
                dict(
                    name=n,
                    how=("fitted" if n in fitted else "held"),
                    ref=pr[n],
                    new=pn[n],
                    d_over_sig=(float(pulls[names.index(n)]) if n in names else None),
                )
            )

        lg_ref = [loghist.parse(p) for p in ref_logs]
        strip = lambda d: {
            k: v for k, v in d.items() if k not in ("loss", "dt", "elapsed")
        }  # noqa: E731
        res = dict(
            label=label,
            postfix=pf,
            new_source=new["kind"],
            ref=ref_path,
            forms=[np_model, np_model_nu],
            fitted=fitted,
            held=held,
            nll_new=new["nll"],
            nll_ref=ref["nll"],
            base_ref=base_ref,
            base_new=base_new,
            ref_under_new=ref_under_new,
            new_under_ref=new_under_ref,
            dnll_newobj=new["nll"]
            - ref_under_new,  # the minimiser's gain on the new objective
            dnll_refobj=new_under_ref
            - ref["nll"],  # >= 0 if ref was the ref objective's minimum
            dbase=base_new - base_ref,
            pen_ref={"m5e-3": pen_r5, "m0": pen_r0},
            pen_new={"m5e-3": pen_n5, "m0": pen_n0},
            wall_new_obj_contrib=e_n * pen_n0,
            wall_ref_obj_contrib=e_r * pen_r5,
            edm_new=new["edm"],
            edm_ref=ref["edm"],
            dalphaS_over_sig_ref=float(d_as / s_ref),
            sig_ratio=float(s_new / s_ref),
            lambdas=lam_rows,
            faces={"ref_m5e-3": wr5, "ref_m0": wr0, "new_m5e-3": wn5, "new_m0": wn0},
            top_shifts=[(names[i], float(pulls[i])) for i in order],
            max_abs_shift=float(np.nanmax(np.abs(pulls))),
            minimiser_new=strip(lg_new),
            minimiser_ref=[strip(x) for x in lg_ref],
        )
        out[label] = res
        # ---- print
        print(
            f"\n===== {label}  ({pf}, from {new['kind']}; forms {np_model}/{np_model_nu}; fitted {fitted}; held {held})"
        )
        print(f"NLL new (tau 8, m 0)          {new['nll']:.10f}")
        print(f"NLL ref (tau 5, m 5e-3)       {ref['nll']:.10f}")
        print(
            f"ref vector under NEW obj      {ref_under_new:.10f}   -> minimiser gain {res['dnll_newobj']:+.6g}"
        )
        print(
            f"new vector under REF obj      {new_under_ref:.10f}   -> dNLL(ref settings) {res['dnll_refobj']:+.6g}"
        )
        print(
            f"unwalled base: ref {base_ref:.10f}  new {base_new:.10f}  d {res['dbase']:+.6g}"
        )
        print(
            f"wall contrib: ref e^10*pen5 {e_r * pen_r5:.4g}; new e^16*pen0 {e_n * pen_n0:.4g}"
            f"  (pen0 new {pen_n0:.3g}, pen0 ref {pen_r0:.3g})"
        )
        print(f"EDM new {new['edm']}  ref {ref['edm']}")
        print(
            f"d(alphaS)/sigma_ref = {res['dalphaS_over_sig_ref']:+.4f}   sigma_new/sigma_ref = {res['sig_ratio']:.4f}  (BLINDED: diffs only)"
        )
        print("lambdas (physical):")
        for r in lam_rows:
            ds = f"{r['d_over_sig']:+.3f}" if r["d_over_sig"] is not None else "-"
            print(
                f"   {r['name']:14s} {r['how']:7s} ref {r['ref']:+.6f}  new {r['new']:+.6f}  d/sig_ref {ds}"
            )
        print(
            "armed conditions: coeff ref -> new   [active@0 ref/new]  [active@5e-3 ref/new]"
        )
        for a5, a0, b5, b0 in zip(wr5, wr0, wn5, wn0):
            print(
                f"   {a0['label']:58s} {a0['coeff']:+.6g} -> {b0['coeff']:+.6g}   "
                f"[{int(a0['active'])}/{int(b0['active'])}] [{int(a5['active'])}/{int(b5['active'])}]  pen0 new {b0['pen']:.3g}"
            )
        print(
            "largest |d/sig_ref|:",
            ", ".join(f"{n} {v:+.3f}" for n, v in res["top_shifts"]),
        )
        m = res["minimiser_new"]
        print(
            f"minimiser new: iters {m['n_iter']} {m['result']} rejected {m['n_rejected']} (longest run {m['longest_rejected_run']}),"
            f" increases {m['n_increase']}, plateau {m['longest_plateau']}, dt med {m['dt_median']:.0f}s max {m['dt_max']:.0f}s,"
            f" timing {m['timing']}, restarts {m['restarts']}"
        )
        for mr, p in zip(res["minimiser_ref"], ref_logs):
            print(
                f"minimiser ref [{os.path.basename(p)}]: iters {mr['n_iter']} nhev {mr['result'].get('nhev')} rejected {mr.get('n_rejected')}"
                f" dt med {mr.get('dt_median', 0):.0f}s timing {mr['timing']}"
            )
    if args.json:
        with open(args.json, "w") as f:
            json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main()
