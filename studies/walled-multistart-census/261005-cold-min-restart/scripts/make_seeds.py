#!/usr/bin/env python3
"""Seeds for the cold-min restart: C (CCWALLCOLDR) mapped into the NOMSTIFF (1a) and XWSTIFF (1b) frames.

Mapping rules (checked here, not assumed):
  * BY NAME. rabbit's load_fitresult intersects names, so a parameter missing from the seed would keep the
    fitter's COLD default. The seed therefore carries the TARGET reference's full name list: x = x_ref, then
    every name also present in C is overwritten with C's value. Names in the target but not in C keep the
    reference value (listed); names in C but not in the target are dropped (listed).
  * theta frame. theta = (lambda - c0)/width with c0 = the anchor of the CARD's theory correction (param_model
    _resolve_anchor, anchor_source=correction). Checked: every param-model anchor value from C's meta chain equals
    the target's, and the REPARAM width is today's code for both (C's stored NLL was reproduced by today's code at
    its stored x in walled-two-minima/260930-walled-chord, gate 2.3e-12). So theta carries over 1:1; any mismatch
    raises.
  * alphaS blinding: same name, same additive scale (model declares none), both cards' data_obs integral ->
    identical offset (scripts/blinding_check.py, rabbit's own Blinding class). So blinded x carries over verbatim.
Writes seeds with rabbit.snapshot.write_snapshot (the --externalPostfit flat format) and a bit-exact round trip.
Prints only DIFFERENCES for alphaS (in sigma of the reference). No absolute alphaS anywhere.
"""
import json
import os
import sys

import h5py
import numpy as np
from rabbit import io_tools, snapshot

from wremnants.postprocessing.scetlib_ad import np_damping_wall as W
from wremnants.postprocessing.scetlib_ad import params as P
from wremnants.postprocessing.scetlib_ad import response as R

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
C_PATH = f"{A}/260917_cc_fits_wall/fitresults_CCWALLCOLDR.hdf5"
REFS = {
    "1a": ("NOMSTIFF", f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"),
    "1b": ("XWSTIFF", f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5"),
}
OUT = f"{A}/261005_cold_min_restart/seeds"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YMAX, MARGIN, TAU = 2.5, 0.0, 8.0


def load(path):
    fr, meta = io_tools.get_fitresult(path, None, meta=True)
    h = fr["parms"].get()
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in h.axes[0]]
    cfg = R.corr_config_from_meta(meta)["config"]
    return dict(
        names=names,
        x=np.asarray(h.values(), float),
        sig=np.sqrt(np.asarray(h.variances(), float)),
        nll=float(fr["nllvalreduced"]),
        cfg=cfg,
    )


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


def wall(phys, fitted, cfg):
    np_model, np_model_nu = W.forms_from_corr_config(cfg)
    rows, pen = [], 0.0
    for c in W.damping_conditions(np_model, np_model_nu, ymax=YMAX, margin=MARGIN):
        if not any(n in fitted for n in c.names):
            continue
        v = float(np.min(np.atleast_1d(c.value(phys, W.numpy_relu2))))
        p = float(c.penalty(phys, W.numpy_relu2))
        pen += p
        rows.append(
            dict(
                label=c.label,
                coeff=v,
                violated=v < c.bound,
                penalty_x_e2tau=p * np.exp(2 * TAU),
            )
        )
    return rows, pen * np.exp(2 * TAU)


def main():
    os.makedirs(OUT, exist_ok=True)
    C = load(C_PATH)
    report = {}
    for tag, (rname, rpath) in REFS.items():
        ref = load(rpath)
        # ---- anchors: every param-model name with a correction anchor key must agree
        pm_names = [n for n in ref["names"] if P.corr_anchor_key(n) is not None] + [
            n
            for n in C["names"]
            if P.corr_anchor_key(n) is not None and n not in ref["names"]
        ]
        anc = {
            n: (P.corr_anchor_value(C["cfg"], n), P.corr_anchor_value(ref["cfg"], n))
            for n in pm_names
        }
        bad = {n: v for n, v in anc.items() if v[0] != v[1]}
        if bad:
            sys.exit(
                f"[{tag}] ANCHOR MISMATCH {list(bad)} -- theta would need re-anchoring; refusing"
            )
        np_model, np_model_nu = W.forms_from_corr_config(ref["cfg"])
        if (np_model, np_model_nu) != W.forms_from_corr_config(C["cfg"]):
            sys.exit(f"[{tag}] NP forms differ")
        lam_names = tuple(
            dict.fromkeys(W._TMD_LAMBDAS[np_model] + W._CS_LAMBDAS[np_model_nu])
        )

        # ---- by-name map
        cidx = {n: i for i, n in enumerate(C["names"])}
        x = ref["x"].copy()
        kept_ref = [n for n in ref["names"] if n not in cidx]
        dropped_C = [n for n in C["names"] if n not in set(ref["names"])]
        for i, n in enumerate(ref["names"]):
            if n in cidx:
                x[i] = C["x"][cidx[n]]
        same_order = C["names"] == ref["names"]

        seed = f"{OUT}/seed_{tag}_C_in_{rname}.hdf5"
        snapshot.write_snapshot(
            seed,
            np.array(ref["names"]),
            x,
            meta=dict(source=C_PATH, frame=rpath, rule="by-name; missing<-ref"),
        )
        with h5py.File(seed, "r") as f:
            xb, nb = f["x"][...], f["parms"][...].astype(str)
            assert "cov" not in f
        assert (
            np.array_equal(xb.view(np.uint64), x.view(np.uint64))
            and list(nb) == ref["names"]
        ), "round trip"

        # ---- describe the seed vs the reference (sigma of the reference)
        d = (x - ref["x"]) / ref["sig"]
        ia = ref["names"].index("alphaS")
        order = np.argsort(-np.abs(d))
        top = [(ref["names"][k], float(d[k])) for k in order[:15]]
        ph_seed, fitted = physical(dict(names=ref["names"], x=x), ref["cfg"], lam_names)
        ph_ref, _ = physical(ref, ref["cfg"], lam_names)
        ph_C, fitC = physical(C, C["cfg"], lam_names)
        wrows, wpen = wall(ph_seed, fitted, ref["cfg"])
        wrows_ref, wpen_ref = wall(ph_ref, fitted, ref["cfg"])
        pmask = np.array(
            [
                n == "alphaS"
                or n.startswith(("lambda", "delta_lambda", "resum", "pdfEig"))
                for n in ref["names"]
            ]
        )
        rep = dict(
            seed=seed,
            reference=rname,
            n_ref=len(ref["names"]),
            n_C=len(C["names"]),
            same_order=same_order,
            kept_from_reference=kept_ref,
            dropped_from_C=dropped_C,
            anchors_checked=len(anc),
            anchors_equal=True,
            dalphaS_over_sigref=float(d[ia]),
            norm_dtheta_sig=float(np.linalg.norm(d)),
            norm_dtheta_sig_parammodel=float(np.linalg.norm(d[pmask])),
            norm_dtheta_sig_nuisance=float(np.linalg.norm(d[~pmask])),
            half_norm2_nuisance=float(0.5 * np.sum(d[~pmask] ** 2)),
            top15_dtheta_sig=top,
            lambdas_C=ph_C,
            lambdas_seed=ph_seed,
            lambdas_ref=ph_ref,
            fitted_lambdas=fitted,
            wall_seed=wrows,
            wall_pen_seed=wpen,
            wall_ref=wrows_ref,
            wall_pen_ref=wpen_ref,
        )
        report[tag] = rep
        print(f"=== {tag}: C -> {rname} frame  seed {seed}")
        print(
            f"   names: ref {len(ref['names'])}, C {len(C['names'])}, identical order {same_order}"
        )
        print(f"   kept from {rname} (absent in C): {kept_ref}")
        print(f"   dropped from C (absent in {rname}): {dropped_C}")
        print(f"   anchors checked {len(anc)}: all equal")
        print(
            f"   dalphaS/sig_{rname} {d[ia]:+.4f}   ||dth/sig|| {np.linalg.norm(d):.3f} "
            f"(param model {np.linalg.norm(d[pmask]):.3f}, nuisances {np.linalg.norm(d[~pmask]):.3f})"
        )
        print("   top-15 |dth/sig|:", ", ".join(f"{n} {v:+.2f}" for n, v in top))
        print("   lambdas C   :", {k: round(v, 6) for k, v in ph_C.items()})
        print("   lambdas seed:", {k: round(v, 6) for k, v in ph_seed.items()})
        print(f"   lambdas {rname}:", {k: round(v, 6) for k, v in ph_ref.items()})
        print(
            f"   wall (tau 8, margin 0) seed penalty {wpen:.4g}  [ref {wpen_ref:.3g}]"
        )
        for r in wrows:
            print(
                f"      {r['label'][:60]:60s} coeff {r['coeff']:+.3e} {'VIOLATED' if r['violated'] else ''} "
                f"pen {r['penalty_x_e2tau']:.3g}"
            )
    with open(f"{TASK}/seed_mapping.json", "w") as f:
        json.dump(report, f, indent=1, default=float)
    print(f"wrote {TASK}/seed_mapping.json")


if __name__ == "__main__":
    main()
