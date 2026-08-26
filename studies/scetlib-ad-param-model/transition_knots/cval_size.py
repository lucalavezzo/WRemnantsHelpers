#!/usr/bin/env python3
"""How big is the rule's bin-level constant c_val, and how much response can it
possibly be hiding?

node_cval interpolates the per-member constants on the GLOBAL kappa_F label,
    tf = log(kappa_F) / var_muf_lnstep,
with NO transition-induced shift -- so d(c_val)/d(x1,x2,x3) is identically zero.
c_val has no node, so it is the one place the "a global coordinate cannot follow
a per-node shift" mechanism genuinely survives.

Sizing it needs two numbers per bin:
  * c_val / sigma_bin   -- the share of the bin the dead constant carries;
  * max_leg |c_leg - c_0| / sigma_bin -- how far that constant moves over a FULL
    member step (kappa_F = 1 -> f). The transition-induced per-node coordinate
    is a fraction of a step, so this is a GENEROUS upper bound on the response
    that node_cval is failing to produce.

Compare the bound against the measured shortfall (~28% of a -0.31% response at
qT [20,24], i.e. ~9e-4 of sigma). If the bound is far below it, node_cval is
closed as a candidate; if it is comparable, it is the remaining hole.
"""
import argparse
import configparser
import json
import os
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)

QT_EDGES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28,
            33, 44, 100]
Y_EDGES = [0, 0.15, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.5]


def make_bins(qt_lo, iy):
    out = []
    for lo in qt_lo:
        k = QT_EDGES.index(lo)
        out.append([60.0, 120.0, Y_EDGES[iy], Y_EDGES[iy + 1],
                    QT_EDGES[k], QT_EDGES[k + 1]])
    return np.asarray(out, float)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("--iy", type=int, default=0)
    ap.add_argument("--qt-lo", type=float, nargs="+",
                    default=[16.0, 18.0, 20.0, 24.0, 28.0, 33.0, 44.0])
    ap.add_argument("--threads", type=int, default=32)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    bins = make_bins(args.qt_lo, args.iy)
    _, s_par = configure(args.base, threads=args.threads, diff_scales=True)
    sing, nons = s_par.sub_pieces()
    p0 = np.asarray(s_par.gradient_central(), float)
    cp = configparser.ConfigParser(inline_comment_prefixes="#")
    cp.read(args.base)
    pdf_set = cp["QCD"]["pdf_set"]
    nf = cp["QCD"].getint("nf", fallback=5)

    s_par.prepare(bins, p0)
    sing.build_bin_rules(bins, p0, n_train=9, n_hvp=1, seed=4242,
                         n_jobs=args.threads)
    f = args.knot
    sing.build_pdf_variations([pdf_set, pdf_set],
                              np.array([0, 0], dtype=np.int32), nf, p0,
                              n_train_var=3, n_eig=0, as_cen=0.0, as_step=0.0,
                              muf_lo=1.0 / f, muf_hi=f)
    nons.build_fo_pdf_variations([pdf_set, pdf_set],
                                 np.array([0, 0], dtype=np.int32), nf, bins,
                                 np.asarray(nons.gradient_central()),
                                 n_eig=0, as_cen=0.0, as_step=0.0,
                                 muf_lo=1.0 / f, muf_hi=f)

    sig = np.asarray(sing.sigma_binned_rule_batch(bins, p0)["value"],
                     float).reshape(-1)
    rep = sing.rule_cvals()

    print(f"\nknot f = {f:g}, |Y| bin {args.iy}")
    print(f"{'qT bin':>12}{'sigma_bin':>13}{'c_val':>13}{'c/sigma':>11}"
          f"{'sites':>7}{'max|dc|/sigma (full step)':>27}")
    rows = []
    for k, b in enumerate(bins):
        # rules are stored in the order they were built
        d = rep[k]
        assert abs(d["key"][4] - b[4]) < 1e-9, (d["key"], b)
        c0 = d["c_val"]
        vc = np.asarray(d["var_c_val"], float)
        ismuf = np.asarray(d["var_is_muf"], int)
        dmax = float(np.abs(vc[ismuf != 0] - c0).max()) if (ismuf != 0).any() else 0.0
        rows.append(dict(qt_lo=b[4], qt_hi=b[5], sigma=sig[k], c_val=c0,
                         var_c_val=vc.tolist(), is_muf=ismuf.tolist(),
                         dmax=dmax))
        print(f"[{b[4]:4g},{b[5]:4g}]".rjust(12)
              + f"{sig[k]:>13.5e}{c0:>13.5e}{c0/sig[k]:>11.3e}"
              + f"{d['n_sites']:>7d}{dmax/abs(sig[k]):>27.3e}")
    json.dump(rows, open(args.out, "w"), indent=1)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
