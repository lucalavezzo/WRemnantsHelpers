#!/usr/bin/env python3
"""ONE cache, built at a GIVEN anchor, evaluated at a LIST of points.

The experiment this serves (Luca, 2026-08-26). Every previous round measured

    cache-built-at-nominal, evaluated at the varied transition point
      versus
    a fresh runcard rerun at the varied point

which confounds the DISPLACEMENT error with any cache-vs-live difference. Build
a SECOND cache whose anchor IS the varied point and the confound is removed:

    cache_varied @ its own anchor    -- exact by construction, same machinery
    cache_nominal @ varied           -- the same point, reached by displacement

and the difference between those two is the displacement/replay error alone.

This script is one arm of that. Run it once per anchor:

    --anchor  the transition-point triple the CACHE is built at ('-' = keep the
              base runcard's value), e.g.  -,0.35,-
    --eval    a point to evaluate that cache at, repeatable, same format.
    --direct  also do a fresh runcard refill (adaptive, diff_scales off) AT THE
              ANCHOR -- the live reference for that anchor.

Per eval point it records THREE numbers off the SAME configured object:

    rule   sigma_binned_rule_batch  -- the cache replay (compressed per-bin
           rule + stored muF members). This is "the cache".
    live   sigma_binned_batch       -- the same object integrated live at that
           parameter point, no rule, no member interpolation.
    direct (anchor only) a separately configured runcard at that point.

Cache construction here is the IN-PROCESS one: build_bin_rules +
build_pdf_variations with n_eig = 0, no alphaS pair, muF knots at 1/f and f.
That is exactly what the on-disk builder writes for the same settings, and it is
the machinery every previous transition number came from. NOTE that the
builder's literal `--no-pdf` is NOT this: it sets plan = None and therefore
builds NO members at all, muF included, which would delete the whole route the
transition points travel on.

REGIME. Say it on every number.
  FINITE variation       x2 = 0.35 / 0.75, x1,x3 = 0.3,0.9 -- the templates.
  NEAR-ANCHOR derivative x2 = 0.55 -- what a FIT uses.
DO NOT DIAGNOSE on qT [18,20] or any bin whose true response is below ~1e-4 of
sigma; the reference there is no better than the number being measured.
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
DEFAULT_QT_LO = [20.0, 24.0, 28.0, 33.0, 44.0]


def make_bins(qt_lo, iy):
    out = []
    for lo in qt_lo:
        k = QT_EDGES.index(lo)
        out.append([60.0, 120.0, Y_EDGES[iy], Y_EDGES[iy + 1],
                    QT_EDGES[k], QT_EDGES[k + 1]])
    return np.asarray(out, float)


def parse_triple(s):
    """'-,0.35,-' -> (None, 0.35, None)."""
    parts = [p.strip() for p in s.split(",")]
    if len(parts) != 3:
        raise SystemExit(f"bad triple {s!r}, want x1,x2,x3 with '-' for unchanged")
    return tuple(None if p == "-" else float(p) for p in parts)


def conf_with(base, out, tri):
    c = configparser.ConfigParser(inline_comment_prefixes="#")
    c.read(base)
    tp = c["Calculation_settings"]["transition_points"]
    cur = [v.strip() for v in tp.strip("[] ").split(",")]
    new = [cur[i] if tri[i] is None else f"{tri[i]}" for i in range(3)]
    c["Calculation_settings"]["transition_points"] = "[" + ", ".join(new) + "]"
    with open(out, "w") as f:
        c.write(f)
    return out, new


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--anchor", default="-,-,-")
    ap.add_argument("--eval", action="append", required=True)
    ap.add_argument("--direct", action="store_true")
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("--qt-lo", type=float, nargs="+", default=DEFAULT_QT_LO)
    ap.add_argument("--iy", type=int, default=0)
    ap.add_argument("--n-train", type=int, default=9)
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--tag", default="arm")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    from wremnants.postprocessing.scetlib_ad import xsec_backend as xb

    def configure(path, threads=8, diff_scales=False):
        import configparser as _cp
        import os as _os
        _imp = xb._import_scetlib()
        sl_config, sl_variations = _imp[0], _imp[1]
        src = xb._scetlib_src()
        conf = _cp.ConfigParser(inline_comment_prefixes="#")
        conf.read(_os.path.join(src, "prod", "scetlib_run", "defaults.conf"))
        if not conf.read(path):
            raise FileNotFoundError(path)
        order, alphas, decay, scales, sigma = sl_config.configure_calculation(conf)
        sl_config.configure_ew_parameters(conf, sigma)
        sl_config.configure_fiducial_volumes(conf, decay)
        if diff_scales:
            sigma.set_diff_scales(1)
        varis = sl_variations.configure_variations(
            conf, _os.path.join(_os.path.dirname(_os.path.abspath(path)),
                                "variations.conf"))
        sl_variations.set_vary(varis[0], order, alphas, scales, sigma)
        pieces = sigma.sub_pieces() if hasattr(sigma, "sub_pieces") else (sigma,)
        for piece in pieces:
            piece.set_gradient_threads(int(threads))
            piece.set_gradient_node_cache(True)
        return conf, sigma

    def live(sigma, bins, p):
        out = sigma.sigma_binned_batch(bins, p)
        v = out[0] if isinstance(out, (tuple, list)) else out
        return np.asarray(v, float).reshape(-1)

    bins = make_bins(args.qt_lo, args.iy)
    f = args.knot
    anchor_tri = parse_triple(args.anchor)
    here = os.path.dirname(os.path.abspath(args.out))
    anchor_conf, anchor_tp = conf_with(
        args.base, os.path.join(here, f"_conf_{args.tag}_anchor.conf"), anchor_tri)
    print(f"ANCHOR runcard transition_points = [{', '.join(anchor_tp)}]", flush=True)

    res = dict(tag=args.tag, base=args.base, anchor=list(anchor_tri),
               anchor_tp=anchor_tp, knot=f, iy=args.iy, seed=args.seed,
               n_train=args.n_train, bins=bins.tolist(), points={})

    # ---- the DIRECT (fresh-runcard, adaptive, no diff_scales) reference -----
    if args.direct:
        _, s_run = configure(anchor_conf, threads=args.threads, diff_scales=False)
        direct = live(s_run, bins, np.asarray(s_run.gradient_central(), float))
        res["direct_at_anchor"] = direct.tolist()
        print("DIRECT at anchor:", " ".join(f"{v:.10e}" for v in direct), flush=True)
        del s_run

    # ---- THE CACHE: rules + muF members, built AT THE ANCHOR ----------------
    cp = configparser.ConfigParser(inline_comment_prefixes="#")
    cp.read(anchor_conf)
    pdf_set = cp["QCD"]["pdf_set"]
    nf = cp["QCD"].getint("nf", fallback=5)

    _, s_par = configure(anchor_conf, threads=args.threads, diff_scales=True)
    sing, nons = s_par.sub_pieces()
    names = list(s_par.gradient_param_names())
    p0 = np.asarray(s_par.gradient_central(), float)
    res["names"] = names
    res["p0"] = p0.tolist()

    s_par.prepare(bins, p0)
    sing.build_bin_rules(bins, p0, n_train=args.n_train, n_hvp=1,
                         seed=args.seed, n_jobs=args.threads)
    sets = [pdf_set] * 2
    mem = np.zeros(2, dtype=np.int32)
    sing.build_pdf_variations(sets, mem, nf, p0, n_train_var=3, n_eig=0,
                              as_cen=0.0, as_step=0.0,
                              muf_lo=1.0 / f, muf_hi=f)
    nons.build_fo_pdf_variations(sets, mem, nf, bins,
                                 np.asarray(nons.gradient_central(), float),
                                 n_eig=0, as_cen=0.0, as_step=0.0,
                                 muf_lo=1.0 / f, muf_hi=f)
    print(f"cache built: {len(bins)} bins, n_train {args.n_train}, seed "
          f"{args.seed}, muF knots {1.0/f:g}/1/{f:g}, n_eig 0, alphaS pair off",
          flush=True)

    for spec in args.eval:
        tri = parse_triple(spec)
        p = p0.copy()
        for k, nm in enumerate(("scale_x1", "scale_x2", "scale_x3")):
            if tri[k] is not None:
                p[names.index(nm)] = tri[k]
        r = sing.sigma_binned_rule_batch(bins, p)
        rv = np.asarray(r["value"], float).reshape(-1)
        lv = live(s_par, bins, p)
        key = spec
        res["points"][key] = dict(
            tri=list(tri), p=p.tolist(), rule=rv.tolist(), live=lv.tolist(),
            is_anchor=bool(np.allclose(p, p0, rtol=0, atol=0)),
        )
        print(f"EVAL {key:>12s}  anchor={res['points'][key]['is_anchor']}")
        print("   rule:", " ".join(f"{v:.10e}" for v in rv))
        print("   live:", " ".join(f"{v:.10e}" for v in lv))
        print("   rule/live-1:", " ".join(f"{a/b-1:+.3e}" for a, b in zip(rv, lv)),
              flush=True)

    # SEPARATION GUARD: distinct eval points must give distinct answers, or the
    # result is a shared cached value and not a measurement.
    keys = list(res["points"])
    for i in range(1, len(keys)):
        a = np.asarray(res["points"][keys[0]]["rule"], float)
        b = np.asarray(res["points"][keys[i]]["rule"], float)
        d = float(np.max(np.abs(b / a - 1.0)))
        print(f"  SEPARATION rule {keys[0]} vs {keys[i]}: max|rel| = {d:.3e}")
        if d < 1e-13:
            raise SystemExit(f"eval points {keys[0]} and {keys[i]} did not "
                             "separate -- refusing a null")

    json.dump(res, open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
