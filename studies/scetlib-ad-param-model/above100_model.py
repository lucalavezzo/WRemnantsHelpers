#!/usr/bin/env python3
r"""What the model says above gen qT 100, and what including it does at reco level.

Two things this measures, and they must be kept apart:

MEASURED, on the CORRECTED region (gen qT < 100).  The in-situ reproducibility
floor of the extended cache against the unextended one over the 748 gen bins they
share, and the closure terms there.  Nothing above 100 enters.

PROVISIONAL, above gen qT 100.  No theory correction exists there yet (the CorrZ
flow bin is exactly 1.0, i.e. the MiNNLO templates are UNCORRECTED), so anything
computed there is model-versus-nothing.  What it is good for is a PREVIEW of the
correction Luca's production will produce: the model's own sigma_gen divided by
the MiNNLO gen yield, anchored to the true CorrZ ratio in the last corrected qT
row, gives the correction the same calculation would give above 100.  The
credibility of that extrapolation is measured where truth exists, by anchoring at
qT 44 and predicting 44 -> 100.

Usage:
  above100_model.py --histmaker <ext run> --ext-cache ... --ext-conf ... \
      [--ref-cache <qT 1-100 cache> --ref-conf ...] [--plot-dir ...]
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
SAMPLE = "Zmumu_2016PostVFP"


def sigma_gen_on(conf, cache, gen_axes, Q_lo, Q_hi, threads, label):
    from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

    core = ScetlibADXsec(conf, cache, threads=threads)
    fold = core.fold_for(gen_axes, Q_lo, Q_hi)
    vals, _ = core.values_and_jacobian(core.anchor.copy())
    sg = fold(np.asarray(vals, float))
    print(
        f"  [{label}] {os.path.basename(os.path.dirname(cache))}: "
        f"{core.bins.shape[0]} cache bins -> {sg.size} gen bins, "
        f"y_convention {fold.y_convention}, sum {sg.sum():.8f} pb"
    )
    return sg, core


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--histmaker", required=True)
    ap.add_argument("--ext-cache", required=True)
    ap.add_argument("--ext-conf", required=True)
    ap.add_argument("--ref-cache", default=None)
    ap.add_argument("--ref-conf", default=None)
    ap.add_argument("--corrz", default=CORRZ)
    ap.add_argument("--threads", type=int, default=48)
    ap.add_argument("--fit-ptll-bins", type=int, default=39)
    ap.add_argument("--fit-yll-bins", type=int, default=20)
    ap.add_argument("--qt-min", type=float, default=1.0)
    ap.add_argument("--plot-dir", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    import h5py
    from wums import ioutils as wums_io

    with h5py.File(args.histmaker, "r") as f:
        o = wums_io.pickle_load_h5py(f[SAMPLE])["output"]
        hr = o["nominal_prefsr_yieldsResponse"]
        hr = hr.get() if hasattr(hr, "get") else hr
        hg = o["prefsr_response"]
        hg = hg.get() if hasattr(hg, "get") else hg

    hp = hr[{"acceptance": True}].project("ptll", "yll", "ptVGen", "absYVGen")
    full = hp.values(flow=True)
    npt, ny = hp.axes["ptll"].size, hp.axes["yll"].size
    nq, nay = hp.axes["ptVGen"].size, hp.axes["absYVGen"].size
    yoff = 1 if hp.axes["yll"].traits.underflow else 0
    R_raw = np.asarray(full[0:npt, yoff : yoff + ny, 0:nq, 0:nay], float)
    qt = np.asarray(hp.axes["ptVGen"].edges, float)
    ay = np.asarray(hp.axes["absYVGen"].edges, float)
    ptl = np.asarray(hp.axes["ptll"].edges, float)
    gv = hg.values(flow=True)
    N_gen = np.asarray(gv[0:nq, 0:nay], float)

    i1 = int(np.argmin(np.abs(qt - args.qt_min)))
    i100 = int(np.argmin(np.abs(qt - 100.0)))
    assert abs(qt[i1] - args.qt_min) < 1e-9 and abs(qt[i100] - 100.0) < 1e-9
    qt_c = qt[i1:]                             # cache/fold grid
    gen_axes = [("ptVGen", qt_c), ("absYVGen", ay)]
    R_raw = R_raw[:, :, i1:, :]
    N_gen = N_gen[i1:, :]
    nqc = qt_c.size - 1
    print(f"gen grid used: qT {nqc} bins [{qt_c[0]:g}, {qt_c[-1]:g}] x "
          f"|Y| {nay} bins; {nqc * nay} gen bins "
          f"({i100 - i1} qT bins below 100, {nqc - (i100 - i1)} above)")

    # ---------------- sigma_gen -------------------------------------------
    print("\n=== sigma_gen ===")
    sg_ext, core_ext = sigma_gen_on(args.ext_conf, args.ext_cache, gen_axes,
                                    60.0, 120.0, args.threads, "extended")
    sg_ext = sg_ext.reshape(nqc, nay)
    n_below = i100 - i1

    if args.ref_cache:
        qt_ref = qt_c[: n_below + 1]
        sg_ref, core_ref = sigma_gen_on(
            args.ref_conf, args.ref_cache,
            [("ptVGen", qt_ref), ("absYVGen", ay)], 60.0, 120.0,
            args.threads, "reference (qT<100)")
        sg_ref = sg_ref.reshape(n_below, nay)
        # ARM SEPARATION: two objects, different cache bin counts, different sums
        print(f"  ARM SEPARATION: {core_ext.bins.shape[0]} vs "
              f"{core_ref.bins.shape[0]} cache bins; region sums "
              f"{sg_ext[:n_below].sum():.8f} vs {sg_ref.sum():.8f} pb  "
              f"(rel {sg_ext[:n_below].sum()/sg_ref.sum()-1:+.3e})")
        d = np.abs(sg_ext[:n_below] / sg_ref - 1.0).reshape(-1)
        w = N_gen[:n_below].reshape(-1)
        print("\n=== IN-SITU TWO-BUILD FLOOR (the 748 shared gen bins) ===")
        print(f"  median |dev| {np.median(d):.3e}   p95 {np.percentile(d,95):.3e}"
              f"   max {d.max():.3e}   N_gen-weighted "
              f"{np.average(d, weights=w):.3e}")

    # ---------------- the implied correction above 100 ---------------------
    from validate_variations_reco import _gen_reference

    qt_lo = qt_c[: n_below + 1]
    _, cen, on_grid = _gen_reference(args.corrz, ay, qt_lo)
    sr = on_grid(cen).T.reshape(n_below, nay)          # sigma_CorrZ, qT<100
    print(f"\nCorrZ central '{cen}': sum over qT<100 {sr.sum():.6g}")

    # the correction the templates applied, per gen cell: sigma_CorrZ / N_gen up
    # to one global scale.  Fixing that scale on a chosen anchor ROW makes it the
    # actual CorrZ ratio there, and the model's own sigma/N_gen extrapolates it.
    def implied(anchor_i, arr, n):
        """model-implied correction on rows [0, n), anchored per |Y| at row
        anchor_i to the true CorrZ ratio."""
        c = arr / np.where(N_gen[:n] > 0, N_gen[:n], np.nan)
        t = sr / np.where(N_gen[:n_below] > 0, N_gen[:n_below], np.nan)
        k = t[anchor_i] / c[anchor_i]                  # per |Y|
        return c * k[None, :], t

    # credibility: anchor at qT 44 and predict 44 -> 100 where truth exists
    i44 = int(np.argmin(np.abs(qt_c - 44.0)))
    imp, true = implied(i44, sg_ext[:n_below], n_below)
    rel = imp[i44:] / true[i44:] - 1.0
    print("\n=== CREDIBILITY OF THE EXTRAPOLATION (anchored at qT 44, "
          "predicting 44 -> 100, where truth exists) ===")
    print(f"  |implied/true - 1| over gen qT [44, 100] x |Y|<2.5: "
          f"median {np.nanmedian(np.abs(rel)):.4f}  p95 "
          f"{np.nanpercentile(np.abs(rel),95):.4f}  max "
          f"{np.nanmax(np.abs(rel)):.4f}")
    for k in range(i44, n_below):
        w = N_gen[k]
        print(f"   qT [{qt_c[k]:6.1f},{qt_c[k+1]:6.1f}]  true "
              f"{np.average(true[k], weights=w):.4f}  implied "
              f"{np.average(imp[k], weights=w):.4f}  "
              f"rel {np.average(imp[k]/true[k]-1, weights=w):+.4f}")

    # the actual preview: anchor at the LAST corrected row [90, 100]
    ia = n_below - 1
    c_all = sg_ext / np.where(N_gen > 0, N_gen, np.nan)
    t_all = sr / np.where(N_gen[:n_below] > 0, N_gen[:n_below], np.nan)
    k = t_all[ia] / c_all[ia]
    imp_all = c_all * k[None, :]
    print(f"\n=== PREVIEW: the correction above 100, anchored at qT "
          f"[{qt_c[ia]:g}, {qt_c[ia+1]:g}] (PROVISIONAL -- no truth exists) ===")
    print(f"  {'gen qT bin':>18} {'N_gen frac':>11} {'implied corr':>13} "
          f"{'/anchor':>9}")
    Ntot = N_gen.sum()
    a_val = np.average(imp_all[ia], weights=N_gen[ia])
    for kk in range(n_below, nqc):
        w = N_gen[kk]
        if w.sum() <= 0:
            print(f"  [{qt_c[kk]:7.1f},{qt_c[kk+1]:7.1f}]  EMPTY (N_gen = 0)")
            continue
        v = np.average(imp_all[kk], weights=w)
        print(f"  [{qt_c[kk]:7.1f},{qt_c[kk+1]:7.1f}] {w.sum()/Ntot:11.4e} "
              f"{v:13.4f} {v/a_val:9.4f}")
    print(f"  anchor row [{qt_c[ia]:g},{qt_c[ia+1]:g}] true CorrZ ratio "
          f"{np.average(t_all[ia], weights=N_gen[ia]):.4f}")

    # ---------------- reco-level effect of the extra columns ---------------
    R = R_raw / np.where(N_gen > 0, N_gen, 1.0)[None, None, :, :]
    R = R[: args.fit_ptll_bins, : args.fit_yll_bins]
    Rf = R.reshape(args.fit_ptll_bins * args.fit_yll_bins, nqc * nay)
    sg_flat = sg_ext.reshape(-1)
    mask = np.zeros((nqc, nay), bool)
    mask[:n_below] = True
    lo = Rf @ (sg_flat * mask.reshape(-1))
    all_ = Rf @ sg_flat
    d = np.where(lo > 0, all_ / np.where(lo > 0, lo, 1) - 1.0, 0.0)
    print("\n=== RECO-LEVEL EFFECT of including the above-100 gen columns ===")
    print(f"  (fit reco bins: ptll < {ptl[args.fit_ptll_bins]:g}, "
          f"{args.fit_ptll_bins}x{args.fit_yll_bins} = {d.size})")
    print(f"  total prediction changes by {all_.sum()/lo.sum()-1:+.4e}")
    print(f"  per-bin: max {np.abs(d).max():.4e}  median {np.median(d):.4e}  "
          f"nonzero {int((d != 0).sum())}/{d.size}")
    dm = d.reshape(args.fit_ptll_bins, args.fit_yll_bins)
    for kk in range(args.fit_ptll_bins):
        if np.abs(dm[kk]).max() > 0:
            print(f"    ptll [{ptl[kk]:6.1f},{ptl[kk+1]:6.1f}]  max "
                  f"{np.abs(dm[kk]).max():.3e}")
    # and the reco bin the fit does NOT use
    if npt > args.fit_ptll_bins:
        Rh = (R_raw / np.where(N_gen > 0, N_gen, 1.0)[None, None, :, :])[
            args.fit_ptll_bins :, : args.fit_yll_bins
        ]
        nh = Rh.shape[0]
        Rhf = Rh.reshape(nh * args.fit_yll_bins, nqc * nay)
        lo_h = Rhf @ (sg_flat * mask.reshape(-1))
        all_h = Rhf @ sg_flat
        print(f"  reco ptll [{ptl[args.fit_ptll_bins]:g}, "
              f"{ptl[-1]:g}] (NOT in the fit): "
              f"{all_h.sum()/lo_h.sum()-1:+.4e}")

    if args.out:
        np.savez(args.out, qt=qt_c, ay=ay, sg_ext=sg_ext, N_gen=N_gen, sr=sr,
                 imp_all=imp_all, t_all=t_all, n_below=n_below, d_reco=d)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
