#!/usr/bin/env python3
"""The transition-point variation, model vs an EXACT reference, at two muF knot
spacings -- same figure format as validate_variations.py's per-direction plot.

Top panel:    sigma(var)/sigma(anchor), the RESPONSE.
Bottom panel: model / reference.

The reference here is the RUNCARD route, not the CorrZ template: the transition
points are written into the card and the beam convolutions are REFILLED at the
shifted muF, so it is the same calculation with the interpolation removed. That
makes the ratio panel OUR error alone -- the template carries a different
nonsingular and possibly a different matching, which would enter a template
comparison as well.

REGIME. These are FINITE variations at the size the production templates carry
(x2 = 0.35 and 0.75 against an anchor of 0.6), not the near-anchor derivative a
fit uses. The two scale differently with the knot spacing and must not be
quoted for each other.
"""
import argparse
import json
import os

import numpy as np

QT_EDGES = [18.0, 20.0, 24.0, 28.0, 33.0, 44.0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", nargs="+", required=True,
                    help="knot_interp_error JSONs, one per knot spacing")
    ap.add_argument("--label", nargs="+", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    import hist

    from wums import output_tools, plot_tools

    ds = [json.load(open(p)) for p in args.json]
    b = np.asarray(ds[0]["bins"], float)
    Te = np.asarray(QT_EDGES, float)
    assert np.allclose(b[:, 4], Te[:-1]), (b[:, 4], Te)

    def h1(v):
        h = hist.Hist(hist.axis.Variable(Te, name="qT", overflow=False,
                                         underflow=False),
                      storage=hist.storage.Double())
        h.view(flow=False)[...] = np.asarray(v, float)
        return h

    ref = np.asarray(ds[0]["run_var"], float) / np.asarray(ds[0]["par_cen"], float)
    for d in ds[1:]:
        r2 = np.asarray(d["run_var"], float) / np.asarray(d["par_cen"], float)
        if np.max(np.abs(r2 / ref - 1.0)) > 5e-4:
            print("WARNING: the runcard references differ between arms by "
                  f"{np.max(np.abs(r2/ref-1)):.2e}")
    hists = [h1(ref)] + [h1(np.asarray(d["par_var"], float)
                            / np.asarray(d["par_cen"], float)) for d in ds]
    labels = ["exact (runcard refill)"] + list(args.label)
    dev = max(float(np.max(np.abs(np.asarray(h.values(), float) - 1.0)))
              for h in hists)
    pad = max(1.35 * dev, 4.0e-3)
    rmax = 0.0
    for h in hists[1:]:
        rmax = max(rmax, float(np.max(np.abs(
            np.asarray(h.values(), float) / ref - 1.0))))
    rpad = max(1.35 * rmax, 2e-4)
    fig = plot_tools.makePlotWithRatioToRef(
        hists, labels=labels,
        ylim=[1.0 - pad, 1.0 + pad],
        logoPos=0,
        colors=["#5790fc", "#e42536", "#f89c20", "#964a8b"][: len(hists)],
        linestyles=["solid", "dashed", "dotted", "dashdot"][: len(hists)],
        xlabel=r"boson $q_\mathrm{T}$ (GeV)",
        ylabel=r"$\sigma_\mathrm{var}/\sigma_\mathrm{central}$",
        rlabel=["model / exact"],
        rrange=[[1.0 - rpad, 1.0 + rpad]],
        binwnorm=None, logy=False, yerr=False, nlegcols=1,
        cms_label="Work in progress", grid=True,
    )
    os.makedirs(args.outdir, exist_ok=True)
    plot_tools.save_pdf_and_png(args.outdir, args.name, fig=fig)
    meta = {
        "variation": args.title,
        "reference": "EXACT runcard refill (transition written into the card, "
                     "beam convolutions rebuilt at the shifted muF) -- NOT the "
                     "CorrZ template",
        "regime": "FINITE variation, the size the production templates carry; "
                  "NOT the near-anchor derivative",
        "bins": "|Y| in [0, 0.15], Q in [60, 120], the card's own qT bins "
                "18-44 (the transition response is identically zero below 16)",
        "build": "scetlib-nak = bb2e7cb + 92f1299 (muF member coordinate fix) "
                 "+ e61a8d0 (settable muF knot spacing)",
        "caution": "qT [18,20] has a true response of 4e-4 or less, at the "
                   "node-ladder target -- do not diagnose on it",
    }
    for p, L in zip(args.json, args.label):
        d = json.load(open(p))
        e = [(np.asarray(d["par_var"], float) / np.asarray(d["par_cen"], float)
              - np.asarray(d["run_var"], float) / np.asarray(d["par_cen"], float))
             / (np.asarray(d["run_var"], float) / np.asarray(d["par_cen"], float)
                - 1.0)]
        meta[f"error/true response, {L}"] = ", ".join(
            f"[{int(b[k,4])},{int(b[k,5])}] {100*e[0][k]:+.1f}%"
            for k in range(len(b)))
    output_tools.write_index_and_log(args.outdir, args.name,
                                     analysis_meta_info=meta, args=None)
    print(f"wrote {args.outdir}/{args.name}.png")


if __name__ == "__main__":
    main()
