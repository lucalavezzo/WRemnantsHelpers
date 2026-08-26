#!/usr/bin/env python3
"""Is the model/template residual STRUCTURED, and is that structure special?

``validate_variations.py`` answers "how big" (max and mean over bins) and, with
``--profile``, "where in qT" (max over |Y|). Neither can tell a structured
residual from scatter of the same size, and the |Y|-integrated response plot
hides whatever the rapidity dependence is. That distinction is the whole
question for the transition points: 1-3e-03 that looks like noise is a floor,
1-3e-03 with a coherent dip/bump/offset is a defect.

So this dumps the residual itself,

    d(|Y|, qT) = [sigma_model(var) / sigma_model(anchor)]
               / [Corr[var]        / Corr[central]]      - 1

per bin, for EVERY mapped variation at once (39 of them cost ~0.2 s each once
the cache is loaded), and writes one npz. Everything downstream -- maps,
per-|Y| profiles, the cross-direction comparison, the floor test -- reads that
npz, so the plots can be re-cut without paying for SCETlib again.

THE FLOOR TEST. Our matched prediction is sigma = S + N with N SCETlib's own
analytic V+jet; the template's is S + N_t with N_t from DYTurbo. Write f =
N/sigma. For a variation whose relative response is s on the resummed piece and
n on the nonsingular one,

    r_model = 1 + s + f  (n - s),     r_ref = 1 + s + f_t (n - s)
    =>  d ~ (f - f_t) (n - s) ~ -Delta * (r_ref - 1)    when n = 0,

where Delta = sigma_model/sigma_ref - 1 in shape, i.e. the CENTRAL mismatch that
is already measured and already known to be a few percent. That is a
quantitative, falsifiable prediction with NO free parameter per direction: the
residual of every direction that does not move the nonsingular (the lambdas, the
TNPs, and the transition points) must lie on one line whose slope is set by the
central mismatch alone. If the transitions sit on that line with everything
else, they are a floor; if they sit off it, they are not.

It is also tested non-parametrically, which does not need Delta at all: fit one
coefficient C(bin) across directions and see whether a SINGLE per-bin number
explains all of them (R^2 per bin), then ask separately whether C = -Delta.

Usage (in the container, see incontainer.sh):

    ./residual_structure_map.py --cache <cache.npz> --conf <cache.conf> \\
        --corr <CorrZ> <pdfas_CorrZ> -o <dir> --npz <out.npz>
    ./residual_structure_map.py --from-npz <out.npz> [--tol-npz <other.npz>] -o <dir>
"""

import argparse
import os
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)
sys.path.insert(0, os.path.join(WREM, "scripts", "rabbit", "scetlib_ad"))

# Directions whose nonsingular piece does NOT move: the NP lambdas and the TNPs
# live entirely in the resummed calculation, and the transition points move the
# matching profile. alphaS / muF / kappa_R DO move the fixed order (ours through
# the frozen grid, the template's through DYTurbo) and are kept separate,
# because for them n != 0 and the one-line prediction above does not apply.
def group_of(label):
    if label.startswith("transition_points"):
        return "transition"
    if label.startswith(("lambda", "delta_lambda")):
        return "lambda"
    if label.startswith(("gamma_", "b_", "h_qqV", "s1", "s-1")):
        return "tnp"
    if "as_0" in label or "ALPHAS_" in label:
        return "alphaS"
    if label.startswith("muf") or label.startswith("kappaFO"):
        return "scale"
    return "other"


N_MOVES_FO = ("alphaS", "scale")   # groups whose nonsingular responds too


# ---------------------------------------------------------------- compute --
def compute(args):
    from validate_variations import (  # noqa: E402
        central_label,
        load_corr,
        merge_matrix,
        variation_for,
    )
    from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

    core = ScetlibADXsec(args.conf, args.cache, threads=args.threads)
    names = list(core.param_names)
    b = core.bins
    yl = np.unique(np.round(b[:, 2:4], 12), axis=0)
    tl = np.unique(np.round(b[:, 4:6], 12), axis=0)
    yl, tl = yl[np.argsort(yl[:, 0])], tl[np.argsort(tl[:, 0])]
    Ye = np.concatenate([yl[:, 0], yl[-1:, 1]])
    Te = np.concatenate([tl[:, 0], tl[-1:, 1]])
    print(f"cache: {core.n_bins} bins, {core.n_params} params")
    print(f"grid: |Y| {Ye.size-1} [{Ye[0]:g},{Ye[-1]:g}], qT {Te.size-1} "
          f"[{Te[0]:g},{Te[-1]:g}]")

    fold = core.fold_for(
        [("ptVGen", Te), ("absYVGen", Ye)], b[0, 0], b[0, 1], partial=args.partial
    )
    cover = fold.covered_mask.T
    yfac = 2.0 if getattr(fold, "y_convention", "") == "positive-side-only" else 1.0
    anchor = core.anchor.copy()

    def model(overrides):
        p = anchor.copy()
        for k, v in overrides.items():
            if k not in names:
                return None
            p[names.index(k)] = v
        vals, _ = core.values_and_jacobian(p)
        return fold(np.asarray(vals, float)).reshape(Te.size - 1, Ye.size - 1).T

    s_cen = model({})

    # The nonsingular alone, at the anchor: f = N / sigma is the weight the
    # floor prediction multiplies. Read straight off the frozen fixed-order
    # grid; guarded because it reaches into the cached-xsec internals.
    f_nons = np.full_like(s_cen, np.nan)
    try:
        fn = core._fn
        nv = fn._nons.fo_binned_pdf_batch(core.bins, anchor[fn._cols])["value"]
        n_on_grid = fold(np.asarray(nv, float)).reshape(Te.size - 1, Ye.size - 1).T
        f_nons = n_on_grid / s_cen
        print(f"nonsingular fraction f: {np.nanmin(f_nons):+.4f} .. "
              f"{np.nanmax(f_nons):+.4f}")
    except Exception as e:  # pragma: no cover - diagnostic only
        print(f"   (nonsingular fraction unavailable: {e})")

    labels_out, d_maps, rr_maps, rm_maps = [], [], [], []
    delta = None
    for path in args.corr:
        h = load_corr(path)
        ax = {a.name: a for a in h.axes}
        labels = [str(x) for x in ax["vars"]]
        vals = np.asarray(h.values(flow=False))
        dims = [a.name for a in h.axes]
        vals = np.squeeze(vals, axis=(dims.index("Q"), dims.index("charge")))
        order = [d for d in dims if d not in ("Q", "charge")]
        vals = np.moveaxis(
            vals,
            [order.index("absY"), order.index("qT"), order.index("vars")],
            [0, 1, 2],
        )
        MY = merge_matrix(ax["absY"].edges, Ye, "absY")
        MT = merge_matrix(ax["qT"].edges, Te, "qT")

        def ref(label):
            return MY @ vals[:, :, labels.index(label)] @ MT.T

        cen_lab = central_label(labels)
        r_cen = ref(cen_lab)
        if delta is None:
            # CENTRAL shape mismatch, normalised so its median is zero: the
            # overall factor is the |Y| convention (x2) and any common
            # normalisation, neither of which enters a variation ratio.
            cc = np.where(cover & (r_cen != 0), s_cen * yfac / np.where(r_cen == 0, 1, r_cen), np.nan)
            delta = cc / np.nanmedian(cc) - 1.0
            print(f"central shape mismatch Delta: {np.nanmin(delta):+.4f} .. "
                  f"{np.nanmax(delta):+.4f} (median-normalised)")
        for L in labels:
            if L == cen_lab:
                continue
            ov = variation_for(L)
            if ov is None:
                continue
            s_var = model(ov)
            if s_var is None:
                continue
            rm = s_var / s_cen
            rr = ref(L) / np.where(r_cen == 0, np.nan, r_cen)
            d = np.where(cover & np.isfinite(rr) & (rr != 0), rm / rr - 1.0, np.nan)
            labels_out.append(L)
            d_maps.append(d)
            rr_maps.append(rr)
            rm_maps.append(rm)
            print(f"  {L:<32} max|d| {np.nanmax(np.abs(d)):8.2e}  "
                  f"response |rr-1| max {np.nanmax(np.abs(rr - 1)):8.2e}")

    np.savez(
        args.npz,
        labels=np.array(labels_out),
        d=np.array(d_maps),
        rr=np.array(rr_maps),
        rm=np.array(rm_maps),
        delta=delta,
        f_nons=f_nons,
        s_cen=s_cen,
        Ye=Ye,
        Te=Te,
        cover=cover,
        cache=os.path.abspath(args.cache),
    )
    print(f"\nwrote {args.npz}  ({len(labels_out)} directions)")


# ------------------------------------------------------------------ plots --
def _grid_ticks(ax, Te, Ye):
    nT, nY = Te.size - 1, Ye.size - 1
    ax.set_xticks(np.arange(nT + 1))
    ax.set_xticklabels([f"{v:g}" for v in Te], rotation=90, fontsize=11)
    ax.set_yticks(np.arange(nY + 1))
    ax.set_yticklabels([f"{v:g}" for v in Ye], fontsize=11)
    ax.set_xlabel(r"boson $q_\mathrm{T}$ bin edges (GeV)")
    ax.set_ylabel(r"$|Y|$ bin edges")


def _save(fig, outdir, name, meta):
    from wums import output_tools, plot_tools

    os.makedirs(outdir, exist_ok=True)
    plot_tools.save_pdf_and_png(outdir, name, fig=fig)
    output_tools.write_index_and_log(outdir, name, analysis_meta_info=meta, args=None)


def plot_map(d, Te, Ye, label, outdir, meta, zmax=None):
    """The residual per (|Y|, qT) bin, in units of 1e-4.

    Drawn in BIN INDEX space, not in qT: the last gen bin is [44,100] and would
    otherwise take half the axis and hide the transition region entirely. wums
    has no working 2D plotter (``plot_tools.makePlot2D`` builds the figure and
    the CMS label but never draws the values), so this is bare matplotlib.
    """
    import matplotlib.pyplot as plt

    v = d * 1e4
    m = zmax if zmax is not None else np.nanmax(np.abs(v))
    m = max(m, 1e-3)
    fig, ax = plt.subplots(figsize=(11, 6))
    mesh = ax.pcolormesh(
        np.arange(Te.size), np.arange(Ye.size), v, cmap="RdBu_r",
        vmin=-m, vmax=m, shading="flat",
    )
    for i in range(v.shape[0]):
        for j in range(v.shape[1]):
            if np.isfinite(v[i, j]):
                ax.text(j + 0.5, i + 0.5, f"{v[i, j]:.1f}", ha="center",
                        va="center", fontsize=7,
                        color="k" if abs(v[i, j]) < 0.6 * m else "w")
    _grid_ticks(ax, Te, Ye)
    fig.colorbar(mesh, ax=ax, label=r"(model/template $-$ 1) $\times 10^{4}$")
    ax.set_title(label, fontsize=13)
    fig.tight_layout()
    _save(fig, outdir, f"map_{_safe(label)}", meta)
    plt.close(fig)


def plot_profiles(d, Te, Ye, label, outdir, meta):
    """One line per |Y| slice: does the structure move with rapidity?"""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 6))
    x = np.arange(Te.size - 1) + 0.5
    cmap = plt.get_cmap("viridis")
    for i in range(d.shape[0]):
        ax.step(
            np.arange(Te.size), np.append(d[i], d[i, -1]) * 1e4, where="post",
            color=cmap(i / max(1, d.shape[0] - 1)),
            label=f"|Y| {Ye[i]:g}-{Ye[i+1]:g}", lw=1.6,
        )
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(np.arange(Te.size))
    ax.set_xticklabels([f"{v:g}" for v in Te], rotation=90, fontsize=10)
    ax.set_xlabel(r"boson $q_\mathrm{T}$ bin edges (GeV)")
    ax.set_ylabel(r"(model/template $-$ 1) $\times 10^{4}$")
    ax.set_title(label, fontsize=13)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    _save(fig, outdir, f"prof_{_safe(label)}", meta)
    plt.close(fig)
    del x


def plot_compare(npz, labels, Te, outdir, name, meta, weighted=True):
    """|Y|-INTEGRATED residual for several directions on one axis.

    This is the panel Luca read the structure off, so it is reproduced exactly:
    sigma summed over |Y| first on both sides, then divided. Overlaying several
    directions is the cheapest discriminator between "the transitions are
    special" and "everything does this".
    """
    import matplotlib.pyplot as plt

    d, rr, rm = npz["d"], npz["rr"], npz["rm"]
    s_cen = npz["s_cen"]
    all_labels = list(npz["labels"])
    fig, ax = plt.subplots(figsize=(10, 6.5))
    cmap = plt.get_cmap("tab10")
    for k, L in enumerate(labels):
        i = all_labels.index(L)
        if weighted:
            w = s_cen
            num = np.nansum(w * rm[i], axis=0) / np.nansum(w, axis=0)
            den = np.nansum(w * rr[i], axis=0) / np.nansum(w, axis=0)
            y = num / den - 1.0
        else:
            y = np.nanmean(d[i], axis=0)
        ax.step(np.arange(Te.size), np.append(y, y[-1]) * 1e4, where="post",
                lw=1.8, color=cmap(k % 10), label=L)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(np.arange(Te.size))
    ax.set_xticklabels([f"{v:g}" for v in Te], rotation=90, fontsize=10)
    ax.set_xlabel(r"boson $q_\mathrm{T}$ bin edges (GeV)")
    ax.set_ylabel(r"$|Y|$-integrated (model/template $-$ 1) $\times 10^{4}$")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    _save(fig, outdir, name, meta)
    plt.close(fig)


def plot_floor(npz, outdir, meta):
    """d against the floor prediction -Delta*(r_ref-1), every bin, every
    direction that leaves the nonsingular alone. One line, no free parameter."""
    import matplotlib.pyplot as plt

    labels = list(npz["labels"])
    d, rr, delta = npz["d"], npz["rr"], npz["delta"]
    fig, ax = plt.subplots(figsize=(7.5, 7))
    cols = {"transition": "#e42536", "lambda": "#5790fc", "tnp": "#964a8b",
            "alphaS": "#f89c20", "scale": "#7a21dd"}
    seen = set()
    for i, L in enumerate(labels):
        g = group_of(L)
        if g in N_MOVES_FO:
            continue
        x = (-delta * (rr[i] - 1.0)).ravel() * 1e4
        y = d[i].ravel() * 1e4
        ok = np.isfinite(x) & np.isfinite(y)
        ax.scatter(x[ok], y[ok], s=10 if g != "transition" else 26,
                   c=cols.get(g, "grey"), alpha=0.55,
                   marker="o" if g != "transition" else "D",
                   label=None if g in seen else g)
        seen.add(g)
    lim = np.nanmax(np.abs(np.concatenate([ax.get_xlim(), ax.get_ylim()])))
    ax.plot([-lim, lim], [-lim, lim], "k--", lw=1, label="y = x (floor)")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xlabel(r"floor prediction $-\Delta\,(r_\mathrm{ref}-1)\times 10^4$")
    ax.set_ylabel(r"observed (model/template $-1)\times 10^4$")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    _save(fig, outdir, "floor_scatter", meta)
    plt.close(fig)


def plot_tolerance(a, b, labels, outdir, meta, tag_a, tag_b):
    """The SAME bins from a 1e-3 and a 1e-4 cache, side by side."""
    import matplotlib.pyplot as plt

    Te_b, Ye_b = b["Te"], b["Ye"]
    la, lb = list(a["labels"]), list(b["labels"])
    # index of the subset cache's bins inside the full one
    iy = [int(np.argmin(np.abs(a["Ye"] - v))) for v in Ye_b[:-1]]
    it = [int(np.argmin(np.abs(a["Te"] - v))) for v in Te_b[:-1]]
    fig, axes = plt.subplots(1, len(labels), figsize=(5.2 * len(labels), 5.4),
                             squeeze=False)
    for k, L in enumerate(labels):
        ax = axes[0][k]
        da = a["d"][la.index(L)][np.ix_(iy, it)]
        db = b["d"][lb.index(L)]      # already only the subset bins
        x = np.arange(len(it))
        for i in range(len(iy)):
            ax.step(np.append(x, x[-1] + 1), np.append(da[i], da[i, -1]) * 1e4,
                    where="post", color="#e42536", lw=1.8,
                    label=f"{tag_a}" if i == 0 else None)
            ax.step(np.append(x, x[-1] + 1), np.append(db[i], db[i, -1]) * 1e4,
                    where="post", color="#5790fc", lw=1.8, ls="--",
                    label=f"{tag_b}" if i == 0 else None)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xticks(np.arange(len(it) + 1))
        ax.set_xticklabels([f"{v:g}" for v in Te_b], rotation=90, fontsize=9)
        ax.set_xlabel(r"$q_\mathrm{T}$ bin edges (GeV)")
        ax.set_ylabel(r"(model/template $-1)\times 10^4$")
        ax.set_title(L, fontsize=11)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=9)
    fig.tight_layout()
    _save(fig, outdir, "tolerance_compare", meta)
    plt.close(fig)



def plot_relacc(npz, outdir, meta, sl, rname, name):
    """Residual as a FRACTION of each direction's own response, in one qT band.

    The absolute residual is not comparable across directions -- a direction
    with a tiny response has a tiny residual for free. What is comparable is
    rms|model/template - 1| divided by rms|response|: "how well does the model
    reproduce the response it is being asked to reproduce". Directions with no
    response in the band are dropped rather than plotted at a meaningless ratio.
    """
    import matplotlib.pyplot as plt

    labels, d, rr = list(npz["labels"]), npz["d"], npz["rr"]
    rows = []
    for i, L in enumerate(labels):
        x, y = (rr[i] - 1.0)[:, sl], d[i][:, sl]
        rx, ry = np.sqrt(np.nanmean(x**2)), np.sqrt(np.nanmean(y**2))
        if not np.isfinite(rx) or rx < 1e-4:       # no response to reproduce
            continue
        rows.append((L, ry / rx, group_of(L)))
    rows.sort(key=lambda r: r[1])
    cols = {"transition": "#e42536", "lambda": "#5790fc", "tnp": "#964a8b",
            "alphaS": "#f89c20", "scale": "#7a21dd"}
    fig, ax = plt.subplots(figsize=(9, 0.28 * len(rows) + 2.2))
    ax.barh([r[0] for r in rows], [r[1] for r in rows],
            color=[cols.get(r[2], "grey") for r in rows])
    ax.set_xscale("log")
    ax.set_xlabel(r"rms$|$model/template$-1|$ / rms$|$response$|$   "
                  f"({rname})")
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="x", alpha=0.3)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in cols.values()]
    ax.legend(handles, list(cols), fontsize=9, loc="lower right")
    fig.tight_layout()
    _save(fig, outdir, name, meta)
    plt.close(fig)


def plot_scan_overlay(npz, scan_dir, outdir, meta):
    """model/template against model/runcard, the same bins.

    The runcard route refills the beam convolutions at the shifted muF, so it is
    the SAME physics computed exactly; the template is an independent production
    run. If the two comparisons agree, the template is exonerated and the whole
    residual belongs to the parameter route. Reads the JSONs
    ``transition_variation_scan.py`` wrote (|Y| in [0, 0.15]).
    """
    import glob
    import json

    import matplotlib.pyplot as plt

    pairs = {"0.35": "transition_points0.2_0.35_1.0",
             "0.75": "transition_points0.2_0.75_1.0"}
    files = {os.path.basename(f).split("_")[1].rstrip(".json"): f
             for f in glob.glob(os.path.join(scan_dir, "scan_*.json"))}
    labels, d, Te = list(npz["labels"]), npz["d"], npz["Te"]
    have = [k for k in pairs if k in files]
    if not have:
        print(f"   (no scan JSONs in {scan_dir})")
        return
    fig, axes = plt.subplots(1, len(have), figsize=(6.2 * len(have), 5.4),
                             squeeze=False)
    for k, x2 in enumerate(sorted(have)):
        ax = axes[0][k]
        js = json.load(open(files[x2]))
        bins = np.asarray(js["bins"], float)
        dev = np.asarray(js["dev"], float)
        i = labels.index(pairs[x2])
        xs, ys_t, ys_r = [], [], []
        for b, v in zip(bins, dev):
            it = int(np.argmin(np.abs(Te - b[4])))
            xs.append(0.5 * (b[4] + min(b[5], 60.0)))
            ys_t.append(d[i][0, it] * 1e4)     # |Y| bin 0 = [0, 0.15]
            ys_r.append(v * 1e4)
        ax.plot(xs, ys_t, "o-", color="#5790fc", lw=1.8,
                label="model / TEMPLATE")
        ax.plot(xs, ys_r, "s--", color="#e42536", lw=1.8,
                label="model / RUNCARD (exact refill)")
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xlabel(r"boson $q_\mathrm{T}$ (GeV, bin centre)")
        ax.set_ylabel(r"residual $\times 10^4$")
        ax.set_title(f"$x_2$ = {x2},  $|Y|$ < 0.15", fontsize=12)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=9)
    fig.tight_layout()
    _save(fig, outdir, "scan_vs_template", meta)
    plt.close(fig)


def _safe(label):
    import re

    return re.sub(r"[^A-Za-z0-9]+", "_", label).strip("_")


# ------------------------------------------------------------------- main --
def analyse(npz, out=print):
    """Numbers, not pictures: the per-bin universal-coefficient test."""
    labels = list(npz["labels"])
    d, rr, delta = npz["d"], npz["rr"], npz["delta"]
    keep = [i for i, L in enumerate(labels) if group_of(L) not in N_MOVES_FO]
    x = np.stack([-delta * (rr[i] - 1.0) for i in keep])       # (K, nY, nT)
    y = np.stack([d[i] for i in keep])
    out("\nFLOOR TEST -- per bin, one coefficient C across the "
        f"{len(keep)} nonsingular-inert directions:")
    out(f"{'qT bin':>14} {'|Y| bin':>12} {'C':>9} {'R^2':>7} {'-Delta':>9} "
        f"{'rms resid':>11}")
    Te, Ye = npz["Te"], npz["Ye"]
    stats = []
    for iy in range(y.shape[1]):
        for it in range(y.shape[2]):
            # the free coefficient is on the RESPONSE, not the prediction, so
            # that C is directly comparable to -Delta
            xx = np.stack([(rr[i] - 1.0)[iy, it] for i in keep])
            yy = y[:, iy, it]
            ok = np.isfinite(xx) & np.isfinite(yy) & (np.abs(xx) > 1e-9)
            if ok.sum() < 4:
                continue
            C = float(np.sum(xx[ok] * yy[ok]) / np.sum(xx[ok] ** 2))
            resid = yy[ok] - C * xx[ok]
            ss = float(np.sum(yy[ok] ** 2))
            r2 = 1.0 - float(np.sum(resid**2)) / ss if ss > 0 else np.nan
            stats.append((it, iy, C, r2, -float(delta[iy, it]),
                          float(np.sqrt(np.mean(resid**2)))))
    for it, iy, C, r2, mD, rms in stats:
        out(f"[{Te[it]:5g},{Te[it+1]:5g}] [{Ye[iy]:4g},{Ye[iy+1]:4g}] "
            f"{C:9.4f} {r2:7.3f} {mD:9.4f} {rms:11.2e}")
    return stats


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--cache")
    ap.add_argument("--conf")
    ap.add_argument("--corr", nargs="+", default=[])
    ap.add_argument("--threads", type=int, default=64)
    ap.add_argument("--partial", action="store_true")
    ap.add_argument("--npz", help="where to write (compute) the residual maps")
    ap.add_argument("--from-npz", help="skip the calculation, plot this instead")
    ap.add_argument("--tol-npz", help="a second npz (different tolerance) to "
                                      "compare on the bins both cover")
    ap.add_argument("--tag-a", default="tol 1e-3 (210 bins)")
    ap.add_argument("--tag-b", default="tol 1e-4 (10 bins)")
    ap.add_argument("-o", "--out-dir")
    ap.add_argument("--map-labels", nargs="*", default=None)
    ap.add_argument("--scan-dir", help="directory of scan_*.json from "
                                       "transition_variation_scan.py")
    args = ap.parse_args()

    if args.from_npz is None:
        if not (args.cache and args.conf and args.corr and args.npz):
            raise SystemExit("compute needs --cache --conf --corr --npz")
        compute(args)
        if not args.out_dir:
            return
        args.from_npz = args.npz

    z = np.load(args.from_npz, allow_pickle=False)
    labels = list(z["labels"])
    Te, Ye = z["Te"], z["Ye"]
    meta = {
        "what": "model/template residual per (|Y|, qT) bin",
        "cache": str(z["cache"]),
        "npz": os.path.abspath(args.from_npz),
    }
    if args.out_dir:
        sel = args.map_labels or [L for L in labels]
        for L in sel:
            if L not in labels:
                print(f"   (no such direction: {L})")
                continue
            i = labels.index(L)
            plot_map(z["d"][i], Te, Ye, L, args.out_dir, meta)
            plot_profiles(z["d"][i], Te, Ye, L, args.out_dir, meta)
        plot_floor(z, args.out_dir, meta)
        # transition region (qT 18-44) and the gen-overflow bin
        plot_relacc(z, args.out_dir, meta, slice(15, 20),
                    r"$q_\mathrm{T}$ 18-44 GeV", "relacc_qt18_44")
        plot_relacc(z, args.out_dir, meta, slice(0, 15),
                    r"$q_\mathrm{T}$ < 18 GeV", "relacc_qt_lt18")
        plot_relacc(z, args.out_dir, meta, slice(20, 21),
                    r"$q_\mathrm{T}$ [44,100] GeV", "relacc_qt44_100")
        for nm, ls in (
            ("compare_transitions_vs_rest",
             ["transition_points0.2_0.35_1.0", "transition_points0.2_0.75_1.0",
              "transition_points0.3_0.6_0.9", "lambda21.0", "s1.", "b_qqV0.5",
              "pdfCT18ZNNLO_as_0120"]),
            ("compare_transitions_vs_scales",
             ["transition_points0.2_0.35_1.0", "transition_points0.3_0.6_0.9",
              "mufup", "mufdown", "kappaFO0.5-kappaf2.",
              "pdfCT18ZNNLO_as_0120"]),
        ):
            keep = [L for L in ls if L in labels]
            plot_compare(z, keep, Te, args.out_dir, nm, meta)
        if args.scan_dir:
            plot_scan_overlay(z, args.scan_dir, args.out_dir, meta)
    analyse(z)

    if args.tol_npz and args.out_dir:
        b = np.load(args.tol_npz, allow_pickle=False)
        common = [L for L in list(b["labels"]) if L in labels]
        # transitions first: they are the reason this comparison exists
        want = [L for L in common if group_of(L) == "transition"] + [
            L for L in common if group_of(L) == "lambda"]
        plot_tolerance(z, b, want[:4], args.out_dir, meta, args.tag_a, args.tag_b)
        print(f"\nTOLERANCE COMPARISON on the {b['d'].shape[1]}x"
              f"{b['d'].shape[2]} shared bins:")
        iy = [int(np.argmin(np.abs(Ye - v))) for v in b["Ye"][:-1]]
        it = [int(np.argmin(np.abs(Te - v))) for v in b["Te"][:-1]]
        print(f"{'direction':<32} {'max|d| A':>10} {'max|d| B':>10} "
              f"{'rms A':>10} {'rms B':>10} {'B/A rms':>9}")
        for L in common:
            da = z["d"][labels.index(L)][np.ix_(iy, it)]
            db = b["d"][list(b["labels"]).index(L)]
            ra = float(np.sqrt(np.nanmean(da**2)))
            rb = float(np.sqrt(np.nanmean(db**2)))
            print(f"{L:<32} {np.nanmax(np.abs(da)):10.2e} "
                  f"{np.nanmax(np.abs(db)):10.2e} {ra:10.2e} {rb:10.2e} "
                  f"{rb/ra if ra else np.nan:9.2f}")


if __name__ == "__main__":
    main()
