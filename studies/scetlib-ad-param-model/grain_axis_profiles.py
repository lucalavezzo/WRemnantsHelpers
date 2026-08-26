#!/usr/bin/env python3
r"""Where the granularity term sits in reco (ptll, yll), grid by grid.

The scalar summaries say how big GRAIN is; this says WHERE, which is what tells
you which gen axis to spend on. Two panels per figure, the |Y|-integrated ptll
profile and the ptll-integrated yll profile, with one curve per gen grid.

Run after the dedicated histmakers (see finegen_histmaker.py). Bare matplotlib:
these are profiles of a derived residual, not histograms.
"""

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants"),
           os.path.join(os.environ.get("WREM_BASE",
                                       "/home/submit/lavezzo/alphaS/WRemnants"),
                        "scripts", "rabbit", "scetlib_ad"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import grain_finegrid as GF  # noqa: E402
from grain_vs_grid import merge_matrix  # noqa: E402

COLORS = {"card 21x10": "#e42536", "reco-grid 40x10": "#2ca02c",
          "corr-grid 58x11": "#964a8b", "corr-grid qT only": "#f89c20",
          "corr-grid |Y| only": "#5790fc"}


def profiles(hm, grids, corr=(GF.CORR_MAIN, GF.CORR_AS), pick=None):
    """{grid label: {direction: (ptll profile, yll profile)}} of signed GRAIN."""
    import validate_variations as VV

    D = GF.load_fine(hm, list(corr))
    Te, Ye, R = D["Te"], D["Ye"], D["R"]
    npt, nyl, nT, nY = R.shape
    i44 = int(np.argmin(np.abs(Te - 44.0)))
    Rf = R.reshape(npt * nyl, nT * nY)
    den = Rf.sum(axis=1)
    nat = GF.native_corr()

    refs = {}
    for hn in corr:
        v, labels = D["var"][hn]
        cen = VV.central_label(labels)
        c = v[..., labels.index(cen)].reshape(-1)
        for L in labels:
            if L == cen or VV.variation_for(L) is None:
                continue
            if pick and L not in pick:
                continue
            with np.errstate(divide="ignore", invalid="ignore"):
                refs[L] = (np.where(c > 0,
                                    v[..., labels.index(L)].reshape(-1) / c,
                                    np.nan), c)

    def native_for(L):
        for _p, (lab, ce, val, Yn, Tn) in nat.items():
            if L in lab:
                return val[:, :, lab.index(L)], val[:, :, lab.index(ce)], Yn, Tn
        return None, None, None, None

    out = {}
    for label, (qe, ye) in grids.items():
        try:
            M_R, M_rho = GF.qt_merges(Te, np.asarray(qe, float),
                                      np.asarray(Te, float), i44, nT)
            MY = merge_matrix(Ye, np.asarray(ye, float), "absY")
        except SystemExit as exc:
            print(f"  {label}: {exc}")
            continue
        Rc = Rf @ np.kron(M_R, MY).T
        out[label] = {}
        for L, (rr, w) in refs.items():
            num, den_, Yn, Tn = native_for(L)
            if num is None:
                continue
            try:
                MYn = merge_matrix(Yn, np.asarray(ye, float), "absY native")
                _, M_rho = GF.qt_merges(Te, np.asarray(qe, float), Tn, i44,
                                        nT)
            except SystemExit as exc:
                print(f"  {label}/{L}: {exc}")
                break
            n_c = MYn @ num @ M_rho.T
            d_c = MYn @ den_ @ M_rho.T
            with np.errstate(divide="ignore", invalid="ignore"):
                rho = np.where(d_c != 0, n_c / d_c, 1.0).T.reshape(-1)
            d2 = ((Rc @ rho) / den / rr - 1.0).reshape(npt, nyl)
            w2 = np.nan_to_num(w).reshape(npt, nyl)
            out[label][L] = (np.nansum(np.abs(d2) * w2, axis=1) / w2.sum(axis=1),
                             np.nansum(np.abs(d2) * w2, axis=0) / w2.sum(axis=0))
    return out, D["pt"], D["yl"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reco-hm", required=True)
    ap.add_argument("--corr-hm", default=None)
    ap.add_argument("-o", "--out-dir", required=True)
    ap.add_argument("--direction", default="pdfCT18ZNNLO_as_0120")
    args = ap.parse_args()

    CORR_Y = [0, .15, .3, .5, .7, .9, 1.1, 1.3, 1.5, 1.8, 2.0, 2.5]
    res, pt, yl = {}, None, None

    import h5py  # noqa: F401  (import cost paid once, keeps the message clear)
    from wums import ioutils  # noqa: F401

    # the reco-grid run: card vs its own fine qT, both at the card's |Y|
    D = GF.load_fine(args.reco_hm, [GF.CORR_MAIN, GF.CORR_AS])
    fineq = list(np.asarray(D["Te"], float)[
        : int(np.argmin(np.abs(D["Te"] - 44.0))) + 1])
    g1, pt, yl = profiles(args.reco_hm,
                          {"card 21x10": (GF.CARD_QT, GF.CARD_Y),
                           "reco-grid 40x10": (fineq, GF.CARD_Y)})
    res.update(g1)

    if args.corr_hm:
        Dc = GF.load_fine(args.corr_hm, [GF.CORR_MAIN, GF.CORR_AS])
        i44 = int(np.argmin(np.abs(Dc["Te"] - 44.0)))
        cq = list(np.asarray(Dc["Te"], float)[: i44 + 1])
        g2, _, _ = profiles(args.corr_hm,
                            {"corr-grid 58x11": (cq, CORR_Y),
                             "corr-grid qT only": (cq, GF.CARD_Y),
                             "corr-grid |Y| only": (GF.CARD_QT, CORR_Y)})
        res.update(g2)

    os.makedirs(args.out_dir, exist_ok=True)
    for tag, D_ in (("median", None), (args.direction, args.direction)):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 4.6))
        for label, per in res.items():
            if not per:
                continue
            if D_ is None:
                P = np.median(np.array([v[0] for v in per.values()]), axis=0)
                Y = np.median(np.array([v[1] for v in per.values()]), axis=0)
            else:
                if D_ not in per:
                    continue
                P, Y = per[D_]
            c = COLORS.get(label, "k")
            a1.step(np.arange(P.size + 1), np.append(P, P[-1]) * 1e4,
                    where="post", color=c, lw=1.7, label=label)
            a2.step(np.arange(Y.size + 1), np.append(Y, Y[-1]) * 1e4,
                    where="post", color=c, lw=1.7, label=label)
        a1.set_xticks(np.arange(0, len(pt), 4))
        a1.set_xticklabels([f"{pt[i]:g}" for i in range(0, len(pt), 4)], fontsize=8)
        a1.set_xlabel(r"$p_T^{\ell\ell}$ [GeV]")
        a2.set_xticks(np.arange(0, len(yl), 2))
        a2.set_xticklabels([f"{yl[i]:g}" for i in range(0, len(yl), 2)], fontsize=8)
        a2.set_xlabel(r"$y^{\ell\ell}$")
        for a in (a1, a2):
            a.set_ylabel(r"$|$GRAIN$|$, yield-weighted $[\times 10^{4}]$")
            a.grid(alpha=0.3); a.legend(fontsize=8); a.set_yscale("log")
        ttl = ("median over the 39 directions" if D_ is None else D_)
        fig.suptitle(f"Where the granularity term sits: {ttl}", fontsize=11)
        fig.tight_layout()
        name = "grain_axis_profile_" + ("median" if D_ is None else "alphas")
        fig.savefig(os.path.join(args.out_dir, name + ".png"), dpi=150,
                    bbox_inches="tight")
        fig.savefig(os.path.join(args.out_dir, name + ".pdf"),
                    bbox_inches="tight")
        plt.close(fig)
        try:
            from wums import output_tools
            output_tools.write_index_and_log(
                args.out_dir, name,
                analysis_meta_info={"reco-grid histmaker": args.reco_hm,
                                    "corr-grid histmaker": str(args.corr_hm)},
                args=None)
        except Exception as exc:
            print(f"   [warn] {exc}")
    print(f"figures -> {args.out_dir}")


if __name__ == "__main__":
    main()
