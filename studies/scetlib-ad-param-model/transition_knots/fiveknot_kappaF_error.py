#!/usr/bin/env python3
"""kappa_F BETWEEN the muF knots, 3 vs 5 knots, against an EXACT reference.

Every muF validation this project has (the CorrZ `mufup`/`mufdown` templates,
validate_variations) sits AT kappa_F = 0.5 or 2, which are knots -- where the
interpolant returns the stored member bit for bit and can say nothing. This
measures the one thing they cannot: how wrong the interpolant is BETWEEN knots,
and whether the extra pair of members fixes it.

THE REFERENCE. A runcard with `kappaf = K` AND `muf_min = muf_min0 / K`. That
pair reproduces the live `scale_kappa_F = K` formula term for term -- Vary.muf
scales muF by the factor and divides the floor by it, so the effective large-bT
cutoff (muF/Q) muf_min is held -- and the 2026-08-25 logbook entry validated it
at K = 2 to 9e-16 .. 5e-6. So this is a refill, not another interpolation, and
the deviation IS the interpolation error.

WHY IT IS THE DIAGNOSTIC FOR THE FIVE-KNOT PROTOTYPE.
  * K = 2 and K = 0.5 are knots of BOTH stencils, so both arms must be exact
    there. Anything else means the outer members moved, which they must not.
  * K = sqrt(2) is a knot of the FIVE-knot stencil only. The five-knot arm must
    be exact there and the three-knot arm must not. That is a sharp,
    sign-definite test that the inner members are built where the kernel thinks
    they are -- which no transition-point measurement can isolate, because
    there the coordinate is a per-node shift rather than a number you choose.
  * K = 2^0.3 / 2^0.7 sit between knots in both, and measure the actual gain.

One K per process: the runcard side needs its own configure(), and a third
configure() in one process segfaults (SCETlib global state).
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
DEFAULT_QT_LO = [8.0, 18.0, 20.0, 24.0, 28.0, 33.0]


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


def _conf_kappaF(base, K, out):
    c = configparser.ConfigParser(inline_comment_prefixes="#")
    c.read(base)
    s = c["Calculation_settings"]
    s["kappaf"] = repr(float(K))
    # The floor must follow, or the reference is a DIFFERENT physical change
    # from the one the member staging makes.
    s["muf_min"] = repr(float(s.get("muf_min", "1.0")) / float(K))
    with open(out, "w") as f:
        c.write(f)
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--base", required=True)
    ap.add_argument("--kappaF", type=float, required=True)
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("--nmuf", type=int, default=4, choices=(2, 4, -4))
    ap.add_argument("--qt-lo", type=float, nargs="+", default=DEFAULT_QT_LO)
    ap.add_argument("--iy", type=int, default=0)
    ap.add_argument("--n-train", type=int, default=9)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    import scetlib_qT
    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    f, K = args.knot, args.kappaF
    bins = make_bins(args.qt_lo, args.iy)
    tmp = os.path.join(os.path.dirname(os.path.abspath(args.out)),
                       f"_kF_{K:.6f}.conf")
    _conf_kappaF(args.base, K, tmp)

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
    nm = args.nmuf
    sets = [pdf_set] * abs(nm)
    mem = np.zeros(abs(nm), dtype=np.int32)
    sing.build_pdf_variations(sets, mem, nf, p0, n_train_var=3, n_eig=0,
                              as_cen=0.0, as_step=0.0,
                              muf_lo=1.0 / f, muf_hi=f, muf_nmem=nm)
    nons.build_fo_pdf_variations(sets, mem, nf, bins,
                                 np.asarray(nons.gradient_central()),
                                 n_eig=0, as_cen=0.0, as_step=0.0,
                                 muf_lo=1.0 / f, muf_hi=f, muf_nmem=nm)

    def rule(q):
        return np.asarray(
            sing.sigma_binned_rule_batch(bins, q)["value"], float
        ).reshape(-1)

    p = p0.copy()
    p[names.index("scale_kappa_F")] = K
    arms = {}
    for used in ((2, 4) if abs(nm) == 4 else (2,)):
        scetlib_qT.DrellYan.set_muf_knots_used(used)
        cen = rule(p0)
        var = rule(p)
        arms[used] = dict(par_cen=cen.tolist(), par_var=var.tolist(),
                          dev=(var / run_var - 1.0).tolist())
    scetlib_qT.DrellYan.set_muf_knots_used(0)
    cen = np.asarray(arms[2]["par_cen"], float)
    true_resp = run_var / cen - 1.0

    json.dump(dict(kappaF=K, knot=f, nmuf=nm, iy=args.iy, n_train=args.n_train,
                   bins=bins.tolist(), run_var=run_var.tolist(),
                   true_resp=true_resp.tolist(),
                   arms={str(k): v for k, v in arms.items()}),
              open(args.out, "w"), indent=1)

    print(f"\nkappa_F = {K:.6g} (= f^{math.log(K)/math.log(f):+.3f}), "
          f"outer knot f = {f:g}, built with {nm} muF members")
    hdr = f"{'qT bin':>14}{'true resp':>13}"
    for used in sorted(arms):
        hdr += f"{'dev ' + str(used + 1) + '-knot':>16}"
    print(hdr + "   (dev = model/runcard - 1, i.e. a fraction of sigma)")
    for k, b in enumerate(bins):
        line = f"[{b[4]:5g},{b[5]:5g}]".rjust(14) + f"{true_resp[k]:>+13.3e}"
        for used in sorted(arms):
            line += f"{arms[used]['dev'][k]:>+16.3e}"
        print(line)
    line = "max|dev|".rjust(14) + " " * 13
    for used in sorted(arms):
        line += f"{np.abs(np.asarray(arms[used]['dev'])).max():>16.3e}"
    print(line)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
