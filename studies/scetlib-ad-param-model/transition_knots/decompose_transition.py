#!/usr/bin/env python3
"""Split the model-vs-TEMPLATE transition disagreement into OURS and THEIRS.

Three predictions of the same transition-point variation, all as
variation/central RESPONSES on the card's own (|Y|, qT) gen bins:

  model    sigma_par(var) / sigma_par(anchor)   -- AD member interpolation
  runcard  sigma_run(var) / sigma_par(anchor)   -- the SAME code, but with the
                                                   transition written into the
                                                   card, so the beam
                                                   convolutions are REFILLED at
                                                   the shifted muF. No
                                                   interpolation anywhere.
  template Corr[var] / Corr[central]            -- the production correction,
                                                   SCETlib resummed matched to
                                                   DYTurbo fixed order

so that

  ours   = model / runcard - 1     (our interpolation + coordinate error only:
                                    identical physics, identical nonsingular)
  theirs = runcard / template - 1  (same resummed piece, DIFFERENT nonsingular
                                    and possibly a different matching)
  total  = model / template - 1    and (1+ours)(1+theirs) must equal (1+total).

Also emits the CENTRAL shape ratio model/template per qT bin, normalised to its
own median, which is the observable for the "is the template a fair reference
here" correlation test: if the two matched constructions differ in qT 18-44,
the central mismatch is structured there and correlates with `theirs`.

sigma_run(anchor) is not computed: a third configure() in one process segfaults
(SCETlib global state), and sigma_par(anchor) equals it to 4e-16 -- both are the
same calculation at the same card, one with autodiff registered.
"""
import argparse
import configparser
import json
import math
import os
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)

QT_EDGES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28,
            33, 44, 100]
Y_EDGES = [0, 0.15, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.5]

PARAM_OF = {"x1": "scale_x1", "x2": "scale_x2", "x3": "scale_x3"}


def make_bins(qt_lo, iy):
    out = []
    for lo in qt_lo:
        k = QT_EDGES.index(lo)
        out.append([60.0, 120.0, Y_EDGES[iy], Y_EDGES[iy + 1],
                    QT_EDGES[k], QT_EDGES[k + 1]])
    return np.asarray(out, float)


def _eval(sigma, bins, p):
    sigma.sigma_binned_batch(bins, p)
    out = sigma.sigma_binned_batch(bins, p)
    v = out[0] if isinstance(out, (tuple, list)) else out
    return np.asarray(v, float).reshape(-1)


def _conf_with_tp(base, x1, x2, x3, out):
    c = configparser.ConfigParser(inline_comment_prefixes="#")
    c.read(base)
    c["Calculation_settings"]["transition_points"] = f"[{x1}, {x2}, {x3}]"
    with open(out, "w") as f:
        c.write(f)
    return out


def merge_matrix(fine, coarse, tol=1e-9):
    fine, coarse = np.asarray(fine, float), np.asarray(coarse, float)
    M = np.zeros((coarse.size - 1, fine.size - 1))
    for k in range(coarse.size - 1):
        lo, hi = coarse[k], coarse[k + 1]
        idx = [i for i in range(fine.size - 1)
               if fine[i] >= lo - tol and fine[i + 1] <= hi + tol]
        M[k, idx] = 1.0
    return M


def template_response(corr_path, label, qt_lo, iy):
    """Corr[label]/Corr[central] and Corr[central] on the model's bins."""
    import pickle

    import lz4.frame
    with lz4.frame.open(corr_path, "rb") as f:
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
    Ye = np.asarray([Y_EDGES[iy], Y_EDGES[iy + 1]], float)
    Te = np.asarray([QT_EDGES[QT_EDGES.index(lo)] for lo in qt_lo]
                    + [QT_EDGES[QT_EDGES.index(qt_lo[-1]) + 1]], float)
    MY = merge_matrix(ax["absY"].edges, Ye)
    MT = merge_matrix(ax["qT"].edges, Te)
    cen = (MY @ vals[:, :, labels.index("central")] @ MT.T).reshape(-1)
    var = (MY @ vals[:, :, labels.index(label)] @ MT.T).reshape(-1)
    return var / cen, cen, labels


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--x1", type=float, default=0.2)
    ap.add_argument("--x2", type=float, default=0.6)
    ap.add_argument("--x3", type=float, default=1.0)
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("--iy", type=int, default=0)
    ap.add_argument("--qt-lo", type=float, nargs="+",
                    default=[float(x) for x in QT_EDGES[:-1]])
    ap.add_argument("--threads", type=int, default=32)
    ap.add_argument("--corr", default=None)
    ap.add_argument("--label", default=None,
                    help="template variation label, e.g. "
                         "transition_points0.2_0.35_1.0")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    bins = make_bins(args.qt_lo, args.iy)
    tag = f"{args.x1}_{args.x2}_{args.x3}"
    tmp = os.path.join(os.path.dirname(os.path.abspath(args.out)),
                       f"_tp_{tag}_k{args.knot:.6f}.conf")
    _conf_with_tp(args.base, args.x1, args.x2, args.x3, tmp)

    _, s_run = configure(tmp, threads=args.threads, diff_scales=False)
    run_var = _eval(s_run, bins, np.asarray(s_run.gradient_central(), float))

    _, s_par = configure(args.base, threads=args.threads, diff_scales=True)
    sing, nons = s_par.sub_pieces()
    names = list(s_par.gradient_param_names())
    p0 = np.asarray(s_par.gradient_central(), float)
    cp = configparser.ConfigParser(inline_comment_prefixes="#")
    cp.read(args.base)
    pdf_set = cp["QCD"]["pdf_set"]
    nf = cp["QCD"].getint("nf", fallback=5)

    s_par.prepare(bins, p0)
    sing.build_bin_rules(bins, p0, n_train=9, n_hvp=1, seed=4242,
                         n_jobs=args.threads)
    sets = [pdf_set, pdf_set]
    mem = np.array([0, 0], dtype=np.int32)
    f = args.knot
    sing.build_pdf_variations(sets, mem, nf, p0, n_train_var=3, n_eig=0,
                              as_cen=0.0, as_step=0.0,
                              muf_lo=1.0 / f, muf_hi=f)
    nons.build_fo_pdf_variations(sets, mem, nf, bins,
                                 np.asarray(nons.gradient_central()),
                                 n_eig=0, as_cen=0.0, as_step=0.0,
                                 muf_lo=1.0 / f, muf_hi=f)

    def rule(q):
        return np.asarray(sing.sigma_binned_rule_batch(bins, q)["value"],
                          float).reshape(-1)

    par_cen = rule(p0)
    p = p0.copy()
    for k, v, d in (("x1", args.x1, 0.2), ("x2", args.x2, 0.6),
                    ("x3", args.x3, 1.0)):
        if abs(v - d) > 1e-12:
            p[names.index(PARAM_OF[k])] = v
    par_var = rule(p)

    R_model = par_var / par_cen
    R_run = run_var / par_cen
    out = {"x1": args.x1, "x2": args.x2, "x3": args.x3, "knot": f,
           "iy": args.iy, "bins": bins.tolist(),
           "par_cen": par_cen.tolist(), "par_var": par_var.tolist(),
           "run_var": run_var.tolist(),
           "R_model": R_model.tolist(), "R_runcard": R_run.tolist()}

    if args.corr and args.label:
        R_tpl, tpl_cen, _ = template_response(args.corr, args.label,
                                              args.qt_lo, args.iy)
        out["R_template"] = R_tpl.tolist()
        out["tpl_cen"] = tpl_cen.tolist()
        ours = R_model / R_run - 1.0
        theirs = R_run / R_tpl - 1.0
        total = R_model / R_tpl - 1.0
        cshape = par_cen / tpl_cen
        cshape = cshape / np.median(cshape)
        out.update(ours=ours.tolist(), theirs=theirs.tolist(),
                   total=total.tolist(), central_shape=cshape.tolist())
        print(f"\ntransition_points [{args.x1}, {args.x2}, {args.x3}], "
              f"|Y| bin {args.iy}, knot f = {f:g}")
        print(f"{'qT bin':>12}{'R_model-1':>12}{'R_run-1':>12}{'R_tpl-1':>12}"
              f"{'ours':>11}{'theirs':>11}{'total':>11}{'cen shape':>11}")
        for k, b in enumerate(bins):
            print(f"[{b[4]:4g},{b[5]:4g}]".rjust(12)
                  + f"{R_model[k]-1:>12.3e}{R_run[k]-1:>12.3e}{R_tpl[k]-1:>12.3e}"
                  + f"{ours[k]:>11.3e}{theirs[k]:>11.3e}{total[k]:>11.3e}"
                  + f"{cshape[k]-1:>+11.3e}")
        clo = np.abs((1 + ours) * (1 + theirs) - (1 + total)).max()
        print(f"closure of the decomposition, max|(1+o)(1+t)-(1+T)| = {clo:.2e}")
    json.dump(out, open(args.out, "w"), indent=1)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
