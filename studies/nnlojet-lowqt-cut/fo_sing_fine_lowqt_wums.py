#!/usr/bin/env python3
"""Fine (0.5 GeV) low-qT comparison: DYTurbo N2LO FO vs O(as^2) singular
(com13_msht20an3lo_n3+0ll_fine_nnlo_sing, validated == blessed coarse after
Q slice to 60-120). |Y|<2.5, pdf0. Shows the qT->0 cancellation structure."""

import numpy as np, glob, os, hist
import matplotlib

matplotlib.use("Agg")
from wremnants.utilities.io_tools import input_tools
from wums import plot_tools, output_tools

FINE = glob.glob(
    "/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_n3+0ll_fine_nnlo_sing/*combined.pkl"
)[0]
DY = "/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-MSHT20aN3LO-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-MSHT20an3lo_as118-{scale}-scetlibmatch.txt"
OUT = os.path.expanduser("~/public_html/alphaS/260714_fo_vs_matched")
QMAX = 10


def prof(h):
    hc = h[{"vars": 0}] if "vars" in h.axes.name else h
    names = hc.axes.name
    v = hc.values()
    keep = [names.index("Y"), names.index("qT")]
    v = v.sum(axis=tuple(i for i in range(v.ndim) if i not in keep))
    if names.index("Y") > names.index("qT"):
        v = v.T
    yax = hc.axes["Y"]
    return v[yax.index(-2.5) : yax.index(2.5)].sum(axis=0), hc.axes["qT"]


hs = input_tools.read_scetlib_hist(FINE, charge=0)
hs = hs[{"Q": slice(complex(0, 60), complex(0, 120))}]
sv, qs = prof(hs)
hdum = input_tools.read_dyturbo_vars_hist(
    DY, var_axis=hs.axes["vars"], axes=("Q", "Y", "qT"), charge=0
)
hdum = hdum[{"Q": slice(complex(0, 60), complex(0, 120)), "vars": "pdf0"}]
names = hdum.axes.name
v = hdum.values()
keep = [names.index("Y"), names.index("qT")]
v = v.sum(axis=tuple(i for i in range(v.ndim) if i not in keep))
if names.index("Y") > names.index("qT"):
    v = v.T
yax = hdum.axes["Y"]
dv = v[yax.index(-2.5) : yax.index(2.5)].sum(axis=0)
qd = hdum.axes["qT"]
assert np.allclose(qs.edges, qd.edges), "grids differ"
nb = int(np.searchsorted(qs.edges, QMAX))
ax = hist.axis.Variable(qs.edges[: nb + 1], name="qT")


def mk(vals):
    h = hist.Hist(ax, storage=hist.storage.Weight())
    h.values()[...] = vals[:nb]
    h.variances()[...] = 0.0
    return h


fig = plot_tools.makePlotWithRatioToRef(
    [mk(dv), mk(sv), mk(dv - sv)],
    [
        r"FO N$^2$LO (DYTurbo)",
        r"singular $\mathcal{O}(\alpha_s^2)$ (SCETlib)",
        r"nonsingular (FO $-$ sing)",
    ],
    colors=["#964a8b", "#5790fc", "#e42536"],
    linestyles=["solid", "dashed", "solid"],
    xlabel=r"$q_T$ [GeV]",
    ylabel=r"d$\sigma$/d$q_T$ [pb/GeV]",
    rlabel="x/FO",
    rrange=[0.9, 1.1],
    nlegcols=1,
    binwnorm=1.0,
    baseline=True,
    yerr=False,
    logy=False,
    legtext_size=15,
    extra_text=["0.5 GeV bins", "Z, $|Y|<2.5$", "$60<Q<120$ GeV"],
    extra_text_loc=(0.72, 0.35),
    xlim=(0, QMAX),
    ratio_legend=False,
)
name = "fo_sing_fine_lowqt_wums"
plot_tools.save_pdf_and_png(OUT, name)
try:
    output_tools.write_index_and_log(OUT, name)
except Exception as e:
    print(e)
print("saved")
print(f"{'bin':>9} | {'FO':>9} | {'sing':>9} | {'nons':>8} | nons/FO")
for i in range(nb):
    a, b = qs.edges[i], qs.edges[i + 1]
    print(
        f"{a:4.1f}-{b:<4.1f} | {dv[i]/(b-a):9.2f} | {sv[i]/(b-a):9.2f} | {(dv[i]-sv[i])/(b-a):8.2f} | {(dv[i]-sv[i])/dv[i]*100:+6.2f}%"
    )
