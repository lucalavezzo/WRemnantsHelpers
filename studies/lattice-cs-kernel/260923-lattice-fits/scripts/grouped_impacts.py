"""Print alpha_s grouped impacts (traditional + global) x 1e-3 from fitresults, side by side.
Reads the fitresult's own impacts_grouped / global_impacts_grouped (what rabbit_plot_pulls_and_impacts.py plots).
Impacts are in theta units of alphaS; x width 0.002 -> physical; x1e3 -> units of 1e-3.
"""

import sys, json
import numpy as np
from rabbit import io_tools

W = 0.002
out = {}
for tok in sys.argv[1:]:
    tag, path = tok.split("=", 1)
    r = io_tools.get_fitresult(path)
    d = {}
    for key in ("impacts_grouped", "global_impacts_grouped"):
        h = r[key].get()
        ax0 = [str(x.decode() if isinstance(x, bytes) else x) for x in h.axes[0]]
        ax1 = [str(x.decode() if isinstance(x, bytes) else x) for x in h.axes[1]]
        i = ax0.index("alphaS")
        vals = h.values()[i]
        d[key] = {g: float(v) * W * 1e3 for g, v in zip(ax1, vals)}
    parms = r["parms"].get()
    names = [str(n.decode() if isinstance(n, bytes) else n) for n in parms.axes[0]]
    d["sigma_alphaS_1e3"] = (
        float(np.sqrt(parms.variances()[names.index("alphaS")])) * W * 1e3
    )
    out[tag] = d
groups = sorted(
    set().union(*[set(v["impacts_grouped"]) for v in out.values()]),
    key=lambda g: -max(out[t]["global_impacts_grouped"].get(g, 0) for t in out),
)
tags = list(out)
hdr = (
    "group".ljust(28)
    + "".join(f"{t+' trad':>18s}" for t in tags)
    + "".join(f"{t+' glob':>18s}" for t in tags)
)
print(hdr)
for g in groups:
    print(
        g.ljust(28)
        + "".join(
            f"{out[t]['impacts_grouped'].get(g, float('nan')):18.3f}" for t in tags
        )
        + "".join(
            f"{out[t]['global_impacts_grouped'].get(g, float('nan')):18.3f}"
            for t in tags
        )
    )
print(
    "sigma(alphaS)".ljust(28)
    + "".join(f"{out[t]['sigma_alphaS_1e3']:18.3f}" for t in tags)
)
# A (believed) disjoint top-level partition; the card groups nest (experiment > expNoCalib > ..., theory > theory_ew ...),
# so a quadrature sum over ALL groups is meaningless. NaN entries (global stat on some fits) are skipped and flagged.
PART = [
    "stat",
    "binByBinStat",
    "experiment",
    "pdfEig",
    "resumTNP",
    "resumNonpert",
    "resumScale",
    "resumTransition",
    "theory_ew",
    "theory_qcd",
    "bcQuarkMass",
    "widthZ",
    "sin2thetaZ",
    "massShift",
    "CMS_background",
]
for t in tags:
    for key in ("impacts_grouped", "global_impacts_grouped"):
        gl = out[t][key]
        vals = [gl.get(g, np.nan) for g in PART]
        nan = [g for g, v in zip(PART, vals) if not np.isfinite(v)]
        q = np.sqrt(np.nansum(np.square(vals)))
        print(
            f"[{t}] {key:24s} quadrature over partition = {q:.3f}  sigma = {out[t]['sigma_alphaS_1e3']:.3f}  ratio {q/out[t]['sigma_alphaS_1e3']:.3f}"
            + (f"  (NaN skipped: {nan})" if nan else "")
        )
import os

json.dump(
    out,
    open(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "grouped_impacts.json",
        ),
        "w",
    ),
    indent=1,
)
