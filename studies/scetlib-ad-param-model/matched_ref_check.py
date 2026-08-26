#!/usr/bin/env python3
"""Compare the model's two evaluation paths against the MATCHED direct calculation.

Why this exists, and why the earlier check was not good enough. `ab_muf_route.py`
and `muf_member_repro.py` both compare against `sing.sigma_binned_batch`. That is
the RESUMMED piece alone, while the rule path returns the MATCHED cross section
(`doc/matched-production-revalidation` section 6). The two differ by the
nonsingular contribution -- ~3% at low qT, 15.7% in the [44,100] bin -- so those
scripts cannot validate anything at high qT, which is exactly where the model
looked worst. This one builds the reference the model is actually supposed to
reproduce:

  direct  = sigma.sigma_binned_batch(bins, p)          the matched wrapper
  tape    = sing.sigma_binned_rule_batch + nons.fo_binned_pdf_batch
  expl    = sing.sigma_binned_rule_pdf_batch + nons.fo_binned_pdf_batch

`tape` is exactly what `scetlib_tf.py:values_and_jacobian` computes, so it is the
model as the fit sees it. `expl` swaps only the resummed half onto the other
entry point.

Everything happens in ONE process on a handful of bins, so it costs minutes
rather than the hours a 210-bin cache needs -- and it answers the question a full
cache cannot answer any better: do the two paths differ once the integration
tolerance is tighter than the level being validated?

The muF variation is applied to the direct reference with
`set_muf_keep_nodes(leg)` on BOTH sub-pieces, and to the model by moving
`scale_kappa_F`. That comparison is apples to apples: same quantity, same bins,
same tolerance.

Ratios are always taken against each route's OWN central, so a constant offset
between routes cannot masquerade as a response error -- which is the mistake this
script exists to avoid.

  $SING ./incontainer.sh python3 matched_ref_check.py --base <cache.conf>
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ab_scale_route import QT_EDGES, Y_EDGES  # noqa: E402

# Spans the whole range on purpose: the first bin (where the nonsingular cutoff
# and the template noise live), the resummation region, the transition, and the
# [44,100] gen-overflow bin where the fixed-order piece dominates and every
# earlier check was blind.
DEFAULT_QT_LO = [0.0, 2.0, 8.0, 20.0, 33.0, 44.0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--iy", type=int, nargs="+", default=[0, 5],
                    help="indices into Y_EDGES; more than one checks that the "
                         "answer is not special to central rapidity")
    ap.add_argument("--qt-lo", type=float, nargs="+", default=DEFAULT_QT_LO)
    ap.add_argument("--leg", type=float, default=0.5)
    ap.add_argument("--n-train", type=int, default=9)
    ap.add_argument("--threads", type=int, default=200)
    ap.add_argument("--corr", help="CorrZ file; adds the production template as a "
                                   "fourth column on the same bins")
    ap.add_argument("--label", default="mufdown",
                    help="template label matching --leg")
    args = ap.parse_args()

    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    conf, sigma = configure(args.base, threads=args.threads, diff_scales=True)
    sing, nons = sigma.sub_pieces()
    names = list(sigma.gradient_param_names())
    ik = names.index("scale_kappa_F")
    p0 = np.asarray(sigma.gradient_central(), float)
    cols = [names.index(n) for n in nons.gradient_param_names()]

    bins = np.asarray(
        [[60.0, 120.0, Y_EDGES[iy], Y_EDGES[iy + 1],
          lo, QT_EDGES[QT_EDGES.index(lo) + 1]]
         for iy in args.iy for lo in args.qt_lo], float)
    print(f"{len(bins)} bins, tolerance from {os.path.basename(args.base)}: "
          f"{conf['Integration']['target_precision_rel']}", flush=True)

    def direct(p):
        v = sigma.sigma_binned_batch(bins, p)
        return np.asarray(v[0] if isinstance(v, (tuple, list)) else v,
                          float).reshape(-1)

    # step one, then the rules and BOTH variation builds -- the fixed-order muF
    # members are what the earlier reproducer never built, so its fixed-order
    # half could not respond to kappa_F at all.
    m0 = np.asarray(sigma.prepare(bins, p0), float)
    sing.build_bin_rules(bins, p0, n_train=args.n_train, n_hvp=1, seed=4242,
                         n_jobs=args.threads)
    pdf_set = conf["QCD"]["pdf_set"]
    nf = conf["QCD"].getint("nf", fallback=5)
    sets = [pdf_set, pdf_set]
    mem = np.array([0, 0], dtype=np.int32)
    sing.build_pdf_variations(sets, mem, nf, p0, n_train_var=3, n_eig=0,
                              as_cen=0.0, as_step=0.0, muf_lo=0.5, muf_hi=2.0)
    nons.build_fo_pdf_variations(sets, mem, nf, bins,
                                 np.asarray(nons.gradient_central()),
                                 n_eig=0, as_cen=0.0, as_step=0.0,
                                 muf_lo=0.5, muf_hi=2.0)

    def model(p, route):
        f = (sing.sigma_binned_rule_batch(bins, p) if route == "tape"
             else sing.sigma_binned_rule_pdf_batch(bins, p, np.zeros(0)))
        v = np.asarray(f["value"], float).reshape(-1)
        rn = nons.fo_binned_pdf_batch(bins, p[cols])
        return v + np.asarray(rn["value"], float).reshape(-1)

    tape_c, expl_c = model(p0, "tape"), model(p0, "expl")
    p = p0.copy()
    p[ik] = args.leg
    tape_v, expl_v = model(p, "tape"), model(p, "expl")

    # the reference, LAST: set_muf_keep_nodes resets the caches
    leg = -1 if args.leg < 1.0 else 1
    for t in (sing, nons):
        t.set_muf_keep_nodes(leg)
    dir_v = direct(p0)

    print("\ncentral, model vs the matched direct calculation")
    print(f"{'qT':>12}{'|Y|':>12}{'tape/direct-1':>16}{'expl/direct-1':>16}")
    for k, b in enumerate(bins):
        print(f"  [{b[4]:4g},{b[5]:4g}]  [{b[2]:.2f},{b[3]:.2f}]"
              f"{tape_c[k] / m0[k] - 1:>16.2e}{expl_c[k] / m0[k] - 1:>16.2e}")

    # The frozen production template, on the SAME bins. It is the deliverable's
    # reference, but it cannot tell a model error from a stale template, which is
    # why the direct calculation is here too -- above qT ~ 1 the two should agree
    # and any disagreement is ours.
    tmpl = None
    if args.corr:
        import types

        cargs = types.SimpleNamespace(corr=args.corr, label=args.label)
        from ab_scale_route import run_corr

        c_cen, c_var = run_corr(cargs, bins)
        tmpl = c_var / c_cen

    print(f"\nVary.muf leg {leg:+d}: response, ratio to each route's own central")
    hdr = (f"{'qT':>12}{'|Y|':>12}{'direct':>11}{'tape':>11}{'expl':>11}"
           f"{'tape/dir':>10}{'expl/dir':>10}")
    if tmpl is not None:
        hdr += f"{'CorrZ':>11}{'dir/CorrZ':>11}"
    print(hdr)
    for k, b in enumerate(bins):
        rd = dir_v[k] / m0[k]
        rt = tape_v[k] / tape_c[k]
        re = expl_v[k] / expl_c[k]
        line = (f"  [{b[4]:4g},{b[5]:4g}]  [{b[2]:.2f},{b[3]:.2f}]"
                f"{rd:>11.6f}{rt:>11.6f}{re:>11.6f}{rt / rd:>10.4f}"
                f"{re / rd:>10.4f}")
        if tmpl is not None:
            line += f"{tmpl[k]:>11.6f}{rd / tmpl[k]:>11.4f}"
        print(line)


if __name__ == "__main__":
    main()
