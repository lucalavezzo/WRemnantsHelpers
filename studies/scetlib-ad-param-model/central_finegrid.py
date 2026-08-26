#!/usr/bin/env python3
r"""CENTRAL reco closure of the scetlib_ad model on TWO gen grids, same region.

The variation side of the finer response-matrix gen binning is measured
(260826_scetlib_ad_response_genbinning). This is the CENTRAL side: does folding
sigma_gen through a 3.7x finer gen grid move the central reco prediction?

Both arms come out of ONE histmaker file that carries both gen grids
(``mz_dilepton --responseGenBinning theoryCorr``):

  shipped   nominal_prefsr_yieldsUnfolding + prefsr           21 x 10 gen bins
  fine      nominal_prefsr_yieldsResponse  + prefsr_response  70 x 11 gen bins

so the MC is literally the same events with the same weights on both sides.

WHY A GEN REGION, AND WHY IT IS LIKE-FOR-LIKE.  A cache over all 770 fine gen
bins is expensive, so the comparison is restricted to a contiguous gen rectangle
whose edges are shipped-grid edges.  Because the fine edges are a strict
refinement of the shipped ones, the rectangle is the SAME phase-space region on
both grids, and

    sigma_reco^S(b) = sum_{g in S} [R_raw(b,g) / N_gen(g)] sigma(g)

is compared to the reference

    ref^S(b)        = sum_{g in S} R_raw(b,g)        ( = R @ N_gen restricted )

which is the corrected-MC reco yield fed by gen region S.  R_raw is additive, so
ref^S is IDENTICALLY the same number on both grids -- verified below to machine
precision.  The whole difference between the two arms is therefore the
NUMERATOR's gen granularity: on the coarse grid sigma is spread inside a gen bin
in proportion to N_gen, on the fine grid it is resolved.

The two-term split is the one from ``reco_central_decompose.py``:

    mod / ref = (mod / fld) x (fld / ref)   =   CALC x MC

  CALC  mod/fld : our matched sigma_gen against the production CorrZ file's, both
                  folded with the same R.  A gen-level calculation difference
                  (different nonsingular generator), not a bug.
  MC    fld/ref : whether the corrected MC's own gen spectrum N_gen(g) has the
                  same shape as the correction file's sigma(g) on this gen grid.
                  NOT a fold error (see the identity above).

Every comparison is SHAPE (one global scale divided out) unless --absolute.
"""

import argparse
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
for _p in (_WREM, os.path.join(_WREM, "scripts", "rabbit", "scetlib_ad"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CORRZ = os.path.join(
    _WREM,
    "wremnants-data/data/TheoryCorrections/"
    "scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4",
)
HISTMAKER = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
    "260826_Z_histmaker_respgrid/mz_dilepton_respgrid.hdf5"
)
SAMPLE = "Zmumu_2016PostVFP"
RECO = ("ptll", "yll")


# --------------------------------------------------------------------------- #
def edge_index(edges, x, what):
    """Index of edge ``x`` in ``edges``, or raise -- no snapping, no tolerance
    beyond float noise.  The region MUST land on real edges of both grids or the
    two arms are not the same phase space."""
    i = int(np.argmin(np.abs(np.asarray(edges, float) - x)))
    if abs(edges[i] - x) > 1e-9:
        raise SystemExit(
            f"{what}: {x:g} is not an edge of this grid; edges are {list(edges)}"
        )
    return i


def load_grid(path, fine, reco_axes=RECO):
    from wremnants.postprocessing.scetlib_np import response_matrix as RM

    kw = dict(
        sample_key=SAMPLE,
        reco_axes=reco_axes,
        gen_axes=("ptVGen", "absYVGen"),
    )
    if fine:
        kw.update(hist_name=RM.RESPONSE_HIST, gen_total_name=RM.RESPONSE_GENTOTAL)
    info = RM.load_R(path, **kw)
    return info


def crop_reco(R, reco_axes, n_keep):
    """Keep the first ``n_keep[i]`` bins of each reco axis (the card's range)."""
    sl = tuple(slice(0, n) for n in n_keep) + (slice(None),) * (R.ndim - len(n_keep))
    out = [(nm, np.asarray(e, float)[: n + 1]) for (nm, e), n in zip(reco_axes, n_keep)]
    return R[sl], out


def shape_metrics(a, b, w, tag, absolute=False):
    a = np.asarray(a, float).reshape(-1)
    b = np.asarray(b, float).reshape(-1)
    w = np.asarray(w, float).reshape(-1)
    good = (b > 0) & (w > 0) & np.isfinite(a)
    scale = 1.0 if absolute else b[good].sum() / a[good].sum()
    r = np.full(a.shape, np.nan)
    r[good] = a[good] * scale / b[good]
    d = np.abs(r[good] - 1.0)
    wm = float(np.average(d, weights=w[good]))
    print(
        f"  {tag:<40} scale {scale:.6g} | wmean|dev| {wm:.6f} | max {d.max():.6f} "
        f"| p95 {np.percentile(d, 95):.6f}"
    )
    return wm, float(d.max()), r, scale


def sigma_gen_on(conf, cache, gen_axes, Q_lo, Q_hi, threads, label):
    """sigma_gen at the cache's anchor, folded onto ``gen_axes`` (qT-major flat)."""
    from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

    core = ScetlibADXsec(conf, cache, threads=threads)
    fold = core.fold_for(gen_axes, Q_lo, Q_hi)
    vals, _ = core.values_and_jacobian(core.anchor.copy())
    sg = fold(np.asarray(vals, float))
    print(
        f"  [{label}] cache {os.path.basename(os.path.dirname(cache))} : "
        f"{core.bins.shape[0]} cache bins -> {sg.size} gen bins, "
        f"y_convention {fold.y_convention}, sum {sg.sum():.8g} pb"
    )
    return sg, core, fold


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--histmaker", default=HISTMAKER)
    ap.add_argument("--corrz", default=CORRZ)
    ap.add_argument("--fine-cache", required=True)
    ap.add_argument("--fine-conf", required=True)
    ap.add_argument("--shipped-cache", required=True)
    ap.add_argument("--shipped-conf", required=True)
    ap.add_argument("--qt", nargs=2, type=float, required=True,
                    help="gen qT region [lo, hi], both edges of BOTH grids")
    ap.add_argument("--absy", nargs=2, type=float, required=True)
    ap.add_argument("--reco-ptll-bins", type=int, default=39,
                    help="reco ptll bins the card carries (edges 0..44)")
    ap.add_argument("--reco-yll-bins", type=int, default=20)
    ap.add_argument("--threads", type=int, default=64)
    ap.add_argument("--out", default=None, help="npz to dump the arrays into")
    ap.add_argument("--card", default=None,
                    help="optional: cross-check the shipped R against the card's "
                         "response auxiliary, and take lumi for the absolute mode")
    args = ap.parse_args()

    qt_lo, qt_hi = args.qt
    y_lo, y_hi = args.absy

    print("=" * 78)
    print(" CENTRAL reco closure, shipped vs fine gen grid, one gen region")
    print("=" * 78)
    print(f"histmaker : {args.histmaker}")
    print(f"region    : gen qT [{qt_lo:g}, {qt_hi:g}] x |Y| [{y_lo:g}, {y_hi:g}]")

    # ---- 1. both response matrices, out of the same file --------------------
    inf_s = load_grid(args.histmaker, fine=False)
    inf_f = load_grid(args.histmaker, fine=True)
    n_keep = (args.reco_ptll_bins, args.reco_yll_bins)
    R_s, reco_s = crop_reco(inf_s["R"], inf_s["reco_axes"], n_keep)
    R_f, reco_f = crop_reco(inf_f["R"], inf_f["reco_axes"], n_keep)
    N_s = np.asarray(inf_s["N_gen"], float)
    N_f = np.asarray(inf_f["N_gen"], float)
    Ts, Ys = (np.asarray(e, float) for _, e in inf_s["gen_axes"])
    Tf, Yf = (np.asarray(e, float) for _, e in inf_f["gen_axes"])
    print(f"\nshipped gen grid : qT {Ts.size-1} bins to {Ts[-1]:g}, "
          f"|Y| {Ys.size-1} bins to {Ys[-1]:g}   -> {N_s.size} bins")
    print(f"fine    gen grid : qT {Tf.size-1} bins to {Tf[-1]:g}, "
          f"|Y| {Yf.size-1} bins to {Yf[-1]:g}   -> {N_f.size} bins")
    print(f"reco             : " +
          ", ".join(f"{n}({len(e)-1}) [{e[0]:g},{e[-1]:g}]" for n, e in reco_s))

    # nesting: every shipped edge must be a fine edge (below the shipped top)
    for e in Ts[Ts <= Tf[-1] + 1e-9]:
        edge_index(Tf, e, "fine qT")
    for e in Ys:
        edge_index(Yf, e, "fine |Y|")
    print("nesting          : every shipped gen edge is a fine gen edge  OK")

    # ---- 2. the coarsening identity, as a control ---------------------------
    # R_raw = R * N_gen is additive, so summing the fine R_raw over the fine
    # bins inside a shipped bin must reproduce the shipped R_raw exactly, for
    # every shipped gen bin below the shipped grid's last (overflow) column.
    Rraw_s = R_s * N_s[None, None, :, :]
    Rraw_f = R_f * N_f[None, None, :, :]
    nT_s_in = Ts.size - 2  # drop the [44, 100] overflow column
    worst = 0.0
    for i in range(nT_s_in):
        i0, i1 = edge_index(Tf, Ts[i], "fine qT"), edge_index(Tf, Ts[i + 1], "fine qT")
        for j in range(Ys.size - 1):
            j0, j1 = edge_index(Yf, Ys[j], "f|Y|"), edge_index(Yf, Ys[j + 1], "f|Y|")
            a = Rraw_f[:, :, i0:i1, j0:j1].sum(axis=(2, 3))
            b = Rraw_s[:, :, i, j]
            den = np.maximum(np.abs(b), 1e-30)
            worst = max(worst, float(np.max(np.abs(a - b) / den)))
    print(f"coarsening ident.: max rel |fine summed - shipped| = {worst:.2e} "
          f"over {nT_s_in * (Ys.size - 1)} shipped gen bins x {R_s[..., 0, 0].size} reco bins")

    # ---- 3. the region, on both grids --------------------------------------
    is0, is1 = edge_index(Ts, qt_lo, "shipped qT"), edge_index(Ts, qt_hi, "shipped qT")
    js0, js1 = edge_index(Ys, y_lo, "shipped |Y|"), edge_index(Ys, y_hi, "shipped |Y|")
    if0, if1 = edge_index(Tf, qt_lo, "fine qT"), edge_index(Tf, qt_hi, "fine qT")
    jf0, jf1 = edge_index(Yf, y_lo, "fine |Y|"), edge_index(Yf, y_hi, "fine |Y|")
    Ts_r, Ys_r = Ts[is0:is1 + 1], Ys[js0:js1 + 1]
    Tf_r, Yf_r = Tf[if0:if1 + 1], Yf[jf0:jf1 + 1]
    n_s = (Ts_r.size - 1) * (Ys_r.size - 1)
    n_f = (Tf_r.size - 1) * (Yf_r.size - 1)
    print(f"\nregion gen bins  : shipped {Ts_r.size-1} x {Ys_r.size-1} = {n_s} "
          f"| fine {Tf_r.size-1} x {Yf_r.size-1} = {n_f}   "
          f"(refinement {n_f / n_s:.2f}x)")

    R_s_r = R_s[:, :, is0:is1, js0:js1].reshape(-1, n_s)
    R_f_r = R_f[:, :, if0:if1, jf0:jf1].reshape(-1, n_f)
    N_s_r = N_s[is0:is1, js0:js1].reshape(-1)
    N_f_r = N_f[if0:if1, jf0:jf1].reshape(-1)

    ref_s = R_s_r @ N_s_r
    ref_f = R_f_r @ N_f_r
    d_ref = np.max(np.abs(ref_f - ref_s) / np.maximum(np.abs(ref_s), 1e-300))
    print(f"reference identity: max rel |ref_fine - ref_shipped| = {d_ref:.3e} "
          f"-> the reference is the SAME object on both arms")
    ref = ref_s
    print(f"region reco yield : {ref.sum():.6g} "
          f"({ref.sum() / (R_s.reshape(-1, N_s.size) @ N_s.reshape(-1)).sum() * 100:.2f}% "
          f"of the card's whole reco yield)")

    # ---- 4. sigma_gen on both grids ----------------------------------------
    print("\nsigma_gen at the anchor:")
    sg_s_full, core_s, _ = sigma_gen_on(
        args.shipped_conf, args.shipped_cache,
        [("ptVGen", Ts), ("absYVGen", Ys)], 60.0, 120.0, args.threads, "shipped")
    sg_s = sg_s_full.reshape(Ts.size - 1, Ys.size - 1)[is0:is1, js0:js1].reshape(-1)
    sg_f, core_f, _ = sigma_gen_on(
        args.fine_conf, args.fine_cache,
        [("ptVGen", Tf_r), ("absYVGen", Yf_r)], 60.0, 120.0, args.threads, "fine")
    sg_f = np.asarray(sg_f, float).reshape(-1)

    # ARM SEPARATION.  values_and_jacobian memoises on the parameter vector
    # alone, so two arms that share one core would return the identical array.
    # These are two distinct ScetlibADXsec objects over two different bin sets;
    # prove it, and prove the region integrals agree only to the integration
    # tolerance rather than bitwise.
    assert core_s is not core_f
    assert core_s.bins.shape[0] != core_f.bins.shape[0]
    tot_s, tot_f = float(sg_s.sum()), float(sg_f.sum())
    print(f"\nARM SEPARATION: two ScetlibADXsec objects, "
          f"{core_s.bins.shape[0]} vs {core_f.bins.shape[0]} cache bins; "
          f"region sigma_gen {tot_s:.8g} vs {tot_f:.8g} pb, "
          f"rel diff {tot_f / tot_s - 1:+.3e}")

    # ---- 5. the production CorrZ prediction on both region grids ------------
    from validate_variations_reco import _gen_reference
    labels, cen, on_grid_s = _gen_reference(args.corrz, Ys_r, Ts_r)
    sr_s = on_grid_s(cen).T.reshape(-1)
    _, _, on_grid_f = _gen_reference(args.corrz, Yf_r, Tf_r)
    sr_f = on_grid_f(cen).T.reshape(-1)
    print(f"\nCorrZ central label '{cen}': region total "
          f"shipped grid {sr_s.sum():.8g}, fine grid {sr_f.sum():.8g}, "
          f"rel diff {sr_f.sum() / sr_s.sum() - 1:+.3e} (must be ~0: exact sum)")

    # ---- 6. the closure, both arms ----------------------------------------
    out = {}
    for tag, R_r, sg, sr, Ngr in (
        ("shipped", R_s_r, sg_s, sr_s, N_s_r),
        ("fine", R_f_r, sg_f, sr_f, N_f_r),
    ):
        mod = R_r @ sg
        fld = R_r @ sr
        print(f"\n=== {tag.upper()} grid, region reco closure (SHAPE) ===")
        wt, mt, rt, _ = shape_metrics(mod, ref, ref, "TOTAL  model / corrected MC")
        wc, mc, rc, _ = shape_metrics(mod, fld, ref, "CALC   model / (R (x) CorrZ)")
        wf, mf, rf, _ = shape_metrics(fld, ref, ref, "MC     (R (x) CorrZ) / MC")
        out[tag] = dict(mod=mod, fld=fld, r_tot=rt, r_calc=rc, r_mc=rf,
                        w_tot=wt, m_tot=mt, w_calc=wc, m_calc=mc, w_mc=wf, m_mc=mf)
        # gen-level, for the record
        shape_metrics(sg, sr, sr, "GEN    sigma_gen model / CorrZ")

    # ---- 7. before/after ---------------------------------------------------
    print("\n" + "=" * 78)
    print(" BEFORE / AFTER -- yield-weighted mean|dev| and max, same region")
    print("=" * 78)
    print(f" {'term':<8} {'shipped wmean':>14} {'fine wmean':>12} {'ratio':>8}   "
          f"{'shipped max':>12} {'fine max':>10} {'ratio':>8}")
    for k, lab in (("tot", "TOTAL"), ("calc", "CALC"), ("mc", "MC")):
        a, b = out["shipped"][f"w_{k}"], out["fine"][f"w_{k}"]
        c, d = out["shipped"][f"m_{k}"], out["fine"][f"m_{k}"]
        print(f" {lab:<8} {a:14.6f} {b:12.6f} {b / a:8.3f}   "
              f"{c:12.6f} {d:10.6f} {d / c:8.3f}")

    # the direct arm-to-arm difference of the central prediction
    ms, mf_ = out["shipped"]["mod"], out["fine"]["mod"]
    sc = ms.sum() / mf_.sum()
    dd = np.abs(mf_ * sc / ms - 1.0)
    print(f"\n fine/shipped central prediction, shape: wmean|dev| "
          f"{float(np.average(dd, weights=ref)):.6f}  max {dd.max():.6f}  "
          f"(total ratio {mf_.sum() / ms.sum():.6f})")

    # ---- 8. profile over reco ptll ----------------------------------------
    ptll_e = np.asarray(reco_s[0][1], float)
    nptll = ptll_e.size - 1
    sh = (nptll, args.reco_yll_bins)
    print(f"\n per reco ptll bin, yll summed with the reference weights:")
    print(f"   {'ptll bin':>13} {'yield frac':>10} | "
          f"{'TOT ship':>9} {'TOT fine':>9} | {'CALC ship':>10} {'CALC fine':>9} | "
          f"{'MC ship':>9} {'MC fine':>9}")
    W = ref.reshape(sh)
    rows = []
    for k in range(nptll):
        w = W[k]
        if w.sum() <= 0:
            continue
        vals = []
        for tag in ("shipped", "fine"):
            for key in ("r_tot", "r_calc", "r_mc"):
                r = out[tag][key].reshape(sh)[k]
                m = np.isfinite(r)
                vals.append(float(np.average(r[m], weights=w[m])) - 1.0 if m.any() else np.nan)
        print(f"   [{ptll_e[k]:5g},{ptll_e[k+1]:5g}] {w.sum()/ref.sum():10.4f} | "
              f"{vals[0]:+9.2e} {vals[3]:+9.2e} | {vals[1]:+10.2e} {vals[4]:+9.2e} | "
              f"{vals[2]:+9.2e} {vals[5]:+9.2e}")
        rows.append([ptll_e[k], ptll_e[k + 1], w.sum() / ref.sum()] + vals)

    if args.out:
        np.savez(args.out, ref=ref, ptll_edges=ptll_e,
                 yll_edges=np.asarray(reco_s[1][1], float),
                 profile=np.asarray(rows, float),
                 region=np.array([qt_lo, qt_hi, y_lo, y_hi]),
                 n_gen_shipped=n_s, n_gen_fine=n_f,
                 sg_shipped=sg_s, sg_fine=sg_f, sr_shipped=sr_s, sr_fine=sr_f,
                 Ts_r=Ts_r, Ys_r=Ys_r, Tf_r=Tf_r, Yf_r=Yf_r,
                 **{f"{t}_{k}": out[t][k] for t in out for k in
                    ("mod", "fld", "r_tot", "r_calc", "r_mc")})
        print(f"\n arrays -> {args.out}")


if __name__ == "__main__":
    main()
