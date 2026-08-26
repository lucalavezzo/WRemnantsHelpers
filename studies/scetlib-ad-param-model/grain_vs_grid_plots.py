#!/usr/bin/env python3
r"""Plots for the gen-grid granularity scan (see grain_vs_grid.py).

Reads the scan CSV (and, for the mechanism plot, the input npz) and writes the
figures. Deliberately bare matplotlib: every panel here is a scaling curve or a
scatter of derived quantities against a grid resolution, not a histogram, so
``wums.plot_tools`` has nothing to build -- its makePlotWithRatioToRef frame
assumes hist objects on a physics axis. ``wums.output_tools.write_index_and_log``
is still used so each figure carries its command and provenance next to it.
"""

import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

BLUE, RED, PURPLE, GREEN, ORANGE = "#5790fc", "#e42536", "#964a8b", "#2ca02c", "#f89c20"


def load(csv_path):
    rows = list(csv.DictReader(open(csv_path)))
    for r in rows:
        for k in r:
            if k != "direction":
                r[k] = float(r[k])
    return rows


def stat(rows, k, m, col, how="median"):
    v = np.array([r[col] for r in rows if r["k"] == k and r["m"] == m], float)
    v = v[np.isfinite(v) & (v > 0)]
    if v.size == 0:
        return np.nan
    return float(np.median(v)) if how == "median" else float(v.max())


def fit_power(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
    p, lc = np.polyfit(np.log(x[ok]), np.log(y[ok]), 1)
    return float(np.exp(lc)), float(p)


def save(fig, outdir, name, meta):
    os.makedirs(outdir, exist_ok=True)
    fig.savefig(os.path.join(outdir, name + ".png"), dpi=150, bbox_inches="tight")
    fig.savefig(os.path.join(outdir, name + ".pdf"), bbox_inches="tight")
    plt.close(fig)
    try:
        from wums import output_tools
        output_tools.write_index_and_log(outdir, name, analysis_meta_info=meta,
                                         args=None)
    except Exception as exc:  # pragma: no cover
        print(f"   [warn] write_index_and_log: {exc}")


# --------------------------------------------------------------------------
def plot_vs_resolution(rows, outdir, axis, meta, measured=None):
    """GRAIN and CALC against the number of gen bins on one axis.

    ``axis`` = 'qt' scans the qT coarsening at the finest |Y|; 'y' the reverse.
    ``measured`` = (nbins, {label: value}) for the directly measured finer grid.
    """
    ks = sorted({r["k"] for r in rows})
    ms = sorted({r["m"] for r in rows})
    if axis == "qt":
        xs = [(k, stat([r for r in rows if r["m"] == 1], k, 1, "nT")) for k in ks]
        nb = np.array([x[1] for x in xs])
        sel = lambda k, col, how: stat(rows, k, 1, col, how)  # noqa: E731
        keys = ks
        xlabel = "gen $q_T$ bins (incl. the trailing overflow bin)"
    else:
        nb = np.array([stat(rows, 1, m, "nY") for m in ms])
        sel = lambda m, col, how: stat(rows, 1, m, col, how)  # noqa: E731
        keys = ms
        xlabel = "gen $|Y|$ bins"

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    series = [
        ("GRAIN  median over 39 directions", "grain_wmean", "median", RED, "o"),
        ("GRAIN  worst direction", "grain_wmean", "max", RED, "s"),
        ("CALC   median over 39 directions", "calc_wmean", "median", BLUE, "o"),
        ("CALC   worst direction", "calc_wmean", "max", BLUE, "s"),
    ]
    for lab, col, how, c, mk in series:
        y = np.array([sel(k, col, how) for k in keys])
        ls = "-" if how == "median" else "--"
        ax.plot(nb, y, ls, marker=mk, color=c, label=lab, lw=1.8, ms=6,
                alpha=0.9 if how == "median" else 0.6)

    # Power law on the two finest points. Drawn for qT only: in |Y| the
    # correction file's own cells stop at 11 bins, so an extrapolation past
    # that has nothing to converge to and would badly overstate the gain (the
    # power law says 1.9x for 10 -> 20; the MEASURED 10 -> 11 is 1.05x).
    y = np.array([sel(k, "grain_wmean", "median") for k in keys])
    order = np.argsort(nb)[::-1]
    C, p = fit_power(nb[order][:2], y[order][:2])
    if axis == "qt":
        xx = np.array([nb.max() * 2.2, nb.max()])
        ax.plot(xx, C * xx ** p, ":", color=RED, lw=1.4,
                label=rf"power law on the 2 finest points, $p={p:.2f}$")
        ax.plot([nb.max() * 2], [C * (nb.max() * 2) ** p], "*", color=RED,
                ms=14, markerfacecolor="none", label="extrapolated 2x finer")
    else:
        ax.axvline(11, color="k", lw=1.0, ls=":", alpha=0.7)
        ax.annotate("the correction's own\n$|Y|$ cells stop here (11)",
                    (11, y.min()), textcoords="offset points", xytext=(-4, 4),
                    fontsize=8, ha="right")
    for mn, mmed, mwst in (measured or []):
        ax.plot([mn], [mmed], "*", color=GREEN, ms=17, zorder=6,
                label="MEASURED (dedicated histmaker): median")
        ax.plot([mn], [mwst], "*", color=GREEN, ms=11, markerfacecolor="none",
                zorder=6, label="MEASURED: worst")

    ax.set_xscale("log"); ax.set_yscale("log")
    ticks = sorted(set(list(nb) + [nb.max() * 2]))
    ax.set_xticks(ticks, minor=False)
    ax.set_xticklabels([f"{int(t)}" for t in ticks])
    ax.set_xticks([], minor=True)
    ax.set_xlabel(xlabel); ax.set_ylabel(r"yield-weighted mean $|$model/ref $-1|$")
    ax.grid(alpha=0.3, which="major")
    ax.legend(fontsize=8, loc="upper right")
    ax.set_title("Reco-level residual against gen-grid resolution\n"
                 "(coarsenings of the shipped card; finer is an extrapolation)",
                 fontsize=10)
    save(fig, outdir, f"grain_vs_{axis}_resolution", meta)


def plot_heatmap(rows, outdir, meta):
    ks = sorted({r["k"] for r in rows}); ms = sorted({r["m"] for r in rows})
    nT = [stat(rows, k, ms[0], "nT") for k in ks]
    nY = [stat(rows, ks[0], m, "nY") for m in ms]
    Z = np.array([[stat(rows, k, m, "grain_wmean") for m in ms] for k in ks])
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    pc = ax.imshow(np.log10(Z.T), origin="lower", cmap="viridis", aspect="auto")
    fig.colorbar(pc, ax=ax, label=r"$\log_{10}$ median GRAIN (yield-weighted)")
    ax.set_xticks(range(len(ks))); ax.set_xticklabels([f"{int(v)}" for v in nT])
    ax.set_yticks(range(len(ms))); ax.set_yticklabels([f"{int(v)}" for v in nY])
    ax.set_xlabel("gen $q_T$ bins"); ax.set_ylabel("gen $|Y|$ bins")
    for i in range(len(ks)):
        for j in range(len(ms)):
            ax.text(i, j, f"{Z[i, j]*1e4:.1f}", ha="center", va="center",
                    color="w", fontsize=8)
    ax.set_title(r"median GRAIN $\times 10^{4}$; shipped grid is the top-left cell",
                 fontsize=10)
    save(fig, outdir, "grain_heatmap", meta)


def plot_sawtooth(npz, outdir, meta, which=("lambda21.0", "mufup",
                                            "pdfCT18ZNNLO_as_0120", "b_qqV0.5")):
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from grain_vs_grid import Grid

    z = np.load(npz)
    labels = [str(x) for x in z["labels"]]
    rs = tuple(int(v) for v in z["reco_shape"])
    pt, Te = z["reco_edges_0"], z["Te"]
    G = Grid(z, 1, 1)
    cen = z["ref_cen"][0].reshape(rs)
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.0), sharex=True)
    for ax, L in zip(axes.ravel(), which):
        i = labels.index(L)
        rho = G.rho(z["corr_num"][i], z["corr_den"][i])
        rho = np.where(np.isfinite(rho), rho, 1.0)
        c = z["ref_cen"][z["ref_cen_of"][i]]
        rr = np.where(c > 0, z["ref_var"][i] / c, np.nan)
        d = (G.r_B(rho) / rr - 1.0).reshape(rs)
        prof = np.nansum(d * cen, axis=1) / cen.sum(axis=1)
        x = 0.5 * (pt[:-1] + pt[1:])
        ax.step(np.arange(rs[0] + 1), np.append(prof, prof[-1]) * 1e4,
                where="post", color=RED, lw=1.8)
        ax.axhline(0, color="k", lw=0.8)
        # mark where a gen qT bin boundary falls
        for e in Te[:21]:
            j = np.searchsorted(pt, e - 1e-9)
            if 0 < j < rs[0]:
                ax.axvline(j, color=BLUE, lw=0.7, alpha=0.45)
        ax.set_title(L, fontsize=10)
        ax.grid(alpha=0.25)
        ax.set_xticks(np.arange(0, rs[0] + 1, 3))
        ax.set_xticklabels([f"{pt[min(k, rs[0])]:g}" for k in
                            range(0, rs[0] + 1, 3)], fontsize=8)
    for ax in axes[1]:
        ax.set_xlabel(r"$p_T^{\ell\ell}$ [GeV]")
    for ax in axes[:, 0]:
        ax.set_ylabel(r"GRAIN, $|Y|$-integrated $[\times 10^{4}]$")
    fig.suptitle("GRAIN alternates with the gen bin boundary (blue lines): one "
                 "gen $q_T$ bin covers two reco bins,\nso the model gives both "
                 "the same bin-averaged response while the truth differs",
                 fontsize=10)
    fig.tight_layout()
    save(fig, outdir, "grain_sawtooth", meta)


def plot_alphas(rows, outdir, meta):
    ks = sorted({r["k"] for r in rows})
    nT = np.array([stat(rows, k, 1, "nT") for k in ks])
    sig = np.array([[r["sigma_as"] for r in rows if r["k"] == k and r["m"] == 1][0]
                    for k in ks])
    # Normalise by the SHIPPED grid's sigma throughout: each grid's own sigma
    # also grows when the grid is coarsened, and dividing by it would hide half
    # the effect behind the other half.
    sig0 = sig[int(np.argmax(nT))]
    worst, quad, wcalc = [], [], []
    for k in ks:
        g = np.array([abs(r["eq_as_grain"]) for r in rows
                      if r["k"] == k and r["m"] == 1])
        c = np.array([abs(r["eq_as_calc"]) for r in rows
                      if r["k"] == k and r["m"] == 1])
        worst.append(g.max() / sig0); quad.append(np.sqrt((g ** 2).sum()) / sig0)
        wcalc.append(c.max() / sig0)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.4))
    a1.plot(nT, worst, "-o", color=RED, label="GRAIN, worst direction")
    a1.plot(nT, quad, "-s", color=PURPLE, label="GRAIN, quadrature over 39")
    a1.plot(nT, wcalc, "--o", color=BLUE, label="CALC, worst direction")
    a1.set_xscale("log"); a1.set_yscale("log")
    for a in (a1, a2):
        a.set_xticks(sorted(nT)); a.set_xticklabels([f"{int(t)}" for t in sorted(nT)])
        a.set_xticks([], minor=True)
    a1.set_xlabel("gen $q_T$ bins")
    a1.set_ylabel(r"$|\Delta\alpha_s|/\sigma(\alpha_s)$ [shipped-grid $\sigma$]")
    a1.grid(alpha=0.3, which="major"); a1.legend(fontsize=8)
    a1.set_title(r"$\alpha_s$ equivalent of the residual, per unit pull", fontsize=10)
    a2.plot(nT, sig * 1e4, "-o", color=GREEN)
    a2.set_xscale("log")
    a2.set_xlabel("gen $q_T$ bins")
    a2.set_ylabel(r"Fisher $\sigma(\alpha_s)\times 10^{4}$")
    a2.grid(alpha=0.3, which="major")
    a2.set_title("information lost to a coarser grid (Asimov Fisher proxy)",
                 fontsize=10)
    fig.tight_layout()
    save(fig, outdir, "alphas_vs_grid", meta)


def plot_scatter(rows, outdir, meta):
    s = [r for r in rows if r["k"] == 1 and r["m"] == 1]
    g = np.array([r["grain_wmean"] for r in s])
    c = np.array([r["calc_wmean"] for r in s])
    resp = np.array([r["response_wmean"] for r in s])
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    sc = ax.scatter(c, g, c=np.log10(np.maximum(resp, 1e-8)), cmap="plasma",
                    s=46, edgecolor="k", linewidth=0.4)
    fig.colorbar(sc, ax=ax, label=r"$\log_{10}$ of the direction's own response")
    lim = [min(c[c > 0].min(), g[g > 0].min()) * 0.5,
           max(c.max(), g.max()) * 2]
    ax.plot(lim, lim, "k--", lw=1, label="GRAIN = CALC")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("CALC (yield-weighted mean)")
    ax.set_ylabel("GRAIN (yield-weighted mean)")
    ax.grid(alpha=0.3, which="both"); ax.legend(fontsize=9)
    n = int((g > c).sum())
    ax.set_title(f"shipped grid: GRAIN > CALC in {n} of {len(s)} directions",
                 fontsize=10)
    save(fig, outdir, "grain_vs_calc", meta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--npz", required=True)
    ap.add_argument("-o", "--out-dir", required=True)
    ap.add_argument("--meta", default="")
    args = ap.parse_args()
    rows = load(args.csv)
    meta = {"scan csv": os.path.abspath(args.csv),
            "inputs npz": os.path.abspath(args.npz),
            "note": args.meta}
    plot_vs_resolution(rows, args.out_dir, "qt", meta)
    # the measured 11-bin |Y| point comes from the corr-grid histmaker
    # (grain_corrgrid.csv, qgrid=card / ygrid=fine)
    plot_vs_resolution(rows, args.out_dir, "y", meta,
                       measured=[(11, 5.083e-05, 3.946e-04)])
    plot_heatmap(rows, args.out_dir, meta)
    plot_sawtooth(args.npz, args.out_dir, meta)
    plot_alphas(rows, args.out_dir, meta)
    plot_scatter(rows, args.out_dir, meta)
    print(f"figures -> {args.out_dir}")


if __name__ == "__main__":
    main()
