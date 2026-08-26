#!/usr/bin/env python3
"""Per-bin model-vs-TEMPLATE transition response, and the central shape, from
an existing cache. No SCETlib run: cache + corr file only.

Emits, for each transition direction and for each qT bin, both |Y|-integrated
(what the validate_variations plot shows) and at |Y| bin 0 (what the runcard
route is measured in):

    R_model     sigma_model(var)/sigma_model(anchor)
    R_template  Corr[var]/Corr[central]
    total       R_model/R_template - 1
    cen_shape   sigma_model(anchor)/Corr[central], normalised to its own median

`total` is the SUM of our interpolation error (model vs an exact runcard refill)
and any genuine difference between the two matched constructions (SCETlib+its
own analytic V+jet here, SCETlib+DYTurbo in the template). cen_shape is the
observable that tests the second: a matching difference in qT 18-44 must show
up as structure there in the CENTRAL, which no response ratio can hide.
"""
import argparse
import json
import os
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)

DIRECTIONS = {
    "transition_points0.2_0.35_1.0": {"scale_x2": 0.35},
    "transition_points0.2_0.75_1.0": {"scale_x2": 0.75},
    "transition_points0.3_0.6_0.9": {"scale_x1": 0.3, "scale_x3": 0.9},
}


def merge_matrix(fine, coarse, tol=1e-9):
    fine, coarse = np.asarray(fine, float), np.asarray(coarse, float)
    M = np.zeros((coarse.size - 1, fine.size - 1))
    for k in range(coarse.size - 1):
        lo, hi = coarse[k], coarse[k + 1]
        idx = [i for i in range(fine.size - 1)
               if fine[i] >= lo - tol and fine[i + 1] <= hi + tol]
        M[k, idx] = 1.0
    return M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--conf", required=True)
    ap.add_argument("--corr", required=True)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    import pickle

    import lz4.frame

    from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

    core = ScetlibADXsec(args.conf, args.cache, threads=args.threads)
    names = list(core.param_names)
    b = core.bins
    yl = np.unique(np.round(b[:, 2:4], 12), axis=0)
    tl = np.unique(np.round(b[:, 4:6], 12), axis=0)
    yl, tl = yl[np.argsort(yl[:, 0])], tl[np.argsort(tl[:, 0])]
    Ye = np.concatenate([yl[:, 0], yl[-1:, 1]])
    Te = np.concatenate([tl[:, 0], tl[-1:, 1]])
    fold = core.fold_for([("ptVGen", Te), ("absYVGen", Ye)], b[0, 0], b[0, 1])
    anchor = core.anchor.copy()

    def model(ov):
        p = anchor.copy()
        for k, v in ov.items():
            p[names.index(k)] = v
        vals, _ = core.values_and_jacobian(p)
        return fold(np.asarray(vals, float)).reshape(Te.size - 1, Ye.size - 1).T

    with lz4.frame.open(args.corr, "rb") as f:
        d = pickle.load(f)
    boson = next(k for k in d if k in ("Z", "W", "Wplus", "Wminus"))
    inner = d[boson]
    key = next(k for k in inner if k.endswith("_hist") and "minnlo" not in k)
    h = inner[key]
    ax = {a.name: a for a in h.axes}
    labels = [str(x) for x in ax["vars"]]
    vals = np.asarray(h.values(flow=False))
    dims = [a.name for a in h.axes]
    vals = np.squeeze(vals, axis=(dims.index("Q"), dims.index("charge")))
    order = [dd for dd in dims if dd not in ("Q", "charge")]
    vals = np.moveaxis(vals, [order.index("absY"), order.index("qT"),
                              order.index("vars")], [0, 1, 2])
    MY, MT = merge_matrix(ax["absY"].edges, Ye), merge_matrix(ax["qT"].edges, Te)
    ref = lambda L: MY @ vals[:, :, labels.index(L)] @ MT.T   # noqa: E731

    s_cen, r_cen = model({}), ref("central")
    out = {"qT_edges": Te.tolist(), "Y_edges": Ye.tolist(), "dirs": {}}

    for how, sel in (("Yint", None), ("iy0", 0)):
        if sel is None:
            sc, rc = s_cen.sum(axis=0), r_cen.sum(axis=0)
        else:
            sc, rc = s_cen[sel], r_cen[sel]
        cs = sc / rc
        cs = cs / np.median(cs)
        out.setdefault("central_shape", {})[how] = (cs - 1.0).tolist()

    for L, ov in DIRECTIONS.items():
        s_var, r_var = model(ov), ref(L)
        rec = {}
        for how, sel in (("Yint", None), ("iy0", 0)):
            if sel is None:
                rm = s_var.sum(axis=0) / s_cen.sum(axis=0)
                rr = r_var.sum(axis=0) / r_cen.sum(axis=0)
            else:
                rm, rr = s_var[sel] / s_cen[sel], r_var[sel] / r_cen[sel]
            rec[how] = {"R_model": rm.tolist(), "R_template": rr.tolist(),
                        "total": (rm / rr - 1.0).tolist()}
        out["dirs"][L] = rec

    json.dump(out, open(args.out, "w"), indent=1)
    for L in DIRECTIONS:
        print(f"\n=== {L}")
        print(f"{'qT bin':>12}{'R_mod-1 (Yint)':>16}{'R_tpl-1 (Yint)':>16}"
              f"{'total (Yint)':>14}{'total (iy0)':>14}{'cen shape iy0':>15}")
        for k in range(Te.size - 1):
            print(f"[{Te[k]:4g},{Te[k+1]:4g}]".rjust(12)
                  + f"{out['dirs'][L]['Yint']['R_model'][k]-1:>16.3e}"
                  + f"{out['dirs'][L]['Yint']['R_template'][k]-1:>16.3e}"
                  + f"{out['dirs'][L]['Yint']['total'][k]:>14.3e}"
                  + f"{out['dirs'][L]['iy0']['total'][k]:>14.3e}"
                  + f"{out['central_shape']['iy0'][k]:>+15.3e}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
