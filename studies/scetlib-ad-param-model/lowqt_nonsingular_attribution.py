#!/usr/bin/env python3
"""Who owns the qT < 2 GeV residual -- us, or the template's nonsingular cutoff?

``residual_structure_map.py`` measured the residual and priced it in alpha_s.
Its ranking put mufup (0.25 sigma), lambda2 (0.18) and kappa_R (0.17) at the
top, all with their residual in the first one or two qT bins, and none of them
improving when the integration tolerance is tightened. This script asks whether
that residual is a MODEL defect at all.

THE ASYMMETRY. The production correction zeroes its nonsingular below
``--qtCutoff`` (make_theory_corr.py, default 1.0 GeV, applied as
``zero_nons_bins = slice(0j, 1j)``). Ours is SCETlib's own analytic V+jet and is
cut at 0.1 GeV (``matched_nons_qt_cut``, config default 0.1). The card's first
gen bin is exactly qT [0,1]. So in that bin the template's variation ratio is a
SINGULAR-ONLY ratio while ours is a matched one, and for a direction with
resummed response s and nonsingular response n,

    r_model = 1 + s + f (n - s),   r_template = 1 + s,     f = N/sigma
    =>   d = r_model/r_template - 1 = f (n - s)

with no free parameter. f is -3.2% there, and n - s is 0.26 for mufup (the
fixed order swings hard at qT -> 0 while the resummed piece barely moves), so
d = -0.8%: the whole observed residual.

THE TEST is assumption-free because f_t = 0 exactly: rebuild the SAME ratio from
our own singular piece alone and see it collapse. Nothing else changes -- same
cache, same rules, same bins, same templates.

    d_matched  = (sigma_var/sigma_cen) / (Corr_var/Corr_cen) - 1
    d_aligned  = the same with our nonsingular dropped in qT [0,1] only, i.e.
                 what a cache built with ``matched_nons_qt_cut = 1.0`` gives

and then the alpha_s-equivalent projection is rerun on both, so the ranking
stays comparable to residual_structure_map.py's.

Usage (in the container, see incontainer.sh):

    ./lowqt_nonsingular_attribution.py --cache <cache.npz> --conf <cache.conf> \\
        --corr <CorrZ> <pdfas_CorrZ> --npz <out.npz> -o <dir>
    ./lowqt_nonsingular_attribution.py --from-npz <out.npz> -o <dir>
"""

import argparse
import os
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)
sys.path.insert(0, os.path.join(WREM, "scripts", "rabbit", "scetlib_ad"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from residual_structure_map import _grid_ticks, _safe, _save, group_of  # noqa: E402

SIG_AS = 6.16e-4      # Asimov fit A, 6 floating (logbook 2026-08-21); no PDF eig
# The nuisance basis the alpha_s projection profiles over: the up leg of every
# non-transition template pair. Same list residual_structure_map.py's companion
# used, so the two rankings are directly comparable.
BASIS = ["kappaFO2.-kappaf0.5", "kappaFO0.5-kappaf2.", "mufup", "mufdown",
         "lambda21.0", "lambda41.0", "delta_lambda20.02", "lambda2_nu0.25",
         "gamma_cusp1.", "gamma_mu_q1.", "gamma_nu1.", "s1.", "h_qqV1.",
         "b_qqV0.5", "b_qqbarV0.5", "b_qqS0.5", "b_qg0.5"]
SIX = ["mufup", "mufdown", "kappaFO0.5-kappaf2.", "kappaFO2.-kappaf0.5",
       "pdfCT18ZNNLO_as_0120", "pdfCT18ZNNLO_as_0116"]


# ---------------------------------------------------------------- compute --
def compute(args):
    from validate_variations import (  # noqa: E402
        central_label, load_corr, merge_matrix, variation_for,
    )
    from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

    core = ScetlibADXsec(args.conf, args.cache, threads=args.threads)
    names = list(core.param_names)
    fn, b = core._fn, core.bins
    yl = np.unique(np.round(b[:, 2:4], 12), axis=0); yl = yl[np.argsort(yl[:, 0])]
    tl = np.unique(np.round(b[:, 4:6], 12), axis=0); tl = tl[np.argsort(tl[:, 0])]
    Ye = np.concatenate([yl[:, 0], yl[-1:, 1]])
    Te = np.concatenate([tl[:, 0], tl[-1:, 1]])
    if abs(Te[1] - args.ref_cutoff) > 1e-9:
        raise SystemExit(
            f"the first qT bin ends at {Te[1]}, not at the reference cutoff "
            f"{args.ref_cutoff}: the alignment is only exact when they coincide."
        )
    fold = core.fold_for([("ptVGen", Te), ("absYVGen", Ye)], b[0, 0], b[0, 1],
                         partial=args.partial)
    cover = fold.covered_mask.T
    yfac = 2.0 if getattr(fold, "y_convention", "") == "positive-side-only" else 1.0

    def onto(a):
        return fold(np.asarray(a, float)).reshape(Te.size - 1, Ye.size - 1).T

    anchor = core.anchor.copy()

    def pieces(p):
        """(matched, nonsingular, singular) on the gen grid."""
        tot = np.asarray(core.values_and_jacobian(p)[0], float)
        non = np.asarray(fn._nons.fo_binned_pdf_batch(
            b, np.ascontiguousarray(np.asarray(p, float)[fn._cols]))["value"], float)
        return onto(tot), onto(non), onto(tot - non)

    tot_c, non_c, sng_c = pieces(anchor)
    _, J = core.values_and_jacobian(anchor)
    R_as = onto(J[:, names.index("alphas")]) / tot_c
    print(f"nonsingular fraction f = N/sigma: {np.nanmin(non_c/tot_c):+.4f} .. "
          f"{np.nanmax(non_c/tot_c):+.4f};  in qT [0,1]: "
          f"{np.nansum(non_c[:,0])/np.nansum(tot_c[:,0]):+.4f}")

    labels, D_m, D_a, RR, N_r, S_r = [], [], [], [], [], []
    delta = None
    for path in args.corr:
        h = load_corr(path)
        ax = {a.name: a for a in h.axes}
        labs = [str(x) for x in ax["vars"]]
        vv = np.asarray(h.values(flow=False))
        dims = [a.name for a in h.axes]
        vv = np.squeeze(vv, axis=(dims.index("Q"), dims.index("charge")))
        order = [d for d in dims if d not in ("Q", "charge")]
        vv = np.moveaxis(vv, [order.index("absY"), order.index("qT"),
                              order.index("vars")], [0, 1, 2])
        MY = merge_matrix(ax["absY"].edges, Ye, "absY")
        MT = merge_matrix(ax["qT"].edges, Te, "qT")

        def ref(L):
            return MY @ vv[:, :, labs.index(L)] @ MT.T

        cen_lab = central_label(labs)
        r_cen = ref(cen_lab)
        if delta is None:
            # central shape mismatch, YIELD-normalised (not median): the leftover
            # constant is then the yield-weighted mean of f - f_t, which is what
            # the cutoff argument predicts to be ~0.
            wq = tot_c / np.nansum(tot_c)
            cc = tot_c * yfac / r_cen
            delta = cc / np.nansum(wq * cc) - 1.0
            print(f"Delta at qT[0,1] |Y|<0.15: {delta[0,0]:+.5f}   f there: "
                  f"{(non_c/tot_c)[0,0]:+.5f}   -> implied f_t = "
                  f"{(non_c/tot_c)[0,0]-delta[0,0]:+.5f}  (0 if the template's "
                  f"nonsingular is cut at {args.ref_cutoff} GeV)")
        for L in labs:
            ov = variation_for(L)
            if ov is None or L == cen_lab or any(k not in names for k in ov):
                continue
            p = anchor.copy()
            for k, val in ov.items():
                p[names.index(k)] = val
            tv, nv, sv = pieces(p)
            rr = ref(L) / np.where(r_cen == 0, np.nan, r_cen)
            good = cover & np.isfinite(rr) & (rr != 0)
            dm = np.where(good, (tv / tot_c) / rr - 1.0, np.nan)
            da = dm.copy()
            da[:, 0] = np.where(good[:, 0],
                                (sv[:, 0] / sng_c[:, 0]) / rr[:, 0] - 1.0, np.nan)
            labels.append(L); D_m.append(dm); D_a.append(da); RR.append(rr)
            N_r.append(nv / non_c); S_r.append(sv / sng_c)
            print(f"  {L:<32} max|d| {np.nanmax(np.abs(dm)):8.2e} -> aligned "
                  f"{np.nanmax(np.abs(da)):8.2e}   qT[0,1] "
                  f"{np.nanmean(dm[:,0])*1e4:8.2f} -> {np.nanmean(da[:,0])*1e4:6.2f} e-4",
                  flush=True)

    np.savez(args.npz, labels=np.array(labels), d=np.array(D_m),
             d_aligned=np.array(D_a), rr=np.array(RR), rn=np.array(N_r),
             rs=np.array(S_r), Te=Te, Ye=Ye, s_cen=tot_c, non_c=non_c,
             sng_c=sng_c, delta=delta, R_as=R_as, cover=cover,
             cache=os.path.abspath(args.cache), ref_cutoff=args.ref_cutoff)
    print(f"\nwrote {args.npz}  ({len(labels)} directions)")


# ------------------------------------------------------------- alpha_s -----
def alphas_equivalents(z, N=1e7):
    """{label: (today, aligned, no[0,1], no[0,1]+[1,2])} in absolute alpha_s."""
    labels = [str(x) for x in z["labels"]]
    d, da, rr, R_as, sig = z["d"], z["d_aligned"], z["rr"], z["R_as"], z["s_cen"]
    basis = [L for L in BASIS if L in labels]
    ok = np.isfinite(d[0]) & np.isfinite(R_as) & np.isfinite(sig)
    Bmat = np.stack([np.where(ok, rr[labels.index(L)] - 1.0, 0.0).ravel()
                     for L in basis], axis=1)

    def solve(dd, L, mask):
        m = ok & mask
        n = np.where(m, sig, 0.0).ravel(); n = n / n.sum() * N
        keep = [k for k, nm in enumerate(basis) if nm != L]
        A = np.concatenate([np.where(m, R_as, 0).ravel()[:, None], Bmat[:, keep]], 1)
        M = A.T @ (n[:, None] * A)
        P = np.zeros_like(M); P[1:, 1:] = np.eye(len(keep))
        rhs = A.T @ (n * np.where(m, dd, 0.0).ravel())
        return float(np.linalg.lstsq(M + P, rhs, rcond=None)[0][0])

    full = np.ones_like(ok)
    no01 = full.copy(); no01[:, 0] = False
    no012 = no01.copy(); no012[:, 1] = False
    out = {}
    for i, L in enumerate(labels):
        out[L] = (solve(d[i], L, full), solve(da[i], L, full),
                  solve(d[i], L, no01), solve(d[i], L, no012))
    return out


# ------------------------------------------------------------------ plots --
def plot_split(z, outdir, meta):
    """|Y|-integrated residual per qT bin, today vs aligned, for the six."""
    import matplotlib.pyplot as plt

    labels = [str(x) for x in z["labels"]]
    Te, sig = z["Te"], z["s_cen"]
    fig, axes = plt.subplots(2, 3, figsize=(17, 9), sharex=True)
    for k, L in enumerate(SIX):
        ax = axes[k // 3][k % 3]
        i = labels.index(L)
        # the two curves are IDENTICAL outside qT [0,1] by construction, so
        # the shipped one is drawn wide and the aligned one on top of it: the
        # only place they separate is the first bin, which is the whole point.
        for arr, col, lw, nm in (
                (z["d"][i], "#e42536", 4.0, "shipped (matched)"),
                (z["d_aligned"][i], "#5790fc", 1.6,
                 r"aligned: our $N$ dropped in $q_\mathrm{T}\,[0,1]$")):
            y = np.nansum(sig * arr, axis=0) / np.nansum(sig, axis=0)
            ax.step(np.arange(Te.size), np.append(y, y[-1]) * 1e4, where="post",
                    lw=lw, color=col, label=nm, alpha=0.95)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xticks(np.arange(Te.size))
        ax.set_xticklabels([f"{v:g}" for v in Te], rotation=90, fontsize=8)
        ax.set_title(L, fontsize=11)
        ax.grid(alpha=0.3)
        if k == 0:
            ax.legend(fontsize=9)
        if k % 3 == 0:
            ax.set_ylabel(r"(model/template $-1)\times 10^{4}$")
        if k // 3 == 1:
            ax.set_xlabel(r"boson $q_\mathrm{T}$ bin edges (GeV)")
    fig.tight_layout()
    _save(fig, outdir, "residual_matched_vs_aligned", meta)
    plt.close(fig)


def plot_delta_vs_f(z, outdir, meta):
    """Delta(bin) against our own nonsingular fraction f, per qT bin.

    The cutoff argument predicts Delta = f - f_t with f_t = 0 in the first bin
    and f_t ~ f above it, i.e. the two curves must MEET at qT [0,1] and separate
    immediately after. Nothing is fitted."""
    import matplotlib.pyplot as plt

    Te, sig = z["Te"], z["s_cen"]
    f = z["non_c"] / z["s_cen"]
    w = np.nansum(sig, axis=0)
    fq = np.nansum(sig * f, axis=0) / w
    dq = np.nansum(sig * z["delta"], axis=0) / w
    fig, ax = plt.subplots(figsize=(9, 5.6))
    x = np.arange(Te.size)
    ax.step(x, np.append(fq, fq[-1]), where="post", lw=2.0, color="#7a21dd",
            label=r"our nonsingular fraction $f = N/\sigma$")
    ax.step(x, np.append(dq, dq[-1]), where="post", lw=2.0, color="#f89c20",
            label=r"central shape mismatch $\Delta$ (model/template)")
    ax.step(x, np.append(fq - dq, (fq - dq)[-1]), where="post", lw=1.6,
            ls="--", color="#5790fc",
            label=r"implied template fraction $f_t = f - \Delta$")
    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(1, color="k", lw=1.0, ls=":")
    # the gen-overflow bin [44,100] has f = +0.19 and would flatten everything
    # else; it is off-scale on purpose and quoted in the axis label instead.
    lo = float(np.nanmin(fq[:-1])); hi = float(np.nanmax(np.abs(dq[:-1])))
    ax.set_ylim(lo - 0.006, max(hi, 0.006) + 0.006)
    ax.text(1.12, lo - 0.004, "production --qtCutoff = 1 GeV",
            rotation=90, fontsize=9, va="bottom")
    ax.annotate(r"$f_t \to 0$: the template has NO nonsingular here",
                xy=(0.55, (fq - dq)[0]), xytext=(3.4, 0.013), fontsize=9,
                arrowprops=dict(arrowstyle="->", lw=1.0,
                                connectionstyle="arc3,rad=0.2"))
    ax.set_xticks(x)
    ax.set_xticklabels([f"{v:g}" for v in Te], rotation=90, fontsize=9)
    ax.set_xlabel(r"boson $q_\mathrm{T}$ bin edges (GeV)")
    ax.set_ylabel(r"fraction of $\sigma$")
    ax.set_title(r"the gen-overflow bin $q_\mathrm{T}$ [44,100] is off scale "
                 r"($f = +0.19$)", fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    _save(fig, outdir, "nonsingular_fraction_vs_delta", meta)
    plt.close(fig)


def plot_alphas(z, eq, outdir, meta):
    """Every direction in alpha_s units, today vs aligned."""
    import matplotlib.pyplot as plt

    cols = {"transition": "#e42536", "lambda": "#5790fc", "tnp": "#964a8b",
            "alphaS": "#f89c20", "scale": "#7a21dd"}
    rows = [(L, abs(v[0]) / SIG_AS, abs(v[1]) / SIG_AS, group_of(L))
            for L, v in eq.items() if abs(v[0]) / SIG_AS > 1e-3
            or abs(v[1]) / SIG_AS > 1e-3]
    rows.sort(key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(9.5, 0.30 * len(rows) + 2.6))
    y = np.arange(len(rows))
    ax.barh(y, [r[1] for r in rows], color=[cols.get(r[3], "grey") for r in rows],
            alpha=0.85)
    ax.plot([r[2] for r in rows], y, "kD", ms=5, label="aligned cutoff")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.set_xscale("log")
    ax.set_xlim(2e-4, 3.0)
    ax.axvline(1.0, color="k", lw=1.2, ls="--")
    ax.text(1.05, 0.5, r"1 $\sigma(\alpha_s)$", rotation=90, fontsize=9)
    ax.set_xlabel(r"equivalent $|\Delta\alpha_s|\,/\,\sigma(\alpha_s)$")
    ax.set_title("bars: the shipped model    diamonds: our nonsingular cut at "
                 "1 GeV, like the template's", fontsize=10)
    ax.grid(axis="x", alpha=0.3)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in cols.values()]
    ax.legend(handles + [plt.Line2D([], [], marker="D", color="k", ls="none")],
              list(cols) + ["aligned cutoff"], fontsize=8, loc="lower right",
              framealpha=0.95, ncol=2)
    fig.tight_layout()
    _save(fig, outdir, "alphas_equivalent_aligned", meta)
    plt.close(fig)


def plot_maps(z, outdir, meta, which):
    """Residual per (|Y|, qT) bin for one direction, shipped and aligned."""
    import matplotlib.pyplot as plt

    labels = [str(x) for x in z["labels"]]
    Te, Ye = z["Te"], z["Ye"]
    for L in which:
        if L not in labels:
            continue
        i = labels.index(L)
        v0, v1 = z["d"][i] * 1e4, z["d_aligned"][i] * 1e4
        m = max(np.nanmax(np.abs(v0)), 1e-3)
        fig, axes = plt.subplots(2, 1, figsize=(12, 10.5))
        for ax, v, nm in ((axes[0], v0, "shipped (matched)"),
                          (axes[1], v1, r"aligned ($N$ dropped in $q_T[0,1]$)")):
            mesh = ax.pcolormesh(np.arange(Te.size), np.arange(Ye.size), v,
                                 cmap="RdBu_r", vmin=-m, vmax=m, shading="flat")
            for a in range(v.shape[0]):
                for c in range(v.shape[1]):
                    if np.isfinite(v[a, c]):
                        ax.text(c + 0.5, a + 0.5, f"{v[a, c]:.1f}", ha="center",
                                va="center", fontsize=6.5,
                                color="k" if abs(v[a, c]) < 0.6 * m else "w")
            _grid_ticks(ax, Te, Ye)
            fig.colorbar(mesh, ax=ax,
                         label=r"(model/template $-$ 1) $\times 10^{4}$")
            ax.set_title(f"{L}  --  {nm}", fontsize=12)
        fig.tight_layout()
        _save(fig, outdir, f"map2_{_safe(L)}", meta)
        plt.close(fig)


# ------------------------------------------------------------------- main --
def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache")
    ap.add_argument("--conf")
    ap.add_argument("--corr", nargs="+", default=[])
    ap.add_argument("--threads", type=int, default=64)
    ap.add_argument("--partial", action="store_true")
    ap.add_argument("--npz")
    ap.add_argument("--from-npz")
    ap.add_argument("--ref-cutoff", type=float, default=1.0,
                    help="the production correction's --qtCutoff (GeV). The "
                         "alignment is exact only if a gen qT bin edge sits "
                         "there; checked, not assumed.")
    ap.add_argument("-o", "--out-dir")
    ap.add_argument("--events", type=float, default=1e7,
                    help="event count for the prior-weighted alpha_s projection")
    args = ap.parse_args()

    if args.from_npz is None:
        if not (args.cache and args.conf and args.corr and args.npz):
            raise SystemExit("compute needs --cache --conf --corr --npz")
        compute(args)
        args.from_npz = args.npz

    z = np.load(args.from_npz, allow_pickle=False)
    eq = alphas_equivalents(z, N=args.events)
    print("\n" + "=" * 96)
    print("EQUIVALENT alpha_s SHIFT, profiled over the other theory nuisances "
          f"(unit priors, N = {args.events:g})")
    print("=" * 96)
    print(f"{'direction':<32}{'shipped':>11}{'/sig':>8}{'aligned':>11}{'/sig':>8}"
          f"{'drop[0,1]':>11}{'/sig':>8}{'drop[0,1]+[1,2]':>17}{'/sig':>8}")
    for L, v in sorted(eq.items(), key=lambda kv: -abs(kv[1][0])):
        print(f"{L:<32}{v[0]:11.2e}{abs(v[0])/SIG_AS:8.3f}{v[1]:11.2e}"
              f"{abs(v[1])/SIG_AS:8.3f}{v[2]:11.2e}{abs(v[2])/SIG_AS:8.3f}"
              f"{v[3]:17.2e}{abs(v[3])/SIG_AS:8.3f}")
    print(f"\nsigma(alpha_s) = {SIG_AS:.2e} (Asimov fit A, 6 floating, no PDF eig)")

    if args.out_dir:
        meta = {
            "what": "attribution of the low-qT model/template residual to the "
                    "production correction's nonsingular qT cutoff",
            "cache": str(z["cache"]),
            "npz": os.path.abspath(args.from_npz),
            "reference cutoff (GeV)": float(z["ref_cutoff"]),
        }
        plot_split(z, args.out_dir, meta)
        plot_delta_vs_f(z, args.out_dir, meta)
        plot_alphas(z, eq, args.out_dir, meta)
        plot_maps(z, args.out_dir, meta, SIX + ["lambda21.0"])
        print(f"\nplots -> {args.out_dir}")


if __name__ == "__main__":
    main()
