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
def _hist1d(edges, vals, name):
    import hist as _h
    o = _h.Hist(_h.axis.Variable(np.asarray(edges, float), name=name,
                                 underflow=False, overflow=False),
                storage=_h.storage.Double())
    o.view(flow=False)[...] = np.asarray(vals, float)
    return o


def make_plots(args, out, ref, reco_axes, sh, gen_s, gen_f,
               qt_lo, qt_hi, y_lo, y_hi, n_s, n_f, d_ref):
    """Three figures: the central ratio on both grids (reco ptll and yll), the
    arm-to-arm 2D map, and the gen-level CALC on both grids."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from wums import plot_tools
    from wremnants.postprocessing.scetlib_np import plot_output

    os.makedirs(args.plot_dir, exist_ok=True)
    meta = {
        "histmaker": args.histmaker,
        "gen region": f"qT [{qt_lo:g}, {qt_hi:g}] x |Y| [{y_lo:g}, {y_hi:g}]",
        "gen bins": f"shipped {n_s}, fine {n_f}",
        "fine cache": args.fine_cache,
        "shipped cache": args.shipped_cache,
        "reference identity max rel dev": f"{d_ref:.3e}",
        "reference": "sum_g R_raw(b,g) over the region = corrected-MC reco yield "
                     "fed by that gen region; identical on both arms",
        "TOTAL shipped / fine (wmean)":
            f"{out['shipped']['w_tot']:.6f} / {out['fine']['w_tot']:.6f}",
    }
    ptll_e = np.asarray(reco_axes[0][1], float)
    yll_e = np.asarray(reco_axes[1][1], float)

    # --- the central ratio, on each reco axis
    for ax_i, (edges, axname, xlabel) in enumerate((
        (ptll_e, "ptll", r"reco $p_{T}^{\ell\ell}$ [GeV]"),
        (yll_e, "yll", r"reco $y^{\ell\ell}$"),
    )):
        other = 1 - ax_i
        r = ref.reshape(sh).sum(axis=other)
        hs = [_hist1d(edges, r, axname)]
        labels = ["corrected MC (region-restricted)"]
        for tag, lab in (("shipped", "model, shipped gen grid ($21\\times10$)"),
                         ("fine", "model, CorrZ gen grid ($70\\times11$)")):
            m = out[tag]["mod"].reshape(sh).sum(axis=other)
            m = m * (r.sum() / m.sum())          # one global scale: SHAPE
            hs.append(_hist1d(edges, m, axname))
            labels.append(lab)
        dev = max(
            float(np.max(np.abs(h.values(flow=False) / np.where(r > 0, r, np.nan) - 1)))
            for h in hs[1:]
        )
        pad = max(1.4 * dev, 5e-4)
        ymax = max(float(np.max(h.values(flow=False) / np.diff(edges))) for h in hs)
        fig = plot_tools.makePlotWithRatioToRef(
            hs, labels=labels,
            colors=["#5790fc", "#e42536", "#964a8b"],
            linestyles=["solid", "dashed", "dotted"],
            xlabel=xlabel, ylabel="yield / bin",
            rlabel=["model / MC"], rrange=[[1 - pad, 1 + pad]],
            binwnorm=1, logy=(axname == "ptll"), yerr=False, nlegcols=1,
            ylim=(None, ymax * (12 if axname == "ptll" else 1.9)),
            ratio_legend=False, legtext_size=15, width_scale=1.15,
            cms_label="Work in progress", grid=True,
        )
        plot_output.save_plot(args.plot_dir, f"central_{axname}_{args.tag}",
                              fig=fig, args=args, meta_info=meta, dpi=140)

    # --- arm-to-arm difference, 2D
    ms = out["shipped"]["mod"]
    mf = out["fine"]["mod"]
    d = (mf * (ms.sum() / mf.sum()) / np.where(ms > 0, ms, np.nan) - 1.0).reshape(sh)
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    v = float(np.nanmax(np.abs(d)) * 100)
    pc = ax.pcolormesh(ptll_e, yll_e, (d * 100).T, cmap="RdBu_r",
                       vmin=-v, vmax=v, shading="flat")
    fig.colorbar(pc, ax=ax, label="fine / shipped $-$ 1  [%]")
    ax.set_xlabel(r"reco $p_{T}^{\ell\ell}$ [GeV]")
    ax.set_ylabel(r"reco $y^{\ell\ell}$")
    ax.set_title("central prediction: CorrZ gen grid vs shipped, shape-matched\n"
                 f"gen region qT [{qt_lo:g}, {qt_hi:g}], |Y| [{y_lo:g}, {y_hi:g}]",
                 fontsize=10)
    fig.tight_layout()
    plot_output.save_plot(args.plot_dir, f"central_armdiff_map_{args.tag}",
                          fig=fig, args=args, meta_info=meta, dpi=140)

    # --- gen level: model / CorrZ per gen qT bin, both grids
    (sg_s, sr_s, Ts_r, Ys_r) = gen_s
    (sg_f, sr_f, Tf_r, Yf_r) = gen_f
    fig, axs = plt.subplots(2, 1, figsize=(8.4, 6.2), sharex=True,
                            gridspec_kw=dict(height_ratios=[2, 1]))
    for (sg, sr, Te, Ye), col, lab in (
        (gen_s, "#e42536", f"shipped ({Ts_r.size-1} qT bins)"),
        (gen_f, "#964a8b", f"CorrZ ({Tf_r.size-1} qT bins)"),
    ):
        a = np.asarray(sg, float).reshape(Te.size - 1, Ye.size - 1).sum(axis=1)
        b = np.asarray(sr, float).reshape(Te.size - 1, Ye.size - 1).sum(axis=1)
        w = np.diff(Te)
        axs[0].stairs(a / w, Te, color=col, lw=2, label=lab)
        axs[1].stairs(100 * (a / b * (b.sum() / a.sum()) - 1), Te, color=col, lw=2,
                      label=lab)
    axs[0].set_yscale("log")
    axs[0].set_ylabel(r"$d\sigma/dq_{T}$ [pb/GeV]", fontsize=11)
    axs[0].legend(fontsize=9)
    axs[0].grid(alpha=0.3)
    axs[1].axhline(0, color="k", lw=0.8)
    axs[1].set_ylabel("model/CorrZ $-$1 [%]", fontsize=11)
    axs[1].set_xlabel(r"gen $q_{T}$ [GeV]")
    axs[1].grid(alpha=0.3)
    axs[0].set_title("gen-level CALC on the two grids (shape-matched over the region)",
                     fontsize=10)
    fig.tight_layout()
    plot_output.save_plot(args.plot_dir, f"gen_calc_qt_{args.tag}",
                          fig=fig, args=args, meta_info=meta, dpi=140)
    print(f"\n plots -> {args.plot_dir}")


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--histmaker", default=HISTMAKER)
    ap.add_argument("--corrz", default=CORRZ)
    ap.add_argument("--fine-cache")
    ap.add_argument("--fine-conf")
    ap.add_argument("--shipped-cache")
    ap.add_argument("--shipped-conf")
    ap.add_argument("--skip-model", action="store_true",
                    help="stop after the grids / nesting / reference identity")
    ap.add_argument("--qt", nargs=2, type=float, required=True,
                    help="gen qT region [lo, hi], both edges of BOTH grids")
    ap.add_argument("--absy", nargs=2, type=float, required=True)
    ap.add_argument("--reco-ptll-bins", type=int, default=39,
                    help="reco ptll bins the card carries (edges 0..44)")
    ap.add_argument("--reco-yll-bins", type=int, default=20)
    ap.add_argument("--threads", type=int, default=64)
    ap.add_argument("--out", default=None, help="npz to dump the arrays into")
    ap.add_argument("--plot-dir", default=None)
    ap.add_argument("--tag", default="region")
    ap.add_argument("--nominal-ref", action="store_true",
                    help="ALSO compare against the histmaker's own reco "
                         "'nominal' (the published TOTAL definition) and report "
                         "the fiducial leak of the region reference against it")
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
    # load_R returns the RAW reco x gen yield; the model divides by N_gen
    # (param_model._setup_binning), so do the same here.
    Rraw_s, reco_s = crop_reco(inf_s["R"], inf_s["reco_axes"], n_keep)
    Rraw_f, reco_f = crop_reco(inf_f["R"], inf_f["reco_axes"], n_keep)
    N_s = np.asarray(inf_s["N_gen"], float)
    N_f = np.asarray(inf_f["N_gen"], float)
    R_s = Rraw_s / np.where(N_s > 0, N_s, 1.0)[None, None, :, :]
    R_f = Rraw_f / np.where(N_f > 0, N_f, 1.0)[None, None, :, :]
    print(f"empty gen bins   : shipped {int((N_s <= 0).sum())} of {N_s.size}, "
          f"fine {int((N_f <= 0).sum())} of {N_f.size}")
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

    if args.skip_model:
        return

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

    # ---- 4b. THE FLOOR.  Coarsening the fine sigma_gen onto the shipped
    # region grid must reproduce the shipped cache's own sigma_gen: both are the
    # same integral over the same cell, computed by two independent builds. The
    # spread of that comparison is the combined integration-tolerance and
    # build-reproducibility floor, and it bounds how much of any arm-to-arm reco
    # difference below can be real granularity rather than build noise.
    sg_f2 = sg_f.reshape(Tf_r.size - 1, Yf_r.size - 1)
    sg_s2 = sg_s.reshape(Ts_r.size - 1, Ys_r.size - 1)
    coarse = np.zeros_like(sg_s2)
    for i in range(Ts_r.size - 1):
        i0 = edge_index(Tf_r, Ts_r[i], "fT"); i1 = edge_index(Tf_r, Ts_r[i + 1], "fT")
        for j in range(Ys_r.size - 1):
            j0 = edge_index(Yf_r, Ys_r[j], "fY"); j1 = edge_index(Yf_r, Ys_r[j + 1], "fY")
            coarse[i, j] = sg_f2[i0:i1, j0:j1].sum()
    d = coarse / sg_s2 - 1.0
    print(f"\nFLOOR (fine sigma_gen coarsened onto the shipped region grid vs the "
          f"shipped cache):\n  {d.size} shipped gen bins: median |dev| "
          f"{np.median(np.abs(d)):.3e}, p95 {np.percentile(np.abs(d), 95):.3e}, "
          f"max {np.abs(d).max():.3e}\n  yield-weighted (by N_gen) "
          f"{float(np.average(np.abs(d), weights=N_s_r.reshape(sg_s2.shape))):.3e}"
          f"   [the published two-build floor in sigma is 3.1e-05]")

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

    # ---- 6b. the published reference, for continuity ------------------------
    if args.nominal_ref:
        import h5py
        from wums import ioutils as wums_io
        with h5py.File(args.histmaker, "r") as f:
            o = wums_io.pickle_load_h5py(f[SAMPLE])["output"]["nominal"]
            hn = o.get() if hasattr(o, "get") else o
        nom = hn.project(*RECO).values(flow=False).astype(float)
        nom = nom[: args.reco_ptll_bins, : args.reco_yll_bins].reshape(-1)
        leak = ref.sum() / nom.sum() - 1.0
        print(f"\n=== against the histmaker's own reco 'nominal' "
              f"(the PUBLISHED reference) ===")
        print(f"  region reference / nominal - 1, total: {leak:+.3e}  "
              f"(gen bins outside the region + the fiducial leak)")
        for tag in ("shipped", "fine"):
            shape_metrics(out[tag]["mod"], nom, nom,
                          f"TOTAL[{tag}] model / histmaker nominal")

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

    # ---- 9. plots ----------------------------------------------------------
    if args.plot_dir:
        make_plots(args, out, ref, reco_s, sh,
                   (sg_s, sr_s, Ts_r, Ys_r), (sg_f, sr_f, Tf_r, Yf_r),
                   qt_lo, qt_hi, y_lo, y_hi, n_s, n_f, d_ref)

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
