#!/usr/bin/env python3
"""The muF interpolation error with and without the ANALYTIC DGLAP evolution of
the beam convolutions, in ONE process, against an EXACT runcard refill.

This is knot_interp_error.py with the experiment turned into a controlled A/B.
That script could only compare two SPACINGS, and only across two processes --
so the two arms differed by their whole rule build. Here the rules, the node
set, the outer member convolutions and the re-solved weights are built ONCE
with the five-knot stencil (kappa_F = 1/f, 1/sqrt f, 1, sqrt f, f) and then
evaluated twice:

    knots_used = 2   the three-knot quadratic (1/f, 1, f) -- the SHIPPED model
    knots_used = 4   the five-knot quartic                -- the proposal

`DrellYan.set_muf_knots_used` holds the kernel's knot count down without
touching anything else, so the difference between the two numbers is the
interpolation ORDER and nothing else. The reference is bit-identical for both
by construction: it is one runcard refill, computed once.

WHAT IS MEASURED

    dev = [param(x2)/param(0.6)] / [runcard(x2)/param(0.6)] - 1

The runcard route writes x2 into the card, so the beam convolutions are
REFILLED at the shifted muF -- exact, no interpolation. The parameter route
moves x2 live and lets the member interpolation carry the induced per-node muF
shift. The physics is identical on both sides, so dev IS the interpolation
error with nothing else in it: no templates, no nonsingular mismatch, no cache.

REGIMES -- always say which one a number belongs to.
  FINITE variation      x2 = 0.35 / 0.75. What the production templates carry
                        and what the CorrZ closure plot shows.
  NEAR-ANCHOR derivative  x2 = 0.55, ~12x smaller. What a FIT uses.
The two do not scale the same way with the knot geometry; quoting one for the
other produced a wrong conclusion earlier in this study.

DO NOT DIAGNOSE on qT [18,20] or any bin whose true response is below ~1e-4 of
sigma -- that is the node-ladder target and the reference is no better than the
number being measured. The script prints the true response next to every dev so
that this is checkable rather than remembered.
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
DEFAULT_QT_LO = [18.0, 20.0, 24.0, 28.0, 33.0]


def make_bins(qt_lo, iy):
    out = []
    for lo in qt_lo:
        k = QT_EDGES.index(lo)
        out.append([60.0, 120.0, Y_EDGES[iy], Y_EDGES[iy + 1],
                    QT_EDGES[k], QT_EDGES[k + 1]])
    return np.asarray(out, float)


def _eval(sigma, bins, p):
    sigma.sigma_binned_batch(bins, p)          # warms the node cache
    out = sigma.sigma_binned_batch(bins, p)
    v = out[0] if isinstance(out, (tuple, list)) else out
    return np.asarray(v, float).reshape(-1)


def _conf_with(base, out, x2=None, x1=None, x3=None):
    c = configparser.ConfigParser(inline_comment_prefixes="#")
    c.read(base)
    tp = c["Calculation_settings"]["transition_points"]
    lo, mid, hi = (v.strip() for v in tp.strip("[] ").split(","))
    lo = lo if x1 is None else f"{x1}"
    mid = mid if x2 is None else f"{x2}"
    hi = hi if x3 is None else f"{x3}"
    c["Calculation_settings"]["transition_points"] = f"[{lo}, {mid}, {hi}]"
    with open(out, "w") as f:
        c.write(f)
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--base", required=True)
    ap.add_argument("--x2", type=float, default=None)
    ap.add_argument("--x1", type=float, default=None)
    ap.add_argument("--x3", type=float, default=None)
    ap.add_argument("--knot", type=float, default=2.0,
                    help="OUTER muF knot factor f; the inner knots sit at "
                         "kappa_F = f^+-1/2")
    ap.add_argument("--nmuf", type=int, default=2, choices=(2, 4, -4),
                    help="how many muF members to BUILD (2 = the shipped "
                         "three-knot stencil).")
    ap.add_argument("--modes", type=int, nargs="+", default=[0, 1, 3],
                    help="analytic-muF modes to evaluate. 0 = the shipped "
                         "member interpolation alone, 1 = + the P0/P1/P0xP0 "
                         "evolution terms the fo_lvl=2 conv prefix already "
                         "holds, 3 = + P2, P0xP1, P1xP0, P0xP0xP0 (needs the "
                         "nodes to be built with mode 3).")
    ap.add_argument("--qt-lo", type=float, nargs="+", default=DEFAULT_QT_LO)
    ap.add_argument("--iy", type=int, default=0)
    ap.add_argument("--n-train", type=int, default=9)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    import scetlib_qT
    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    # Mode 3 fills four conv kinds one fixed order above nnlo, and which kernels
    # the conv provider LOADS is decided when the calculation is configured, so
    # the mode has to be set first. Every arm then reads the SAME nodes: modes 0
    # and 1 simply do not look at the extra kinds. That is what makes this an
    # A/B/C rather than three separate calculations.
    if max(args.modes) >= 3:
        scetlib_qT.DrellYan.set_muf_analytic(3)

    f = args.knot
    if not f > 1.0:
        raise SystemExit("--knot must exceed 1")
    if args.x2 is None and args.x1 is None and args.x3 is None:
        raise SystemExit("give at least one of --x1 --x2 --x3")
    bins = make_bins(args.qt_lo, args.iy)
    tag = f"x1_{args.x1}_x2_{args.x2}_x3_{args.x3}_k{f:.6f}"
    tmp = os.path.join(os.path.dirname(os.path.abspath(args.out)),
                       f"_{tag}.conf")
    _conf_with(args.base, tmp, x2=args.x2, x1=args.x1, x3=args.x3)

    # THE REFERENCE: the transition points written into the runcard, so the beam
    # convolutions are refilled at the shifted muF. Computed once and shared by
    # both arms -- that is what makes this a controlled A/B.
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
    sing.build_bin_rules(bins, p0, n_train=args.n_train, n_hvp=1, seed=4242,
                         n_jobs=args.threads)
    nm = 2
    sets = [pdf_set] * nm
    mem = np.zeros(nm, dtype=np.int32)
    # NB no muf_nmem here: that argument exists only on the five-knot branch.
    # This build is off eb60a04, where the muF stencil is always the two outer
    # members -- which is exactly what the analytic route is compared against.
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

    p = p0.copy()
    for nmv, v in (("scale_x1", args.x1), ("scale_x2", args.x2),
                   ("scale_x3", args.x3)):
        if v is not None:
            p[names.index(nmv)] = v

    arms = {}
    for mode in args.modes:
        scetlib_qT.DrellYan.set_muf_analytic(mode)
        cen = rule(p0)
        var = rule(p)
        arms[mode] = dict(par_cen=cen.tolist(), par_var=var.tolist(),
                          dev=((var / cen) / (run_var / cen) - 1.0).tolist())
    scetlib_qT.DrellYan.set_muf_analytic(0)

    # THE ARMS MUST SEPARATE. A perfect null between two arms of an A/B is the
    # signature of a shared cached result, not of a change that does nothing;
    # this study has already been burnt by exactly that. The central value must
    # be IDENTICAL between modes (the correction vanishes at D = 0) and the
    # VARIED one must differ, so both halves are checked.
    ref = arms[args.modes[0]]
    for mode in args.modes[1:]:
        dc = max(abs(a / b - 1.0) for a, b in zip(arms[mode]["par_cen"],
                                                  ref["par_cen"]))
        dv = max(abs(a / b - 1.0) for a, b in zip(arms[mode]["par_var"],
                                                  ref["par_var"]))
        print(f"  ARM SEPARATION mode {args.modes[0]} vs {mode}: "
              f"max|d central| = {dc:.3e}  max|d varied| = {dv:.3e}")
        if dv < 1e-12:
            raise SystemExit(
                f"arms {args.modes[0]} and {mode} did not separate on the "
                "VARIED point -- refusing to report a null")

    # The TRUE response, from the reference alone. Printed so that the
    # "do not diagnose below 1e-4 of sigma" rule can be applied by the reader
    # instead of taken on trust.
    true_resp = (run_var / np.asarray(arms[args.modes[0]]["par_cen"])) - 1.0

    out = dict(x1=args.x1, x2=args.x2, x3=args.x3, knot=f, h=math.log(f),
               nmuf=nm, n_train=args.n_train, iy=args.iy, modes=args.modes,
               bins=bins.tolist(), run_var=run_var.tolist(),
               true_resp=true_resp.tolist(),
               arms={str(k): v for k, v in arms.items()})
    json.dump(out, open(args.out, "w"), indent=1)

    print(f"\nx1={args.x1} x2={args.x2} x3={args.x3}, outer knot f = {f:.6f} "
          f"(h = ln f = {math.log(f):.4f}), built with {nm} muF members")
    hdr = f"{'qT bin':>14}{'true resp':>13}"
    for used in sorted(arms):
        hdr += f"{'dev mode ' + str(used):>16}"
        hdr += f"{'% of resp':>11}"
    print(hdr)
    for k, b in enumerate(bins):
        line = f"[{b[4]:5g},{b[5]:5g}]".rjust(14) + f"{true_resp[k]:>+13.3e}"
        for used in sorted(arms):
            d = arms[used]["dev"][k]
            line += f"{d:>+16.3e}"
            line += f"{100.0 * d / true_resp[k]:>+10.1f}%" if true_resp[k] else \
                    f"{'--':>11}"
        print(line)
    line = "max|dev|".rjust(14) + " " * 13
    for used in sorted(arms):
        line += f"{np.abs(np.asarray(arms[used]['dev'])).max():>16.3e}{'':>11}"
    print(line)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
