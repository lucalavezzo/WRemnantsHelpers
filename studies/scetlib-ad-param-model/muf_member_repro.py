#!/usr/bin/env python3
"""Minimal reproducer: the muF member as a bin RULE vs the same member LIVE.

`ab_muf_route.py` showed that ``set_muf_keep_nodes(-1)`` evaluated live gives a
Vary.muf-down response of 0.947 (inside the production template's range) while
the same member read back out of a built cache gives 0.707 -- a 26% deficit in
the resummed piece. This isolates that to the smallest thing that can show it:
ONE process, SIX bins, muF pair ONLY (no alphaS pair, no eigenvectors), rules
built and evaluated without ever going through a file.

  live central   : sigma_binned_batch(p0)                      -- the truth
  rule central   : sigma_binned_rule_pdf_batch(p0, c=[])       -- compression only
  rule muF down  : same at scale_kappa_F = 0.5, i.e. t = -1     -- the member
  live muF down  : set_muf_keep_nodes(-1) then sigma_binned_batch

Reading it:
  rule/live central ~ 1e-4          the compression is faithful (expected)
  rule muF == live muF              the build is fine -> look at serialization
  rule muF != live muF              build_pdf_variations is losing it, and this
                                    script is the upstream reproducer

Dropping the alphaS pair matters: it means member indexing (`last = nvar - 2`
stepping over the muF legs) cannot be the explanation if the deficit survives,
because with 2 members there is nothing to step over.

The live muF evaluation is LAST because set_muf_keep_nodes calls _ad_reset() and
would throw the rules away.

  $SING ./incontainer.sh python3 muf_member_repro.py --base <cache.conf>
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ab_scale_route import make_bins  # noqa: E402

DEFAULT_QT_LO = [0.0, 1.0, 2.0, 4.0, 8.0, 33.0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="the central runcard")
    ap.add_argument("--iy", type=int, default=0)
    ap.add_argument("--qt-lo", type=float, nargs="+", default=DEFAULT_QT_LO)
    ap.add_argument("--n-train", type=int, default=9)
    ap.add_argument("--n-train-var", type=int, default=3)
    ap.add_argument("--threads", type=int, default=64)
    ap.add_argument("--leg", type=float, default=0.5,
                    help="kappa_F to evaluate the rule at (0.5 = t -1, 2.0 = +1)")
    ap.add_argument("--with-as-pair", action="store_true",
                    help="also build the alphaS pair AHEAD of the muF legs, as a "
                         "real cache does. The muF pair alone reproduces the live "
                         "member exactly, so this is the switch that matters.")
    args = ap.parse_args()

    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    conf, sigma = configure(args.base, threads=args.threads, diff_scales=True)
    sing, _nons = sigma.sub_pieces()
    names = list(sigma.gradient_param_names())
    ik = names.index("scale_kappa_F")
    p0 = np.asarray(sigma.gradient_central(), float)
    bins = make_bins(args.qt_lo, args.iy)

    def live(piece, p):
        piece.sigma_binned_batch(bins, p)          # warm
        out = piece.sigma_binned_batch(bins, p)
        v = out[0] if isinstance(out, (tuple, list)) else out
        return np.asarray(v, float).reshape(-1)

    live_cen = live(sing, p0)

    info = sing.build_bin_rules(bins, p0, n_train=args.n_train, n_hvp=1,
                               seed=4242, n_jobs=args.threads)
    print(f"rules: {[d['nodes'] for d in info]} nodes/bin, "
          f"worst resid {max(d['resid'] for d in info):.1e}")

    pdf_set = conf["QCD"]["pdf_set"]
    nf = conf["QCD"].getint("nf", fallback=5)
    # muF pair: two members, no eigenvectors. The set/member entries are unused
    # for muF legs but one entry per member is still required.
    sets, members = [pdf_set, pdf_set], [0, 0]
    as_cen, as_step = 0.0, 0.0
    if args.with_as_pair:
        # LAST before the muF legs and in (down, up) order -- exactly the order
        # prepare_cache_for_card builds, since both builders index from the end.
        from prepare_cache_for_card import _scetlib_src, _upstream_prepare_cache

        up = _upstream_prepare_cache()
        as_cen = float(p0[names.index("alphas")])
        pair = up.find_alphas_pair(pdf_set, "auto", as_cen)
        if not pair:
            raise SystemExit(f"no alphaS pair found for {pdf_set}")
        down, up_set, as_step = pair
        for s in (down, up_set):
            up.ensure_beamfunc_grids(_scetlib_src(), s, [0], 0)
        sets = [down, up_set] + sets
        members = [0, 0] + members
        print(f"alphaS pair: {down} / {up_set}, central {as_cen:.4f} "
              f"+- {as_step:.4f}")
    sing.build_pdf_variations(sets, np.array(members, dtype=np.int32),
                              nf, p0, n_train_var=args.n_train_var, n_eig=0,
                              as_cen=as_cen, as_step=as_step,
                              muf_lo=0.5, muf_hi=2.0)

    c = np.zeros(0, dtype=np.float64)
    p = p0.copy()
    p[ik] = args.leg

    def expl(q):   # explicit quadratic over the stored member integrals
        return np.asarray(sing.sigma_binned_rule_pdf_batch(bins, q, c)["value"],
                          float).reshape(-1)

    def tape(q):   # members on the clad tape -- the route scetlib_tf.py takes
        return np.asarray(sing.sigma_binned_rule_batch(bins, q)["value"],
                          float).reshape(-1)

    rule_cen, rule_var = expl(p0), expl(p)
    tape_cen, tape_var = tape(p0), tape(p)

    # LAST: this resets the node cache and discards the rules.
    leg = -1 if args.leg < 1.0 else 1
    sing.set_muf_keep_nodes(leg)
    live_var = live(sing, p0)

    print(f"\nVary.muf leg {leg:+d} (kappa_F = {args.leg}), resummed piece")
    print("live = the truth; expl = sigma_binned_rule_pdf_batch; "
          "tape = sigma_binned_rule_batch (what scetlib_tf.py calls)\n")
    print(f"{'qT':>11}{'live var/cen':>14}{'expl var/cen':>14}"
          f"{'tape var/cen':>14}{'expl/live':>11}{'tape/live':>11}")
    for k, b in enumerate(bins):
        lr = live_var[k] / live_cen[k]
        er = rule_var[k] / rule_cen[k]
        tr = tape_var[k] / tape_cen[k]
        print(f"  [{b[4]:4g},{b[5]:4g}]{lr:>14.6f}{er:>14.6f}{tr:>14.6f}"
              f"{er / lr:>11.4f}{tr / lr:>11.4f}")
    print(f"\ncentral, expl/live - 1: {abs(rule_cen / live_cen - 1).max():.2e}"
          f"   tape/live - 1: {abs(tape_cen / live_cen - 1).max():.2e}")


if __name__ == "__main__":
    main()
