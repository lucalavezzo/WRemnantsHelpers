#!/usr/bin/env python3
r"""Gen-binning granularity of the CENTRAL reco prediction -- WITHOUT a cache.

The cache-based measurement (``central_finegrid.py``) needs sigma_gen on the fine
gen grid and so is limited to the region a cache was built for. This one is not
limited at all, because it replaces the model's sigma_gen by the PRODUCTION CorrZ
spectrum -- which the model reproduces to 0.075 % at gen level -- and so needs no
SCETlib, no cache and no build:

    CEN_GRAIN(b) = [ sum_g   R_raw(b,g) sigma(g) / N_gen(g) ]
                 / [ sum_G   R_raw(b,G) sigma(G) / N_gen(G) ]

with g the FINE gen bins (the correction's own grid) and G the SHIPPED ones. The
denominators of the two folds are identical by additivity of R_raw, so this ratio
is exactly the granularity of the central prediction: how much the reco
prediction moves when sigma is resolved inside a shipped gen cell instead of
being spread there in proportion to N_gen.

It is the central analogue of ``grain_finegrid.py``'s GRAIN for the variations,
and it bounds what the cache-based arm-to-arm number can possibly be: any
difference beyond this is the two builds' own reproducibility, not binning.
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

from central_finegrid import (  # noqa: E402
    HISTMAKER, CORRZ, RECO, SAMPLE, crop_reco, edge_index, load_grid,
)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--histmaker", default=HISTMAKER)
    ap.add_argument("--corrz", default=CORRZ)
    ap.add_argument("--reco-ptll-bins", type=int, default=39)
    ap.add_argument("--reco-yll-bins", type=int, default=20)
    ap.add_argument("--plot-dir", default=None)
    args = ap.parse_args()

    inf_s = load_grid(args.histmaker, fine=False)
    inf_f = load_grid(args.histmaker, fine=True)
    n_keep = (args.reco_ptll_bins, args.reco_yll_bins)
    Rraw_s, reco_s = crop_reco(inf_s["R"], inf_s["reco_axes"], n_keep)
    Rraw_f, _ = crop_reco(inf_f["R"], inf_f["reco_axes"], n_keep)
    N_s = np.asarray(inf_s["N_gen"], float)
    N_f = np.asarray(inf_f["N_gen"], float)
    Ts, Ys = (np.asarray(e, float) for _, e in inf_s["gen_axes"])
    Tf, Yf = (np.asarray(e, float) for _, e in inf_f["gen_axes"])
    ptll_e = np.asarray(reco_s[0][1], float)
    nptll = ptll_e.size - 1

    from validate_variations_reco import _gen_reference

    def sigma_on(Ye, Te):
        labels, cen, on_grid = _gen_reference(args.corrz, Ye, Te)
        return on_grid(cen).T  # (nT, nY)

    sig_s = sigma_on(Ys, Ts)
    sig_f = sigma_on(Yf, Tf)
    print(f"CorrZ total on the two grids: {sig_s.sum():.10g} vs {sig_f.sum():.10g} "
          f"(rel {sig_f.sum()/sig_s.sum()-1:+.1e})")

    keep = {}
    for qt_lo, qt_hi, lab in ((0.0, 44.0, "gen qT [0, 44]   (no overflow column)"),
                              (1.0, 44.0, "gen qT [1, 44]   (the headline region)"),
                              (0.0, 1.0, "gen qT [0, 1]    (the convention cell)"),
                              (0.0, 100.0, "gen qT [0, 100]  (incl. the shipped OVERFLOW)")):
        is0 = edge_index(Ts, qt_lo, "s qT"); is1 = edge_index(Ts, qt_hi, "s qT")
        if0 = edge_index(Tf, qt_lo, "f qT"); if1 = edge_index(Tf, qt_hi, "f qT")
        ns = (is1 - is0) * (Ys.size - 1)
        nf = (if1 - if0) * (Yf.size - 1)
        Rs = Rraw_s[:, :, is0:is1, :].reshape(-1, ns)
        Rf = Rraw_f[:, :, if0:if1, :].reshape(-1, nf)
        ws = (sig_s[is0:is1, :] / N_s[is0:is1, :]).reshape(-1)
        wf = (sig_f[if0:if1, :] / N_f[if0:if1, :]).reshape(-1)
        a = Rf @ wf
        b = Rs @ ws
        ref = Rs.sum(axis=1)
        good = (b > 0) & (ref > 0)
        r = np.full(a.shape, np.nan)
        r[good] = a[good] / b[good]
        sc = float(np.average(r[good], weights=ref[good]))
        d = np.abs(r[good] / sc - 1.0)
        wm = float(np.average(d, weights=ref[good]))
        print(f"\n{lab}   shipped {ns} gen bins -> fine {nf}")
        print(f"   total fine/shipped - 1  = {a[good].sum()/b[good].sum()-1:+.3e}")
        print(f"   SHAPE: yield-weighted mean|dev| {wm:.3e}   max {d.max():.3e}   "
              f"p95 {np.percentile(d, 95):.3e}")
        yfrac = ref[good].sum() / Rraw_s.reshape(-1, N_s.size).sum(axis=1)[good].sum()
        print(f"   region carries {yfrac:.4f} of the card's reco yield")
        keep[(qt_lo, qt_hi)] = (r / sc, ref, ns, nf, wm, float(d.max()))
        if qt_lo == 1.0:
            prof = np.full(nptll, np.nan)
            R2 = r.reshape(nptll, -1) / sc
            W2 = ref.reshape(nptll, -1)
            for k in range(nptll):
                m = np.isfinite(R2[k]) & (W2[k] > 0)
                if m.any():
                    prof[k] = float(np.average(R2[k][m], weights=W2[k][m])) - 1.0
            print("   per reco ptll bin (yll summed, reference-weighted):")
            for k in range(nptll):
                print(f"     [{ptll_e[k]:5g},{ptll_e[k+1]:5g}] {prof[k]:+.2e}")

    if args.plot_dir:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from wremnants.postprocessing.scetlib_np import plot_output

        yll_e = np.asarray(reco_s[1][1], float)
        r1, ref1, ns1, nf1, wm1, mx1 = keep[(1.0, 44.0)]
        rA, refA, nsA, nfA, wmA, mxA = keep[(0.0, 100.0)]
        meta = {
            "histmaker": args.histmaker,
            "correction": args.corrz,
            "method": "sigma_CorrZ folded through R_raw/N_gen on the two gen "
                      "grids; the two folds share the same denominator by "
                      "additivity of R_raw, so the ratio IS the central "
                      "prediction's gen granularity. No cache, no SCETlib.",
            "qT [1,44]  wmean / max": f"{wm1:.3e} / {mx1:.3e}",
            "qT [0,100] wmean / max": f"{wmA:.3e} / {mxA:.3e}",
            "for scale, the published central closure": "1.28e-03 (shape)",
        }
        fig, axs = plt.subplots(2, 1, figsize=(8.4, 6.4), sharex=True,
                                gridspec_kw=dict(height_ratios=[1, 1]))
        ax = axs[0]
        profs = {}
        for (rr, rw), col, lab in (
            ((r1, ref1), "#e42536", f"gen qT [1, 44]: {ns1} -> {nf1} gen bins"),
            ((rA, refA), "#5790fc", f"gen qT [0, 100]: {nsA} -> {nfA} (incl. the "
                                    "shipped overflow)"),
        ):
            R2 = np.asarray(rr).reshape(nptll, -1)
            W2 = np.asarray(rw).reshape(nptll, -1)
            prof = np.full(nptll, np.nan)
            for k in range(nptll):
                m = np.isfinite(R2[k]) & (W2[k] > 0)
                if m.any():
                    prof[k] = float(np.average(R2[k][m], weights=W2[k][m])) - 1.0
            ax.stairs(prof * 100, ptll_e, color=col, lw=2, label=lab)
            profs[lab] = (prof, col)
        ax.axhspan(-0.128, 0.128, color="0.85", zorder=0,
                   label="published central closure, $\\pm$0.128 %")
        ax.axhline(0, color="k", lw=0.8)
        ax.set_ylabel("fine / shipped $-$ 1  [%]", fontsize=11)
        ax.set_title("gen granularity of the CENTRAL reco prediction "
                     "(cache-free, $\\sigma_{CorrZ}$ folded two ways)", fontsize=10)
        ax.legend(fontsize=9, loc="upper left")
        ax.grid(alpha=0.3)
        for lab, (prof, col) in profs.items():
            if lab.startswith("gen qT [1, 44]"):
                axs[1].stairs(prof * 100, ptll_e, color=col, lw=2, label=lab)
        axs[1].axhline(0, color="k", lw=0.8)
        axs[1].set_ylim(-0.05, 0.05)
        axs[1].set_ylabel("same, zoomed  [%]", fontsize=11)
        axs[1].set_xlabel(r"reco $p_{T}^{\ell\ell}$ [GeV]")
        axs[1].grid(alpha=0.3)
        axs[1].legend(fontsize=9, loc="upper left")
        fig.tight_layout()
        plot_output.save_plot(args.plot_dir, "central_grain_nocache_ptll",
                             fig=fig, args=args, meta_info=meta, dpi=140)

        fig, ax = plt.subplots(figsize=(7.8, 4.8))
        m2 = (np.asarray(r1).reshape(nptll, -1) - 1.0) * 100
        v = float(np.nanpercentile(np.abs(m2), 99))
        pc = ax.pcolormesh(ptll_e, yll_e, m2.T, cmap="RdBu_r", vmin=-v, vmax=v,
                           shading="flat")
        fig.colorbar(pc, ax=ax, label="fine / shipped $-$ 1  [%]")
        ax.set_xlabel(r"reco $p_{T}^{\ell\ell}$ [GeV]")
        ax.set_ylabel(r"reco $y^{\ell\ell}$")
        ax.set_title("central prediction: CorrZ gen grid vs shipped, "
                     "gen qT [1, 44] (cache-free)", fontsize=10)
        fig.tight_layout()
        plot_output.save_plot(args.plot_dir, "central_grain_nocache_map",
                             fig=fig, args=args, meta_info=meta, dpi=140)
        print(f"\n plots -> {args.plot_dir}")


if __name__ == "__main__":
    main()
