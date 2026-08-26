#!/usr/bin/env python3
"""Decompose the CENTRAL reco closure of the scetlib_ad model into two terms.

``validate_reco.py`` gives one number (yield-weighted mean |sigma_reco/nominal - 1|).
That number is a sum of two unrelated things, fixed by unrelated work, so it is
worth splitting before anyone acts on it.

Three reco predictions, all on the card's (ptll, yll) grid:

  ref  = the histmaker's own 'nominal' -- MiNNLO reweighted to SCETlib+DYTurbo
         event by event, then reconstructed. THE reference.
  fld  = R @ sigma_gen[CorrZ]   -- the PRODUCTION gen prediction (the same
         correction file the histmaker was reweighted with), folded with the
         card's binned response matrix R.
  mod  = R @ sigma_gen[model]   -- the model's own matched gen prediction,
         folded with the same R.

  mod / ref  =  (mod / fld)  x  (fld / ref)      [ CALC ] x [ MC ]

  * mod/fld is a pure GEN-LEVEL difference: our matched cross section against
    the production one on the 210-bin gen grid. It is expected to be nonzero and
    NOT a bug -- production uses DYTurbo for the nonsingular, we use SCETlib's
    in-house analytic V+jet -- and it cancels in every variation ratio.
  * fld/ref is NOT a fold error, and calling it one would be wrong. R is stored
    as R_raw / N_gen, so R @ N_gen reproduces the histmaker's reco nominal up to
    the events that have NO gen column: measured, a nearly flat -7.6e-4 (max
    2.3e-3), which is the reco-selected events whose GEN |Y| exceeds 2.5 and so
    falls in the dropped gen overflow.  A near-constant offset is removed by the
    shape comparison, so the central prediction carries essentially no fold
    approximation. What fld/ref actually measures is whether the
    CORRECTED MC's own gen spectrum N_gen(g) has the same shape as the
    correction file's sigma(g) on this gen grid. It is nonzero because the
    histmaker applies the correction through helicity moments on a MiNNLO
    sample, which is not the same operation as multiplying a binned UL
    spectrum, and because MiNNLO's residual (Q, y, qT) correlation survives
    inside a gen bin. It is therefore labelled MC, not FOLD.
    The experiment that would isolate the helicity route: rebuild the histmaker
    with --noTheoryCorrsViaHelicities and re-measure; whatever survives is the
    within-gen-bin MiNNLO residual.

Every comparison is SHAPE: sigma is in pb and 'nominal' is a weighted yield, so
one global scale is divided out first (and reported).
"""

import argparse
import os
import sys

import numpy as np

_WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
for _p in (_WREM, os.path.join(_WREM, "scripts", "rabbit", "scetlib_ad")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import validate_variations as VV  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from validate_variations_reco import (  # noqa: E402
    _gen_reference,
    load_hist,
    plot_map,
)

CORRZ = os.path.join(
    _WREM,
    "wremnants-data/data/TheoryCorrections/"
    "scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4",
)


def shape_metrics(a, b, w, tag):
    """|a/b - 1| after one global scale on a. Returns (wmean, max, ratio)."""
    a = np.asarray(a, float).reshape(-1)
    b = np.asarray(b, float).reshape(-1)
    w = np.asarray(w, float).reshape(-1)
    good = (b > 0) & (w > 0) & np.isfinite(a)
    scale = b[good].sum() / a[good].sum()
    r = np.full(a.shape, np.nan)
    r[good] = a[good] * scale / b[good]
    d = np.abs(r[good] - 1.0)
    wm = float(np.average(d, weights=w[good]))
    print(
        f"  {tag:<34} global scale {scale:.6g} | yield-weighted mean|dev| "
        f"{wm:.5f} | max {d.max():.5f} | p95 {np.percentile(d, 95):.5f}"
    )
    return wm, float(d.max()), r


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--datacard", required=True)
    ap.add_argument("--histmaker", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--conf", required=True)
    ap.add_argument("--corrz", default=CORRZ)
    ap.add_argument("--sample", default="Zmumu_2016PostVFP")
    ap.add_argument("--threads", type=int, default=64)
    ap.add_argument("--plot-dir", default=None)
    args = ap.parse_args()

    from rabbit.inputdata import FitInputData

    from wremnants.postprocessing.scetlib_ad.param_model import SCETlibADParamModel

    indata = FitInputData(args.datacard)
    model = SCETlibADParamModel(
        indata, cache=args.cache, conf=args.conf, gen_level=0,
        threads=args.threads, fit_params="lambda2", poi_params="lambda2",
        jitCompile="off",
    )
    reco_axes = model._fit_axes(indata)
    ptll_edges, yll_edges = reco_axes[0][1], reco_axes[1][1]
    R = np.asarray(model.R.numpy(), float)
    sg_mod = np.asarray(model.sigma_gen_central_flat.numpy(), float)
    (qt_name, Te), (y_name, Ye) = model.gen_axes
    nT, nY = Te.size - 1, Ye.size - 1

    # --- production gen prediction on the same grid -------------------------
    labels, cen, on_grid = _gen_reference(args.corrz, Ye, Te)
    sg_ref = on_grid(cen).T.reshape(-1)          # (qT, |Y|) flattened

    # --- histmaker nominal on the card's reco grid --------------------------
    hn = load_hist(args.histmaker, args.sample, "nominal")
    nom_names = [a.name for a in hn.axes]
    nv = np.asarray(hn.values(flow=False), float)
    keep_idx = [nom_names.index(n) for n, _ in reco_axes]
    drop = tuple(i for i in range(nv.ndim) if i not in keep_idx)
    if drop:
        nv = nv.sum(axis=drop)
    rem = [n for n in nom_names if nom_names.index(n) in keep_idx]
    nv = np.transpose(nv, [rem.index(n) for n, _ in reco_axes])
    ref = nv[: len(ptll_edges) - 1, : len(yll_edges) - 1]

    from wremnants.postprocessing.scetlib_ad.response import R_info_from_auxiliary

    N_gen = np.asarray(R_info_from_auxiliary(indata)["N_gen"], float).reshape(-1)
    mod = (R @ sg_mod).reshape(model.reco_shape)
    fld = (R @ sg_ref).reshape(model.reco_shape)
    ident = (R @ N_gen).reshape(model.reco_shape)
    with np.errstate(divide="ignore", invalid="ignore"):
        idr = np.where(ref > 0, ident / ref - 1.0, 0.0)
    print(
        f"\nidentity check: (R @ N_gen) vs histmaker nominal, max|dev| "
        f"{np.abs(idr).max():.3e} over {ref.size} reco bins\n"
        "  -> the CENTRAL prediction carries no fold approximation; the second\n"
        "     term below is a gen-spectrum difference, not a fold error."
    )

    print("\n=== GEN level (210 bins) ===")
    shape_metrics(sg_mod, sg_ref, sg_ref, "CALC  sigma_gen model / CorrZ")
    shape_metrics(sg_ref, N_gen, N_gen, "MC    CorrZ / N_gen (corrected MC)")

    print("\n=== RECO level (780 bins), all shape ===")
    wm_tot, mx_tot, r_tot = shape_metrics(mod, ref, ref, "TOTAL  mod / histmaker nominal")
    wm_gen, mx_gen, r_gen = shape_metrics(mod, fld, ref, "CALC   mod / (R @ CorrZ)")
    wm_fld, mx_fld, r_fld = shape_metrics(fld, ref, ref, "MC     (R @ CorrZ) / nominal")
    print(
        f"\n  check: CALC + MC = {wm_gen + wm_fld:.5f} vs TOTAL {wm_tot:.5f} "
        "(they are not additive in general -- the two residuals partly cancel "
        "or reinforce bin by bin; this only says whether one dominates)"
    )

    # --- where it lives ------------------------------------------------------
    r_tot = r_tot.reshape(model.reco_shape)
    r_gen = r_gen.reshape(model.reco_shape)
    r_fld = r_fld.reshape(model.reco_shape)
    print(
        f"\n  per-ptll-bin, yll summed with reference weights "
        f"({len(ptll_edges)-1} bins):"
    )
    print(f"    {'ptll bin':>14} {'yield frac':>11} {'TOTAL':>9} {'CALC':>9} {'MC':>9}")
    wtot = ref.sum()
    for k in range(len(ptll_edges) - 1):
        w = ref[k]
        if w.sum() <= 0:
            continue
        def proj(r):
            return float(np.average(r[k], weights=w)) - 1.0
        print(
            f"    [{ptll_edges[k]:5g},{ptll_edges[k+1]:5g}] {w.sum()/wtot:11.4f} "
            f"{proj(r_tot):+9.2e} {proj(r_gen):+9.2e} {proj(r_fld):+9.2e}"
        )

    # headline excluding the lowest reco ptll bin, which is where the gen
    # qT [0,1] nonsingular-cutoff convention lands
    for kmin, lab in ((1, "ptll > 1 GeV"), (2, "ptll > 1.5 GeV")):
        sl = slice(kmin, None)
        d = np.abs(r_tot[sl] - 1.0)
        w = ref[sl]
        print(
            f"\n  TOTAL restricted to {lab}: yield-weighted mean|dev| "
            f"{float(np.average(d, weights=w)):.5f} (max {d.max():.5f}); "
            f"that region carries {w.sum()/wtot:.4f} of the yield"
        )

    if args.plot_dir:
        os.makedirs(args.plot_dir, exist_ok=True)
        for arr, nm, ttl, cb in (
            (r_tot, "central_map_total", "TOTAL: model / histmaker nominal $-$ 1",
             "model / nominal $-$ 1  [%]"),
            (r_gen, "central_map_calc", r"CALC: model / ($R\,\otimes\,$CorrZ) $-$ 1",
             r"model / ($R\,\otimes\,$CorrZ) $-$ 1  [%]"),
            (r_fld, "central_map_mc", r"MC: ($R\,\otimes\,$CorrZ) / nominal $-$ 1",
             r"($R\,\otimes\,$CorrZ) / nominal $-$ 1  [%]"),
        ):
            plot_map(arr - 1.0, ptll_edges, yll_edges, ttl,
                     os.path.join(args.plot_dir, nm + ".png"), cbar=cb)
        print(f"\n  maps -> {args.plot_dir}")


if __name__ == "__main__":
    main()
