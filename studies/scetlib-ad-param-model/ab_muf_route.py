#!/usr/bin/env python3
"""A/B the muF direction: does ``set_muf_keep_nodes`` reproduce a fresh configure?

Companion to ``ab_scale_route.py``, which does the same job for ``kappa_R`` and
the transition points. muF needs its own script because it does NOT go through
the live AD kernel at all -- ``scale_kappa_F`` is an inert slot there. The whole
muF response comes from the two members ``build_pdf_variations`` builds with
``set_muf_keep_nodes(-1/+1)``, and the cache then interpolates in
``t = ln(kappa_F)/ln(2)``, which is exact at ``t = 0, +-1``. So at
``scale_kappa_F = 2`` the model returns that member and nothing else, and if the
member is wrong the model is wrong by exactly the same amount.

Two routes, ratio always taken against each route's OWN central:

  ``--mode fresh``      ``Vary.muf`` set on the Scale_provider BEFORE the first
                        evaluation, so the bT quadrature and the beam
                        convolutions adapt to the varied muF. This is what the
                        production driver does, hence the reference.
  ``--mode keepnodes``  evaluate central first (populating the node and FO
                        caches), then ``set_muf_keep_nodes(leg)``, which keeps
                        the abscissas and refreshes the node data in place. This
                        is what the cache build does.

Why this is the suspect. ``Scale_provider.hpp`` gives ``Vary.muf`` two
properties nothing else has: it stays ON in the FO limit (every other variation
switches off at large qT/Q), and it is compensated at ``muT = 0`` so the
effective cutoff stays ``(muF/Q) * muf_min`` -- the production runcard sets
``muf_min = 1.40``, so that compensation is live. ``set_muf_keep_nodes`` itself
carries the comment "refreshing only conv is what made an earlier attempt 27.6%
wrong", and the cache currently misses the ``mufdown`` template by 26.6%. That
is close enough to be worth measuring rather than assuming.

Reading the result:
  fresh == keepnodes  -> the refresh is fine; the disagreement with the template
                         is then either the template label meaning something
                         else or the production job's own configuration.
  fresh != keepnodes  -> the in-place refresh is losing something, and by how
                         much tells you which piece (use --piece).

One ``configure()`` per process is the rule (a third segfaults, SCETlib global
state), so ``fresh`` uses its budget of two and ``keepnodes`` uses one.

  $SING ./incontainer.sh python3 ab_muf_route.py --mode fresh     --leg -1 -o f.json
  $SING ./incontainer.sh python3 ab_muf_route.py --mode keepnodes --leg -1 -o k.json
  python3 ab_scale_route.py --mode compare f.json k.json
"""
import argparse
import configparser
import json
import os
import sys

import numpy as np

# incontainer.sh cds to WREM_BASE, and setup.sh has already built PYTHONPATH for
# scetlib_qT -- so add this directory here rather than exporting PYTHONPATH from
# outside, which would clobber that.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ab_scale_route import QT_EDGES, _eval, make_bins  # noqa: E402

DEFAULT_QT_LO = [0.0, 1.0, 2.0, 4.0, 8.0, 33.0]


def _configure(path, threads, leg, piece):
    """``configure()`` from xsec_backend, but keeping the Scale_provider.

    xsec_backend.configure returns only ``(conf, sigma)``, and Vary.muf lives on
    the Scale_provider, so this mirrors it step for step and hands that back too.
    Kept deliberately parallel to the original -- if that one grows a step, this
    one is wrong until it grows the same step.
    """
    from wremnants.postprocessing.scetlib_ad.xsec_backend import (
        _import_scetlib,
        _scetlib_src,
    )

    sl_config, sl_variations, _ = _import_scetlib()
    conf = configparser.ConfigParser(inline_comment_prefixes="#")
    conf.read(os.path.join(_scetlib_src(), "prod", "scetlib_run", "defaults.conf"))
    if not conf.read(path):
        raise FileNotFoundError(path)

    order, alphas, decay, scales, sigma = sl_config.configure_calculation(conf)
    sl_config.configure_ew_parameters(conf, sigma)
    sl_config.configure_fiducial_volumes(conf, decay)
    varis = sl_variations.configure_variations(
        conf, os.path.join(os.path.dirname(os.path.abspath(path)), "variations.conf")
    )
    sl_variations.set_vary(varis[0], order, alphas, scales, sigma)

    # AFTER set_vary, which would otherwise put the central leg back.
    if leg:
        vy = scales.vary()
        vy.muf = leg
        scales.set_vary(vy)

    for p in sigma.sub_pieces():
        p.set_gradient_threads(int(threads) if threads else (os.cpu_count() or 8))
        p.set_gradient_node_cache(True)
    if piece != "matched":
        sub = sigma.sub_pieces()
        sigma = sub[0] if piece == "sing" else sub[1]
    return sigma, scales


def run_fresh(args, bins):
    """Vary.muf set before the first evaluation: nodes adapt. The reference."""
    s_cen, _ = _configure(args.base, args.threads, 0, args.piece)
    cen = _eval(s_cen, bins, np.asarray(s_cen.gradient_central(), float))
    s_var, _ = _configure(args.base, args.threads, args.leg, args.piece)
    var = _eval(s_var, bins, np.asarray(s_var.gradient_central(), float))
    return cen, var


def run_keepnodes(args, bins):
    """Evaluate central, then move the leg in place. What the cache build does."""
    sigma, _ = _configure(args.base, args.threads, 0, args.piece)
    p0 = np.asarray(sigma.gradient_central(), float)
    cen = _eval(sigma, bins, p0)
    # set_muf_keep_nodes lives on the sub-piece; with --piece matched reach both,
    # which is also the order build_pdf_variations uses (it holds one piece at a
    # time but shares the Scale_provider, so the sibling follows).
    targets = sigma.sub_pieces() if args.piece == "matched" else [sigma]
    for t in targets:
        t.set_muf_keep_nodes(args.leg)
    var = _eval(sigma, bins, p0)
    return cen, var


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", required=True, choices=("fresh", "keepnodes"))
    ap.add_argument("--base", required=True, help="the central runcard")
    ap.add_argument("--leg", type=int, default=-1, choices=(-1, 1),
                    help="Vary.muf leg: -1 down (kappa_F 0.5), +1 up (2.0)")
    ap.add_argument("--piece", default="matched",
                    choices=("matched", "sing", "nons"),
                    help="isolate a sub-piece; muF is meant to CANCEL between "
                         "them, so a piece that is individually fine while the "
                         "matched sum is not points at the cancellation")
    ap.add_argument("--iy", type=int, default=0, help="index into Y_EDGES")
    ap.add_argument("--qt-lo", type=float, nargs="+", default=DEFAULT_QT_LO,
                    help=f"lower qT edges, from {QT_EDGES}")
    ap.add_argument("--threads", type=int, default=64)
    ap.add_argument("-o", "--out", help="write the raw values as JSON")
    args = ap.parse_args()

    bins = make_bins(args.qt_lo, args.iy)
    cen, var = (run_fresh if args.mode == "fresh" else run_keepnodes)(args, bins)

    tag = f"{args.mode} leg={args.leg:+d} {args.piece}"
    if args.out:
        with open(args.out, "w") as f:
            json.dump({"tag": tag, "mode": args.mode, "leg": args.leg,
                       "piece": args.piece, "bins": bins.tolist(),
                       "cen": cen.tolist(), "var": var.tolist()}, f, indent=1)
        print(f"wrote {args.out}")
    print(f"\n{tag}")
    for k, b in enumerate(bins):
        print(f"  qT [{b[4]:4g},{b[5]:4g}]  var/cen = {var[k] / cen[k]:.6f}")


if __name__ == "__main__":
    main()
