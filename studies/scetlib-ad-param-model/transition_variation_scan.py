#!/usr/bin/env python3
"""Does the transition residual behave like an interpolation error? Scan x2.

NOTE ON THE NAME: this scans the SIZE of the variation, NOT the number of knots.
It cannot test a multi-knot configuration -- build_pdf_variations hard-refuses
any muf_lo/muf_hi but 0.5/2.0 (Vary.muf is a fixed factor of two in
Scale_provider) and the code carries exactly ONE pair. Adding knots needs
upstream changes to both. The evidence here is INDIRECT: if the residual does not
grow with the variation size, it is not interpolation order, so more knots would
not help.

The transition points reach the beam convolutions through the muF member pair:
bfc6be6 feeds the induced per-node muF shift into the same quadratic that carries
kappa_F, and that quadratic is built from three samples -- kappa_F = 0.5, 1, 2 --
so it is exact AT THOSE KNOTS and approximate in between. A transition variation
induces a muF shift that lands wherever it lands, generally between knots.

If that is the residual (we measure 1.1-3.4e-03 against the production templates,
and Josh quotes +7.8e-04 against an independent runcard route), then adding knots
would reduce it and the case for making the knot count tunable is made. If it is
not, more knots buy nothing and the effort belongs elsewhere.

The runcard route settles it. Changing x2 in the RUNCARD refills the convolutions
at the shifted muF exactly -- no interpolation anywhere -- while changing the
PARAMETER interpolates. So

    param(x2) / runcard(x2) - 1

IS the interpolation error, isolated, with the physics identical on both sides.
Scan x2 and the shape of that error decides it:

  * zero at the anchor (x2 = 0.6), which is already known;
  * GROWING with |t|, the induced shift in member units t = ln(muF/muF0)/ln 2,
    and for a quadratic interpolant growing faster than linearly in |t|;
  * DIPPING back toward zero as |t| -> 1, where the next knot sits.

A residual that is flat in t, or that does not dip near a knot, is not
interpolation order and this whole proposal is wrong.

One x2 per process: each needs its own configure() for the runcard side, and a
third configure() in one process segfaults (SCETlib global state).

  ./knot_scan.py --base <cache.conf> --x2 0.45 -o scan_045.json
  ./knot_scan.py --collect scan_*.json
"""
import argparse
import configparser
import glob
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ab_scale_route import _eval, make_bins  # noqa: E402

# Above the transition region there is nothing to see -- g_run = 1 and x2 does
# nothing -- so sample where the matching actually lives.
DEFAULT_QT_LO = [20.0, 28.0, 33.0, 44.0]


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
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base")
    ap.add_argument("--x2", type=float)
    ap.add_argument("--qt-lo", type=float, nargs="+", default=DEFAULT_QT_LO)
    ap.add_argument("--iy", type=int, default=0)
    ap.add_argument("--threads", type=int, default=64)
    ap.add_argument("-o", "--out")
    ap.add_argument("--collect", nargs="+",
                    help="tabulate JSONs written by earlier runs and report "
                         "whether the error grows with the induced shift")
    args = ap.parse_args()

    if args.collect:
        rows = []
        for p in sorted(args.collect):
            d = json.load(open(p))
            rows.append((d["x2"], np.asarray(d["dev"], float),
                         np.asarray(d["t_hat"], float)))
        print(f"{'x2':>7}{'|t| (member units)':>20}{'max|param/runcard-1|':>24}"
              f"{'mean':>12}")
        for x2, dev, t in sorted(rows):
            print(f"{x2:>7.2f}{np.abs(t).max():>20.4f}"
                  f"{np.abs(dev).max():>24.3e}{np.abs(dev).mean():>12.3e}")
        print("\nInterpolation order predicts: zero at x2 = 0.6, growing "
              "super-linearly in |t|, dipping as |t| -> 1.")
        return

    if not (args.base and args.x2 and args.out):
        raise SystemExit("need --base, --x2 and -o (or --collect)")

    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    bins = make_bins(args.qt_lo, args.iy)
    tmp = os.path.join(os.path.dirname(os.path.abspath(args.out)),
                       f"_x2_{args.x2}.conf")
    _conf_with_x2(args.base, args.x2, tmp)

    # runcard route: autodiff OFF, the change written into the card, so the
    # convolutions are rebuilt at the shifted muF. The reference.
    _, s_run = configure(tmp, threads=args.threads, diff_scales=False)
    run_var = _eval(s_run, bins, np.asarray(s_run.gradient_central(), float))

    # parameter route: autodiff ON, x2 moved as a live parameter -- but the
    # muF MEMBERS must exist first. bfc6be6 carries the transition-induced muF
    # shift through the member interpolation, and ad_g.var_muf is only set once
    # build_pdf_variations has run, so a live evaluation with no members skips
    # that block entirely and still has the ORIGINAL sign-flipped derivative.
    # Measured that way the "error" is ~2e-01, i.e. the pre-fix bug, not an
    # interpolation residual. So build the rules and both member sets, and
    # evaluate through the rule replay -- which is also what the fit does.
    _, s_par = configure(args.base, threads=args.threads, diff_scales=True)
    sing, nons = s_par.sub_pieces()
    names = list(s_par.gradient_param_names())
    p0 = np.asarray(s_par.gradient_central(), float)
    cols = [names.index(n) for n in nons.gradient_param_names()]
    conf_par = configparser.ConfigParser(inline_comment_prefixes="#")
    conf_par.read(args.base)
    pdf_set = conf_par["QCD"]["pdf_set"]
    nf = conf_par["QCD"].getint("nf", fallback=5)

    s_par.prepare(bins, p0)
    sing.build_bin_rules(bins, p0, n_train=9, n_hvp=1, seed=4242,
                         n_jobs=args.threads)
    sets = [pdf_set, pdf_set]
    mem = np.array([0, 0], dtype=np.int32)
    sing.build_pdf_variations(sets, mem, nf, p0, n_train_var=3, n_eig=0,
                              as_cen=0.0, as_step=0.0, muf_lo=0.5, muf_hi=2.0)
    nons.build_fo_pdf_variations(sets, mem, nf, bins,
                                 np.asarray(nons.gradient_central()),
                                 n_eig=0, as_cen=0.0, as_step=0.0,
                                 muf_lo=0.5, muf_hi=2.0)

    def rule(q):
        v = np.asarray(sing.sigma_binned_rule_batch(bins, q)["value"],
                       float).reshape(-1)
        return v      # already the matched total -- see scetlib-cms MR !7

    par_cen = rule(p0)
    p = p0.copy()
    p[names.index("scale_x2")] = args.x2
    par_var = rule(p)

    # The runcard route has no central of its own at this x2; normalise both to
    # the ANCHOR so the two sides are the same ratio. The anchor central is the
    # parameter route's, which equals the runcard's at x2 = 0.6 to 4e-16.
    dev = (par_var / par_cen) / (run_var / par_cen) - 1.0
    # Induced shift in member units. x2 scales muB, and muf tracks muB when
    # Lf ~ 0, so ln(x2/x2_0)/ln 2 is the leading estimate -- enough to order the
    # scan, not a substitute for the kernel's own per-node ln_muf_shift.
    t_hat = np.full(len(bins), math.log(args.x2 / 0.6) / math.log(2.0))

    json.dump({"x2": args.x2, "bins": bins.tolist(), "dev": dev.tolist(),
               "t_hat": t_hat.tolist()}, open(args.out, "w"), indent=1)
    print(f"\nx2 = {args.x2}  (|t| ~ {abs(t_hat[0]):.4f} member units)")
    for k, b in enumerate(bins):
        print(f"  qT [{b[4]:4g},{b[5]:4g}]  param/runcard - 1 = {dev[k]:+.3e}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
