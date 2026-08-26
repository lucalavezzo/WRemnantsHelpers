#!/usr/bin/env python3
"""Closure against the production CorrZ templates, 3 knots vs 5, from ONE cache.

Reuses scripts/rabbit/scetlib_ad/validate_variations.py -- its variation map,
its reference loading, its bin merging and its plot -- and adds exactly one
thing: it evaluates the model TWICE, with the muF stencil clamped to the outer
pair and with all of it, so the two arms differ by the interpolation order and
by nothing else. Everything downstream (which bins, how |Y| is summed, how the
ratio is formed) is the upstream script's.

Per direction it writes the standard per-direction plot for each arm into
<out>/knots3 and <out>/knots5, and for the directions named by --overlay one
figure with BOTH arms against the template, which is the before/after the
proposal has to be judged on.
"""
import argparse
import os
import re
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)
sys.path.insert(0, os.path.join(WREM, "scripts", "rabbit", "scetlib_ad"))

import validate_variations as vv  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corr", required=True, nargs="+")
    ap.add_argument("--cache", required=True)
    ap.add_argument("--conf", required=True)
    ap.add_argument("--threads", type=int, default=32)
    ap.add_argument("--out", required=True)
    ap.add_argument("--overlay", nargs="*", default=None,
                    help="directions to draw both arms on one figure "
                         "(default: the three transition directions)")
    args = ap.parse_args()

    import scetlib_qT
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
    print(f"model grid: |Y| {Ye.size-1} bins [{Ye[0]:g}, {Ye[-1]:g}], "
          f"qT {Te.size-1} bins [{Te[0]:g}, {Te[-1]:g}]")

    fold = core.fold_for([("ptVGen", Te), ("absYVGen", Ye)], b[0, 0], b[0, 1],
                         partial=True)
    cover = fold.covered_mask.T
    print(f"   {int(cover.sum())} of {cover.size} gen cells covered "
          f"({int((~cover).sum())} excluded)")
    anchor = core.anchor.copy()

    def set_arm(used):
        """Select the muF stencil AND drop the value cache.

        THE TRAP: ScetlibCachedXsecTF.values_and_jacobian memoises on the
        PARAMETER VECTOR alone (scetlib_tf.py, `self._cache_key = p.tobytes()`).
        The knot count is not part of that key, so evaluating the two arms
        back to back at the same p returns the FIRST arm's numbers for both --
        and the A/B then shows a perfect null, which is exactly what a
        no-effect change would show. Caught here by the kappa_F = sqrt(2)
        probe, which must differ between the arms and did not.
        """
        scetlib_qT.DrellYan.set_muf_knots_used(used)
        core.tf_fn._cache_key = None
        core.tf_fn._hess_cache_key = None

    def model(overrides):
        p = anchor.copy()
        for k, val in overrides.items():
            if k not in names:
                return None
            p[names.index(k)] = val
        vals_, _ = core.values_and_jacobian(p)
        return fold(np.asarray(vals_, float)).reshape(Te.size - 1,
                                                      Ye.size - 1).T

    ARMS = ((2, "knots3", "3-knot (shipped)"), (0, "knots5", "5-knot"))
    cen = {}
    for used, tag, _ in ARMS:
        set_arm(used)
        cen[tag] = model({})
    # The anchor must be identical: at the anchor every member weight is zero
    # and the interpolant returns the stored central. If this is not ~0 the
    # clamp is doing more than clamping.
    dcen = np.nanmax(np.abs(cen["knots5"] / cen["knots3"] - 1.0))
    print(f"   central 5-knot/3-knot - 1, max over bins: {dcen:.3e} "
          f"(must be ~0: the anchor is not interpolated)")
    # LIVE CHECK that the two arms really are two arms. kappa_F = sqrt(2) is a
    # knot of the five-knot stencil only, so the arms MUST differ there; if they
    # do not, the value cache (see set_arm) is serving one arm's numbers to both
    # and every number below would be a spurious null.
    probe = {}
    for used, tag, _ in ARMS:
        set_arm(used)
        probe[tag] = model({"scale_kappa_F": float(np.sqrt(2.0))}) / cen[tag]
    sep = float(np.nanmax(np.abs(probe["knots5"] / probe["knots3"] - 1.0)))
    print(f"   ARM SEPARATION probe, kappa_F = sqrt(2): "
          f"max|5-knot/3-knot - 1| = {sep:.3e}")
    if not sep > 1e-6:
        raise SystemExit(
            "the two arms are identical at kappa_F = sqrt(2), which is a knot "
            "of one stencil and not the other. The clamp or the value cache is "
            "not doing what this script assumes; refusing to report a null.")

    overlay = args.overlay
    if overlay is None:
        overlay = ["transition_points0.2_0.35_1.0",
                   "transition_points0.2_0.75_1.0",
                   "transition_points0.3_0.6_0.9"]

    rows = []
    for path in args.corr:
        h = vv.load_corr(path)
        ax = {a.name: a for a in h.axes}
        labels = [str(x) for x in ax["vars"]]
        vals = np.asarray(h.values(flow=False))
        dims = [a.name for a in h.axes]
        iQ, ich = dims.index("Q"), dims.index("charge")
        vals = np.squeeze(vals, axis=(iQ, ich))
        order = [d for d in dims if d not in ("Q", "charge")]
        vals = np.moveaxis(vals, [order.index("absY"), order.index("qT"),
                                  order.index("vars")], [0, 1, 2])
        MY = vv.merge_matrix(ax["absY"].edges, Ye, "absY")
        MT = vv.merge_matrix(ax["qT"].edges, Te, "qT")

        def ref(label):
            return MY @ vals[:, :, labels.index(label)] @ MT.T

        cen_lab = vv.central_label(labels)
        r_cen = ref(cen_lab)
        for L in labels:
            if L == cen_lab:
                continue
            ov = vv.variation_for(L)
            if ov is None or any(k not in names for k in ov):
                continue
            rr = ref(L) / r_cen
            rr1 = ref(L).sum(axis=0) / r_cen.sum(axis=0)
            per_arm = {}
            for used, tag, _ in ARMS:
                set_arm(used)
                s_var = model(ov)
                rm = s_var / cen[tag]
                good = np.isfinite(rm) & np.isfinite(rr) & (rr != 0) & cover
                dev = np.abs(rm[good] / rr[good] - 1.0)
                per_arm[tag] = dict(
                    maxdev=float(dev.max()), meandev=float(dev.mean()),
                    r1=s_var.sum(axis=0) / cen[tag].sum(axis=0))
            rows.append((L, per_arm, rr1, os.path.basename(path)))

    scetlib_qT.DrellYan.set_muf_knots_used(0)

    print(f"\n{'variation':<34}{'3-knot max|dev|':>17}{'5-knot max|dev|':>17}"
          f"{'ratio':>9}   {'3-knot mean':>12}{'5-knot mean':>13}")
    for L, pa, _, _ in rows:
        a, bq = pa["knots3"]["maxdev"], pa["knots5"]["maxdev"]
        print(f"{L:<34}{a:>17.3e}{bq:>17.3e}{(bq / a if a else np.nan):>9.2f}"
              f"   {pa['knots3']['meandev']:>12.3e}{pa['knots5']['meandev']:>13.3e}")

    os.makedirs(args.out, exist_ok=True)
    _plots(rows, Te, args, overlay)


def _plots(rows, Te, args, overlay):
    import hist

    from wums import output_tools, plot_tools

    def h1(v):
        hh = hist.Hist(hist.axis.Variable(Te, name="qT", overflow=False,
                                          underflow=False),
                       storage=hist.storage.Double())
        hh.view(flow=False)[...] = np.asarray(v, float)
        return hh

    for L, pa, rr1, src in rows:
        for tag, lab in (("knots3", "3-knot (shipped)"), ("knots5", "5-knot")):
            d = os.path.join(args.out, tag)
            vv.plot_response(
                L, Te, pa[tag]["r1"], rr1, d,
                {"variation": L, "muF stencil": lab,
                 "reference": src, "cache": os.path.basename(args.cache),
                 "both curves": "variation / central (a RESPONSE, not a xsec)",
                 "max|model/template - 1| (covered bins)":
                     f"{pa[tag]['maxdev']:.3e}",
                 "mean|.|": f"{pa[tag]['meandev']:.3e}"})
        if L not in overlay:
            continue
        dev = max(float(np.max(np.abs(np.asarray(rr1) - 1.0))),
                  float(np.max(np.abs(np.asarray(pa["knots3"]["r1"]) - 1.0))),
                  float(np.max(np.abs(np.asarray(pa["knots5"]["r1"]) - 1.0))))
        pad = max(1.2 * dev, 2.0e-3)
        fig = plot_tools.makePlotWithRatioToRef(
            [h1(rr1), h1(pa["knots3"]["r1"]), h1(pa["knots5"]["r1"])],
            labels=[f"template  {L}", "model  3-knot $\\mu_F$ (shipped)",
                    "model  5-knot $\\mu_F$"],
            ylim=[1.0 - pad, 1.0 + pad],
            logoPos=0,
            colors=["#5790fc", "#e42536", "#f89c20"],
            linestyles=["solid", "dashed", "dashdot"],
            xlabel=r"boson $q_\mathrm{T}$ (GeV)",
            ylabel=r"$\sigma_\mathrm{var}/\sigma_\mathrm{central}$",
            rlabel=["model / template"],
            rrange=[[0.995, 1.005]],
            binwnorm=None, logy=False, yerr=False, nlegcols=1,
            cms_label="Work in progress", grid=True)
        safe = re.sub(r"[^A-Za-z0-9]+", "_", L).strip("_")
        plot_tools.save_pdf_and_png(args.out, f"ab_{safe}", fig=fig)
        output_tools.write_index_and_log(
            args.out, f"ab_{safe}",
            analysis_meta_info={
                "variation": L, "reference": src,
                "cache": os.path.basename(args.cache),
                "arms": "one cache, DrellYan.set_muf_knots_used(2) vs all",
                "3-knot max|dev|": f"{pa['knots3']['maxdev']:.3e}",
                "5-knot max|dev|": f"{pa['knots5']['maxdev']:.3e}"},
            args=None)


if __name__ == "__main__":
    main()
