#!/usr/bin/env python3
"""A/B a differentiable scale direction: PARAMETER route vs RUNCARD route.

The question this answers is always the same one: for the *identical physical
change*, does SCETlib's autodiff path (``set_diff_scales(1)`` + a live parameter)
give the same answer as the production path (the value written into the runcard,
autodiff off)? If it does not, the derivative our fit uses is wrong no matter how
well the cache replays it.

This is the test that settled ``scale_x2`` (the transition points): the runcard
route reproduces the production CorrZ template to 2e-6, the parameter route comes
out with the *wrong sign*. It is written here as a reusable tool because every
differentiable scale needs the same treatment.

Three routes, one per process (see NOTE on segfaults):

  ``--mode runcard``  two ``configure()`` calls, autodiff OFF, the change made in
                      the runcard. This is the REFERENCE -- the production
                      corrections were made this way.
  ``--mode param``    one ``configure()`` call, autodiff ON, the change made by
                      moving the registered parameter. This is OUR path.
  ``--mode corr``     the production template read straight out of the corr file.
                      Needs no SCETlib, so it runs anywhere.

then ``--mode compare`` prints the table from the JSONs.

NOTE on segfaults: a third ``configure()`` in one process crashes (SCETlib global
state), so each mode runs standalone and hands its numbers over as JSON. Do not
"tidy" this into one process.

Example (kappa_R at low qT, which is where the model disagrees by 4e-2):

    B=$CACHE/base_from_reference.conf
    sed 's/^\\[Calculation_settings\\]/[Calculation_settings]\\nkappafo = 0.5\\nkappaf = 2./' $B > var.conf
    ./ab_scale_route.py --mode runcard --base $B --var var.conf --out A.json
    ./ab_scale_route.py --mode param   --base $B --param scale_kappa_R=0.5 --out B.json
    ./ab_scale_route.py --mode corr    --corr $CORRZ --label 'kappaFO0.5-kappaf2.' --out C.json
    ./ab_scale_route.py --mode compare --json A.json B.json C.json
"""
import argparse
import json
import os
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)
sys.path.insert(0, os.path.join(WREM, "scripts", "rabbit", "scetlib_ad"))

# the card's gen grid: Q [60,120], 10 |Y| slices, 21 qT bins
QT_EDGES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 33, 44, 100]
Y_EDGES = [0, 0.15, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.5]
DEFAULT_QT_LO = [0.0, 1.0, 2.0, 4.0, 8.0, 33.0]


def make_bins(qt_lo, iy):
    """[[Q_lo, Q_hi, Y_lo, Y_hi, qT_lo, qT_hi], ...] -- the cache's own layout."""
    out = []
    for lo in qt_lo:
        k = QT_EDGES.index(lo)
        out.append([60.0, 120.0, Y_EDGES[iy], Y_EDGES[iy + 1], QT_EDGES[k], QT_EDGES[k + 1]])
    return np.asarray(out, float)


def _eval(sigma, bins, p):
    # first call warms the node cache; the second is the one that is stable
    sigma.sigma_binned_batch(bins, p)
    out = sigma.sigma_binned_batch(bins, p)
    v = out[0] if isinstance(out, (tuple, list)) else out
    return np.asarray(v, float).reshape(-1)


def _apply(sigma, tokens):
    names = list(sigma.gradient_param_names())
    p = np.asarray(sigma.gradient_central(), float).copy()
    for tok in tokens:
        name, val = tok.split("=")
        if name not in names:
            raise SystemExit(
                f"{name!r} is not a registered parameter. Registered: {names}"
            )
        p[names.index(name)] = float(val)
    return p


def run_runcard(args, bins):
    """The change written into the runcard.

    Autodiff is OFF by default, which is the production path. ``--diff-scales``
    turns it on and ``--var-param`` moves a parameter on top of the varied
    runcard, which together let the two routes be MIXED -- the central from one
    configuration and the variation from another. That is how the muB_min/muS_min
    floor hypothesis is testable without rebuilding SCETlib: production
    compensates the floors by w_fo = mu_FO/Q, so a runcard at kappa_FO = 0.5
    effectively doubles them, while the autodiff path leaves prof_w_fo at its
    configure-time value. Doubling the floors in the varied runcard by hand and
    moving kappa_R there should then reproduce the production ratio exactly.
    """
    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    kw = dict(
        threads=args.threads,
        diff_scales=args.diff_scales,
        fo_resolve_muR=args.fo_resolve,
    )
    _, s_cen = configure(args.base, **kw)
    cen = _eval(s_cen, bins, np.asarray(s_cen.gradient_central(), float))
    _, s_var = configure(args.var, **kw)
    var = _eval(s_var, bins, _apply(s_var, args.var_param))
    return cen, var


def run_param(args, bins):
    """Autodiff ON, the change made by moving the parameter: our path."""
    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    _, sigma = configure(
        args.base, threads=args.threads, diff_scales=True, fo_resolve_muR=args.fo_resolve
    )
    p0 = np.asarray(sigma.gradient_central(), float)
    cen = _eval(sigma, bins, p0)
    var = _eval(sigma, bins, _apply(sigma, args.param))
    return cen, var


def run_corr(args, bins):
    """The production template, bin-integrated onto the same bins."""
    from validate_variations import central_label, load_corr

    h = load_corr(args.corr)
    labels = [str(x) for x in h.axes["vars"]]
    if args.label not in labels:
        raise SystemExit(f"{args.label!r} not in the corr file. Have: {labels}")
    ax = {a.name: i for i, a in enumerate(h.axes)}
    v = np.asarray(h.values(flow=False))
    qt_f = np.asarray(h.axes["qT"].edges, float)
    y_f = np.asarray(h.axes["absY"].edges, float)

    def slab(label):
        idx = [slice(None)] * v.ndim
        idx[ax["Q"]] = 0
        idx[ax["charge"]] = 0
        idx[ax["vars"]] = labels.index(label)
        s = v[tuple(idx)]
        rest = [a.name for a in h.axes if a.name not in ("Q", "charge", "vars")]
        return s if rest.index("absY") == 0 else s.T  # -> (absY, qT)

    # Build the merge only for the bins actually asked for: the correction's
    # absY grid is NOT a superset of the card's everywhere (it breaks at 1.3/1.6),
    # so a full merge_matrix over all 10 slices raises even when the slice we want
    # is fine. Align per requested bin instead, and say which bin failed.
    def row(fine, lo, hi, what, tol=1e-9):
        idx = [
            i
            for i in range(fine.size - 1)
            if fine[i] >= lo - tol and fine[i + 1] <= hi + tol
        ]
        if not idx or abs(fine[idx[0]] - lo) > tol or abs(fine[idx[-1] + 1] - hi) > tol:
            raise SystemExit(
                f"{what} [{lo}, {hi}] is not a sub-binning of the correction's grid "
                f"({what} edges near it: {fine[max(0, np.searchsorted(fine, lo) - 2):np.searchsorted(fine, hi) + 2]})"
            )
        m = np.zeros(fine.size - 1)
        m[idx] = 1.0
        return m

    def onto(label):
        s = slab(label)  # (absY, qT)
        return np.asarray(
            [
                row(y_f, b[2], b[3], "absY") @ s @ row(qt_f, b[4], b[5], "qT")
                for b in bins
            ],
            float,
        )

    return onto(central_label(labels)), onto(args.label)


def compare(paths):
    d = [json.load(open(p)) for p in paths]
    bins = np.asarray(d[0]["bins"], float)
    for x in d[1:]:
        if not np.allclose(np.asarray(x["bins"], float), bins):
            raise SystemExit("the JSONs are not on the same bins")
    hdr = f"{'|Y|':>12} {'qT':>12}"
    for x in d:
        hdr += f" {x['tag'][:20]:>20}"
    if len(d) > 1:
        hdr += f" {'ratio col2/col1':>16}"
    print(hdr)
    print("-" * len(hdr))
    rows = []
    for k, b in enumerate(bins):
        line = f" [{b[2]:4g},{b[3]:4g}] [{b[4]:4g},{b[5]:4g}]"
        r = [x["var"][k] / x["cen"][k] for x in d]
        for val in r:
            line += f" {val:20.6f}"
        if len(r) > 1:
            line += f" {r[1] / r[0]:16.6f}"
        rows.append(r)
        print(line)
    if len(d) > 1:
        rows = np.asarray(rows)
        print()
        for j in range(1, rows.shape[1]):
            dev = np.abs(rows[:, j] / rows[:, 0] - 1.0)
            print(
                f"  {d[j]['tag']} vs {d[0]['tag']}: "
                f"max |ratio/ratio-1| = {dev.max():.3e} "
                f"at qT [{bins[dev.argmax(),4]:g},{bins[dev.argmax(),5]:g}]"
            )


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", required=True,
                    choices=["runcard", "param", "corr", "compare"])
    ap.add_argument("--base", help="central runcard")
    ap.add_argument("--var", help="runcard with the change applied (mode runcard)")
    ap.add_argument("--var-param", nargs="+", default=[],
                    help="NAME=VALUE applied on top of --var (mode runcard), so a "
                         "runcard change and a parameter change can be combined")
    ap.add_argument("--diff-scales", action="store_true",
                    help="mode runcard: leave autodiff ON. Off (the default) is "
                         "the production path and the reference")
    ap.add_argument("--param", nargs="+", default=[],
                    help="NAME=VALUE for the registered parameter (mode param)")
    ap.add_argument("--corr", help="the *CorrZ.pkl.lz4 (mode corr)")
    ap.add_argument("--label", help="its variation label (mode corr)")
    ap.add_argument("--json", nargs="+", help="the JSONs to tabulate (mode compare); "
                                              "the FIRST is the reference column")
    ap.add_argument("--out", help="where to write this route's numbers")
    ap.add_argument("--tag", help="column name in the table (default: the mode)")
    ap.add_argument("--iy", type=int, default=0, help="which |Y| slice (default 0)")
    ap.add_argument("--qt-lo", type=float, nargs="+", default=DEFAULT_QT_LO,
                    help="low edges of the qT bins to probe")
    ap.add_argument("--threads", type=int, default=64)
    ap.add_argument("--fo-resolve", action="store_true",
                    help="resolve the fixed-order muR into the frozen grid; the "
                         "cache is built WITH this, production runs WITHOUT it, so "
                         "it is itself a difference worth A/B-ing for kappa_R")
    args = ap.parse_args()

    if args.mode == "compare":
        return compare(args.json)

    bins = make_bins(args.qt_lo, args.iy)
    cen, var = {"runcard": run_runcard, "param": run_param, "corr": run_corr}[args.mode](
        args, bins
    )
    rec = {
        "tag": args.tag or args.mode,
        "mode": args.mode,
        "bins": bins.tolist(),
        "cen": cen.tolist(),
        "var": var.tolist(),
        "fo_resolve": bool(args.fo_resolve),
        "param": args.param,
        "var_param": args.var_param,
        "diff_scales": bool(getattr(args, "diff_scales", False)),
        "label": args.label,
    }
    if args.out:
        with open(args.out, "w") as f:
            json.dump(rec, f, indent=1)
        print(f"wrote {args.out}")
    for k, b in enumerate(bins):
        print(f"  qT [{b[4]:4g},{b[5]:4g}]  var/cen = {var[k]/cen[k]:.6f}")


if __name__ == "__main__":
    main()
