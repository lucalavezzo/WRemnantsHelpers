#!/usr/bin/env python3
"""WHERE the transition-point response error lives, at the SIGMA level, split by
mechanism -- against an EXACT runcard refill, all arms in ONE process.

`anlmuf_interp_error.py` measured the total error for the analytic-muF modes.
It found the route fixes qT >= 24 by 2-9x and makes qT <= 24 WORSE by a
near-constant ~8 percentage points of the response, at every variation size and
both signs. A constant fraction of the response is the signature of a MISSING
first-order response, not of an interpolation remainder (which scales as D^2 or
D^3). This script separates the candidates by switching each one off:

  ad_muf_anl  0 = shipped member interpolation, 1 = + analytic DGLAP evolution
  ad_muf_abl  1  drop the member interpolation of the beam CONVOLUTIONS
              2  drop the member interpolation of the per-SITE rule weights
             16  freeze the explicit ln(muB/muF) of the beam matching
                 coefficients at the ANCHOR transition points

1|16 removes the transition response of the WHOLE muF sector, so
      resp(shipped) - resp(1|16)
is the size of that sector at the sigma level -- the number the ~9x RG
cancellation claim is about, measured rather than argued. If the shortfall at
qT [20,24] is LARGER than the sector, no amount of work inside the sector can
fix it.

Also printed, from `rule_cvals()`:
  c_val / sigma        the share of the bin carried by the rule's dead constant
  c_grad . dp / sigma  the first-order response of that constant that the
                       STAGED replay throws away (node_cval's gradient runs
                       only over the member coordinates, so d c/d x2 == 0)

REGIME. Say it on every number.
  FINITE variation      x2 = 0.35 / 0.75, x1,x3 = 0.3,0.9 -- the templates.
  NEAR-ANCHOR derivative x2 = 0.55, ~12x smaller -- what a FIT uses.
DO NOT DIAGNOSE on qT [18,20] or any bin whose true response is below ~1e-4 of
sigma: that is the node-ladder target of the reference itself.
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

# (label, ad_muf_anl, ad_muf_abl)
ARMS = [
    ("shipped",   0, 0),
    ("anl1",      1, 0),
    ("anl1only",  1, 1),
    ("noconv",    0, 1),
    ("nowsite",   0, 2),
    ("noLf",      0, 16),
    ("nomuf",     0, 1 | 16),
    ("anl1noLf",  1, 16),
]

# Arms that need ad_muf_abl bit 8 (the c_i1 evolution), i.e. a build that has
# it. Opt in with --with-i1 so a run against a build without it cannot trip the
# arm-separation guard and be misread as "the term does nothing".
EXTRA_ARMS = [
    ("anl1i1",     1, 8),
    ("anl1i1only", 1, 1 | 8),
]

# Arms at ad_muf_anl = 3 (the full alphas^3 evolution: P2, P0xP1, P1xP0,
# P0xP0xP0). With LIVE rules the nodes are filled in-process, so mode 3 needs no
# cache rebuild here -- only set_muf_analytic(3) BEFORE configure, so the conv
# provider loads the N3LO kernel set.
MODE3_ARMS = [
    ("anl3",       3, 0),           # the tier D-027 costed; measured flat
    ("anl3i1",     3, 8),
    ("anl3only",   3, 1),           # PURE analytic, full alphas^3
    ("anl3i1only", 3, 1 | 8),       # PURE analytic, full alphas^3 + c_i1
]

# Arms that need ad_muf_abl bit 64 (quartic Hermite residual). Bit 8 no longer
# exists as an ablation bit -- the c_i1 term is now ad_muf_i1, default ON -- so
# these are all "with c_i1".
HERM_ARMS = [
    ("anl1herm",  1, 64),
    ("anl3herm",  3, 64),
    ("anl3only",  3, 1),
    ("anl3pure",  3, 1),   # alias, kept so the label reads clearly
]

# Arms that need the RESIDUAL INTERPOLANT FORM field, ad_muf_abl bits 7..9
# (form = (abl >> 7) & 7).  Every form is exact at all three members, so each
# arm keeps kappa_F = 1/f, 1, f bit-identical and leaves the other 35 directions
# untouched -- what changes is only how the residual is carried to a
# displacement that sits at no knot.
#
#   quart  = the bit-64 quartic through the form field (a CONTROL: it must
#            reproduce the anl1herm arm to every digit)
#   bq03   = quadratic <-> quartic blended with theta = T^2/(T^2 + (A1-1)^2
#            + (A2-1)^2), T = 0.3   -- the conditioning-guarded quartic
#   bq1    = the same at T = 1
#   bq1a   = the same at T = 1, guarding on A1 alone
#   clip   = the quadratic times min((d/m)^2, 1): the quartic INSIDE the
#            stencil, never larger in magnitude than the quadratic OUTSIDE it
#   bc1    = quadratic <-> cubic, guarded on A1c, T = 1
SAFE_ARMS = [
    ("anl1cub",   1, 1 << 7),
    ("anl1quart", 1, 2 << 7),
    ("anl1bq03",  1, 3 << 7),
    ("anl1bq1",   1, 4 << 7),
    ("anl1bq1a",  1, 5 << 7),
    ("anl1clip",  1, 6 << 7),
    ("anl1bc1",   1, 7 << 7),
    ("anl1herm",  1, 64),
]

# Arms that need ad_muf_abl bit 32 (clamped extrapolation).
CLAMP_ARMS = [
    ("clamp",      0, 32),          # clamp with no analytic term
    ("anl1clamp",  1, 32),          # THE CANDIDATE
    ("anl1i1clamp", 1, 8 | 32),     # + the c_i1 evolution
    ("anl1clampw", 1, 32 | 64),     # + clamp the site weights too (unused bit)
]


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
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--x2", type=float, default=None)
    ap.add_argument("--x1", type=float, default=None)
    ap.add_argument("--x3", type=float, default=None)
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("--qt-lo", type=float, nargs="+", default=DEFAULT_QT_LO)
    ap.add_argument("--iy", type=int, default=0)
    ap.add_argument("--n-train", type=int, default=9)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--with-herm", action="store_true",
                    help="add the ad_muf_abl bit-64 arms (quartic Hermite "
                         "residual). Needs a build that implements it.")
    ap.add_argument("--with-mode3", action="store_true",
                    help="add the ad_muf_anl = 3 arms. Sets the mode BEFORE "
                         "configure so the N3LO conv kernels are loaded.")
    ap.add_argument("--with-safe", action="store_true",
                    help="add the residual-form arms (ad_muf_abl bits 7..9). "
                         "Needs a build that implements the form field.")
    ap.add_argument("--with-clamp", action="store_true",
                    help="add the ad_muf_abl bit-32 arms (clamped "
                         "extrapolation). Needs a build that implements it.")
    ap.add_argument("--with-i1", action="store_true",
                    help="add the ad_muf_abl bit-8 arms (evolve c_i1_qq/qg). "
                         "Needs a build that implements bit 8.")
    ap.add_argument("--arms", nargs="*", default=None,
                    help="subset of arm labels; default all")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    import scetlib_qT
    from wremnants.postprocessing.scetlib_ad import xsec_backend as xb

    def configure(path, threads=8, diff_scales=False):
        """xsec_backend.configure, with `sub_pieces` made optional.

        The upstream helper calls `sigma.sub_pieces()` unconditionally, which a
        `calculation_piece = sing` runcard does not have -- and the sing-only run
        is the experiment that separates OUR muF error from the model's frozen
        nonsingular. Same logic otherwise, so the matched runs are unaffected.
        """
        import configparser as _cp
        import os as _os
        # xb._import_scetlib returned (sl_config, sl_variations, sl_tf) until
        # 2026-08-26 and (sl_config, sl_variations) after -- the TF import was
        # dropped there so a cache build need not pay for TensorFlow. Take the
        # first two either way rather than pinning to one signature.
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

    pool = (ARMS + (EXTRA_ARMS if args.with_i1 else [])
            + (MODE3_ARMS if args.with_mode3 else [])
            + (HERM_ARMS if args.with_herm else [])
            + (CLAMP_ARMS if args.with_clamp else [])
            + (SAFE_ARMS if args.with_safe else []))
    arms_wanted = [a for a in pool if args.arms is None or a[0] in args.arms]
    # Which kernels the conv provider LOADS is decided when the calculation is
    # configured, and mode 3 fills four conv kinds one fixed order above nnlo,
    # so the mode has to be set FIRST. Every arm then reads the SAME nodes;
    # modes 0 and 1 simply do not look at the extra kinds.
    if any(a[1] >= 3 for a in arms_wanted):
        scetlib_qT.DrellYan.set_muf_analytic(3)

    f = args.knot
    if args.x2 is None and args.x1 is None and args.x3 is None:
        raise SystemExit("give at least one of --x1 --x2 --x3")
    bins = make_bins(args.qt_lo, args.iy)
    tag = f"x1_{args.x1}_x2_{args.x2}_x3_{args.x3}_k{f:.6f}"
    tmp = os.path.join(os.path.dirname(os.path.abspath(args.out)), f"_{tag}.conf")
    _conf_with(args.base, tmp, x2=args.x2, x1=args.x1, x3=args.x3)

    # THE REFERENCE, computed once and shared by every arm.
    _, s_run = configure(tmp, threads=args.threads, diff_scales=False)
    run_var = _eval(s_run, bins, np.asarray(s_run.gradient_central(), float))

    _, s_par = configure(args.base, threads=args.threads, diff_scales=True)
    # calculation_piece = sing has no matched partner, so no sub-pieces and no
    # fixed-order columns. Running the same attribution BOTH ways is the test
    # that separates our muF error from the model's frozen nonsingular: the
    # model's fo_node_value depends only on kappa_R, alphaS and kappa_F, so its
    # transition response is identically zero, while the runcard's nonsingular
    # (FO minus the profiled singular expansion) has one.
    if hasattr(s_par, "sub_pieces"):
        sing, nons = s_par.sub_pieces()
    else:
        sing, nons = s_par, None
    names = list(s_par.gradient_param_names())
    p0 = np.asarray(s_par.gradient_central(), float)
    cp = configparser.ConfigParser(inline_comment_prefixes="#")
    cp.read(args.base)
    pdf_set = cp["QCD"]["pdf_set"]
    nf = cp["QCD"].getint("nf", fallback=5)

    # `prepare` builds the outer node set; it lives on the MATCHED wrapper.
    # Unpaired (calculation_piece = sing) the resummed half owns its own grid,
    # so one evaluation is what builds it.
    if hasattr(s_par, "prepare"):
        s_par.prepare(bins, p0)
    else:
        _eval(s_par, bins, p0)
    sing.build_bin_rules(bins, p0, n_train=args.n_train, n_hvp=1, seed=4242,
                         n_jobs=args.threads)
    sets = [pdf_set] * 2
    mem = np.zeros(2, dtype=np.int32)
    sing.build_pdf_variations(sets, mem, nf, p0, n_train_var=3, n_eig=0,
                              as_cen=0.0, as_step=0.0,
                              muf_lo=1.0 / f, muf_hi=f)
    if nons is not None:
        nons.build_fo_pdf_variations(sets, mem, nf, bins,
                                     np.asarray(nons.gradient_central()),
                                     n_eig=0, as_cen=0.0, as_step=0.0,
                                     muf_lo=1.0 / f, muf_hi=f)

    def rule(q, want_grad=False):
        r = sing.sigma_binned_rule_batch(bins, q)
        v = np.asarray(r["value"], float).reshape(-1)
        if not want_grad:
            return v
        return v, np.asarray(r["grad"], float).reshape(len(v), -1)

    p = p0.copy()
    varied = []
    for nmv, v in (("scale_x1", args.x1), ("scale_x2", args.x2),
                   ("scale_x3", args.x3)):
        if v is not None:
            p[names.index(nmv)] = v
            varied.append(nmv)
    dp = p - p0

    # ---- the rule's dead constant, and the gradient staging discards --------
    cv = sing.rule_cvals()
    keymap = {}
    for d in cv:
        k = tuple(np.round(np.asarray(d["key"], float), 6))
        keymap[k] = d
    cval, cgrad_dp = np.zeros(len(bins)), np.zeros(len(bins))
    for i, b in enumerate(bins):
        k = tuple(np.round(np.asarray(b, float), 6))
        d = keymap.get(k)
        if d is None:
            continue
        cval[i] = float(d["c_val"])
        g = np.asarray(d["c_grad"], float)
        if g.size == dp.size:
            cgrad_dp[i] = float(np.dot(g, dp))

    out_arms = {}
    for label, anl, abl in arms_wanted:
        scetlib_qT.DrellYan.set_muf_analytic(anl)
        scetlib_qT.DrellYan.set_muf_ablate(abl)
        cen, gcen = rule(p0, want_grad=True)
        var = rule(p)
        out_arms[label] = dict(
            anl=anl, abl=abl, cen=cen.tolist(), var=var.tolist(),
            resp=(var / cen - 1.0).tolist(),
            dev=(var / run_var - 1.0).tolist(),
            grad_lin=[float(np.dot(gcen[i], dp)) / cen[i] for i in range(len(cen))],
        )
    scetlib_qT.DrellYan.set_muf_analytic(0)
    scetlib_qT.DrellYan.set_muf_ablate(0)

    # ARM SEPARATION. A clean null between two arms of an A/B is this study's
    # known signature of a shared cached result, so refuse to report one.
    ref = out_arms[arms_wanted[0][0]]
    seps = {}
    for label, _, _ in arms_wanted[1:]:
        a = out_arms[label]
        dc = max(abs(x / y - 1.0) for x, y in zip(a["cen"], ref["cen"]))
        dv = max(abs(x / y - 1.0) for x, y in zip(a["var"], ref["var"]))
        seps[label] = (dc, dv)
        print(f"  ARM SEPARATION {arms_wanted[0][0]} vs {label:9s}: "
              f"max|d central| = {dc:.3e}  max|d varied| = {dv:.3e}")
        if dv < 1e-13:
            raise SystemExit(f"arm {label} did not separate -- refusing a null")

    ship = np.asarray(ref["cen"], float)
    true_resp = run_var / ship - 1.0

    res = dict(x1=args.x1, x2=args.x2, x3=args.x3, knot=f, iy=args.iy,
               n_train=args.n_train, varied=varied, bins=bins.tolist(),
               names=names, dp=dp.tolist(), run_var=run_var.tolist(),
               true_resp=true_resp.tolist(), c_val=cval.tolist(),
               c_val_over_sigma=(cval / ship).tolist(),
               c_grad_dp_over_sigma=(cgrad_dp / ship).tolist(),
               arms=out_arms, separations={k: list(v) for k, v in seps.items()})
    json.dump(res, open(args.out, "w"), indent=1)

    lab = ", ".join(f"{n}={v}" for n, v in
                    (("x1", args.x1), ("x2", args.x2), ("x3", args.x3))
                    if v is not None)
    print(f"\n=== {lab}   |Y| [{Y_EDGES[args.iy]}, {Y_EDGES[args.iy+1]}], "
          f"knot f = {f}, n_train = {args.n_train} ===")

    print("\nRESPONSE PER ARM (sigma_arm(var)/sigma_arm(anchor) - 1), and the "
          "TRUE response from the runcard refill")
    hdr = f"{'qT bin':>13}{'true':>12}"
    for label, _, _ in arms_wanted:
        hdr += f"{label:>12}"
    print(hdr)
    for k, b in enumerate(bins):
        line = f"[{b[4]:5g},{b[5]:5g}]".rjust(13) + f"{true_resp[k]:>+12.3e}"
        for label, _, _ in arms_wanted:
            line += f"{out_arms[label]['resp'][k]:>+12.3e}"
        print(line)

    print("\nERROR PER ARM as a % of the TRUE response  (dev = arm/runcard - 1)")
    hdr = f"{'qT bin':>13}{'true resp':>12}"
    for label, _, _ in arms_wanted:
        hdr += f"{label:>12}"
    print(hdr)
    for k, b in enumerate(bins):
        line = f"[{b[4]:5g},{b[5]:5g}]".rjust(13) + f"{true_resp[k]:>+12.3e}"
        for label, _, _ in arms_wanted:
            d = out_arms[label]["dev"][k]
            line += (f"{100.0*d/true_resp[k]:>+11.1f}%" if true_resp[k]
                     else f"{'--':>12}")
        print(line)

    print("\nSECTOR SIZES, as a fraction of the TRUE response "
          "(resp(shipped) - resp(arm)) / true_resp")
    print(f"{'qT bin':>13}{'true resp':>12}{'muF sector':>12}{'Lf half':>12}"
          f"{'conv half':>12}{'site wts':>12}{'c_val/sig':>12}"
          f"{'cgrad.dp/sig':>14}{'as % resp':>11}")
    for k, b in enumerate(bins):
        R = true_resp[k]
        sh = out_arms["shipped"]["resp"][k] if "shipped" in out_arms else float("nan")
        def frac(lbl):
            if lbl not in out_arms or not R:
                return float("nan")
            return (sh - out_arms[lbl]["resp"][k]) / R
        line = (f"[{b[4]:5g},{b[5]:5g}]".rjust(13) + f"{R:>+12.3e}"
                + f"{frac('nomuf'):>+12.3f}{frac('noLf'):>+12.3f}"
                + f"{frac('noconv'):>+12.3f}{frac('nowsite'):>+12.3f}"
                + f"{cval[k]/ship[k]:>+12.3e}{cgrad_dp[k]/ship[k]:>+14.3e}"
                + (f"{100.0*cgrad_dp[k]/ship[k]/R:>+10.1f}%" if R else f"{'--':>11}"))
        print(line)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
