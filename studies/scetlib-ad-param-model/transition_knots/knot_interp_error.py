#!/usr/bin/env python3
"""The muF interpolation error, isolated, at a SETTABLE knot spacing.

This is ../transition_variation_scan.py with the one thing that script could not
do: the knot spacing. It scanned the SIZE of the variation because
build_pdf_variations hard-refused any muf_lo/muf_hi but 0.5/2.0. With the
knot-spacing patch (worktree /work/submit/lavezzo/alphaS/scetlib-knots, branch
knot-spacing) that refusal became "reciprocal and ordered", and
Scale_provider's Vary.muf factor is driven from muf_hi -- so the SAME three-knot
quadratic can be sampled at knots kappa_F = 1/f, 1, f for any f.

WHAT IS MEASURED, and why it is the decisive observable

    dev = [param(x2)/param(0.6)] / [runcard(x2)/param(0.6)] - 1

The runcard route writes x2 into the card, so the beam convolutions are REFILLED
at the shifted muF -- exact, no interpolation. The parameter route moves x2 live
and lets bfc6be6's member interpolation carry the induced muF shift. The physics
is identical on both sides, so dev IS the interpolation error with nothing else
in it. No templates, no nonsingular mismatch, no cache tolerance.

THE PREDICTION. The interpolant is a quadratic through samples at
ln(kappa_F) = -h, 0, +h with h = ln(f). Two standard results:

  * at a displacement delta, the value error is (f'''/6) delta (delta^2 - h^2),
    so at fixed delta it scales as h^2;
  * its DERIVATIVE at the anchor is the central difference
    [F(h) - F(-h)]/(2h), whose error is (h^2/6) F'''(0) -- also h^2, and it does
    NOT vanish as delta -> 0.

The second is the one that matters here, and it explains why scanning the
variation size found a FLAT residual: an anchor-derivative error is flat by
construction. So flatness was never evidence against interpolation order, and
the only test that separates the two hypotheses is h itself.

  f = 2 -> h = 0.6931 ; f = sqrt(2) -> h = 0.3466. h^2 ratio 4.00.

  interpolation-limited  =>  dev(sqrt2) ~ dev(2) / 4
  floor                  =>  dev(sqrt2) ~ dev(2)

One x2 and one knot factor per process: the runcard side needs its own
configure() and a third configure() in one process segfaults (SCETlib global
state).
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

# The card's own gen grid. Copied rather than imported from ../ab_scale_route.py
# on purpose: the sibling study scripts are being edited by another session, and
# this measurement must not change underneath itself between the two arms.
QT_EDGES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28,
            33, 44, 100]
Y_EDGES = [0, 0.15, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.5]

# Where the x2 residual lives: zero below qT 16 (g_run = 1 and x2 does nothing
# there), largest in qT 18-28, gone again by 44.
DEFAULT_QT_LO = [18.0, 20.0, 24.0, 28.0, 33.0]


def make_bins(qt_lo, iy):
    """[[Q_lo, Q_hi, Y_lo, Y_hi, qT_lo, qT_hi], ...] -- the cache's own layout."""
    out = []
    for lo in qt_lo:
        k = QT_EDGES.index(lo)
        out.append([60.0, 120.0, Y_EDGES[iy], Y_EDGES[iy + 1],
                    QT_EDGES[k], QT_EDGES[k + 1]])
    return np.asarray(out, float)


def _eval(sigma, bins, p):
    # the first call warms the node cache; the second is the stable one
    sigma.sigma_binned_batch(bins, p)
    out = sigma.sigma_binned_batch(bins, p)
    v = out[0] if isinstance(out, (tuple, list)) else out
    return np.asarray(v, float).reshape(-1)


def _conf_with_x2(base, x2, out):
    """The base runcard with transition_points' middle entry replaced."""
    c = configparser.ConfigParser(inline_comment_prefixes="#")
    c.read(base)
    tp = c["Calculation_settings"]["transition_points"]
    lo, _mid, hi = (v.strip() for v in tp.strip("[] ").split(","))
    c["Calculation_settings"]["transition_points"] = f"[{lo}, {x2}, {hi}]"
    with open(out, "w") as f:
        c.write(f)
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--base")
    ap.add_argument("--x2", type=float)
    ap.add_argument("--knot", type=float, default=2.0,
                    help="muF knot factor f: members at kappa_F = 1/f and f")
    ap.add_argument("--qt-lo", type=float, nargs="+", default=DEFAULT_QT_LO)
    ap.add_argument("--iy", type=int, default=0)
    ap.add_argument("--threads", type=int, default=32)
    ap.add_argument("-o", "--out")
    ap.add_argument("--collect", nargs="+")
    args = ap.parse_args()

    if args.collect:
        rows = []
        for p in sorted(args.collect):
            d = json.load(open(p))
            rows.append(d)
        by = {}
        for d in rows:
            by.setdefault(round(d["x2"], 6), {})[round(d["knot"], 6)] = d
        knots = sorted({round(d["knot"], 6) for d in rows})
        print(f"knot factors found: {knots}")
        for x2 in sorted(by):
            print(f"\n--- x2 = {x2}  (anchor 0.6)")
            hdr = f"{'qT bin':>14}" + "".join(f"{'f='+format(k,'.4g'):>16}" for k in knots)
            if len(knots) == 2:
                hdr += f"{'ratio':>10}{'h^2 ratio':>12}"
            print(hdr)
            b0 = by[x2][knots[0]]["bins"]
            for i, b in enumerate(b0):
                line = f"[{b[4]:5g},{b[5]:5g}]".rjust(14)
                vals = []
                for k in knots:
                    d = by[x2].get(k)
                    v = d["dev"][i] if d else float("nan")
                    vals.append(v)
                    line += f"{v:>+16.3e}"
                if len(knots) == 2 and vals[1] != 0:
                    line += f"{vals[0]/vals[1]:>10.2f}"
                    line += f"{(math.log(knots[0])/math.log(knots[1]))**2:>12.2f}"
                print(line)
            line = "max|dev|".rjust(14)
            mx = []
            for k in knots:
                d = by[x2].get(k)
                m = float(np.abs(np.asarray(d["dev"], float)).max()) if d else float("nan")
                mx.append(m)
                line += f"{m:>16.3e}"
            if len(knots) == 2 and mx[1]:
                line += f"{mx[0]/mx[1]:>10.2f}"
                line += f"{(math.log(knots[0])/math.log(knots[1]))**2:>12.2f}"
            print(line)
        print("\nInterpolation-limited => ratio ~ h^2 ratio. Floor => ratio ~ 1.")
        return

    if not (args.base and args.x2 and args.out):
        raise SystemExit("need --base, --x2 and -o (or --collect)")

    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    f = args.knot
    if not f > 1.0:
        raise SystemExit("--knot must exceed 1")
    bins = make_bins(args.qt_lo, args.iy)
    tmp = os.path.join(os.path.dirname(os.path.abspath(args.out)),
                       f"_x2_{args.x2}_k{f:.6f}.conf")
    _conf_with_x2(args.base, args.x2, tmp)

    # reference: the change in the RUNCARD, so the convolutions are refilled
    _, s_run = configure(tmp, threads=args.threads, diff_scales=False)
    run_var = _eval(s_run, bins, np.asarray(s_run.gradient_central(), float))

    # parameter route through the rule replay, with the muF pair at 1/f and f
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
    sing.build_pdf_variations(sets, mem, nf, p0, n_train_var=3, n_eig=0,
                              as_cen=0.0, as_step=0.0,
                              muf_lo=1.0 / f, muf_hi=f)
    nons.build_fo_pdf_variations(sets, mem, nf, bins,
                                 np.asarray(nons.gradient_central()),
                                 n_eig=0, as_cen=0.0, as_step=0.0,
                                 muf_lo=1.0 / f, muf_hi=f)

    def rule(q):
        return np.asarray(
            sing.sigma_binned_rule_batch(bins, q)["value"], float
        ).reshape(-1)

    par_cen = rule(p0)
    p = p0.copy()
    p[names.index("scale_x2")] = args.x2
    par_var = rule(p)

    dev = (par_var / par_cen) / (run_var / par_cen) - 1.0
    json.dump({"x2": args.x2, "knot": f, "h": math.log(f),
               "bins": bins.tolist(), "dev": dev.tolist(),
               "par_cen": par_cen.tolist(), "par_var": par_var.tolist(),
               "run_var": run_var.tolist()},
              open(args.out, "w"), indent=1)
    print(f"\nx2 = {args.x2}, knot f = {f:.6f} (h = ln f = {math.log(f):.4f})")
    for k, b in enumerate(bins):
        print(f"  qT [{b[4]:4g},{b[5]:4g}]  param/runcard - 1 = {dev[k]:+.3e}")
    print(f"  max|dev| = {np.abs(dev).max():.3e}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
