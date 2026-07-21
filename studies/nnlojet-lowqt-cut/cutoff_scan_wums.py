"""qtCutoff 1..5 scan on the N3+0LL+NNLO matched spectrum — wums-styled ratio plot."""

import numpy as np, os, hist
import matplotlib

matplotlib.use("Agg")
from wremnants.utilities.io_tools import input_tools
from wums import plot_tools, output_tools

Z = "/ceph/submit/data/user/l/lavezzo/zstuff"
RESUM = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_combined.pkl"
SING = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse_nnlo_sing/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_nnlo_sing_combined.pkl"
FO = "/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-MSHT20aN3LO-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-MSHT20an3lo_as118-{scale}-scetlibmatch.txt"
OUT = os.path.expanduser("~/public_html/alphaS/260714_fo_vs_matched")


def prof(h):
    hc = h[{"vars": "pdf0"}]
    names = hc.axes.name
    v = hc.values()
    keep = [names.index("Y"), names.index("qT")]
    v = v.sum(axis=tuple(i for i in range(v.ndim) if i not in keep))
    if names.index("Y") > names.index("qT"):
        v = v.T
    yax = hc.axes["Y"]
    return v[yax.index(-2.5) : yax.index(2.5)].sum(axis=0), hc.axes["qT"]


hists = []
labels = []
for X in (1, 2, 3, 4, 5):
    hm = input_tools.read_matched_scetlib_dyturbo_hist(
        RESUM,
        SING,
        FO,
        axes=("Q", "Y", "qT"),
        charge=0,
        zero_nons_bins=slice(0j, complex(0, float(X))),
    )
    v, qt = prof(hm)
    h1 = hist.Hist(
        hist.axis.Variable(qt.edges, name="qT"), storage=hist.storage.Double()
    )
    h1[...] = v
    hists.append(h1[{"qT": slice(0j, 20j)}])
    labels.append("nominal (1 GeV)" if X == 1 else f"{X} GeV")

fig = plot_tools.makePlotWithRatioToRef(
    hists,
    labels,
    colors=["#5790fc", "#f89c20", "#e42536", "#964a8b", "#7a21dd"],
    xlabel=r"$q_T$ [GeV]",
    ylabel="d$\\sigma$/d$q_T$ [pb/GeV]",
    rlabel="x/nominal",
    rrange=[0.995, 1.035],
    nlegcols=1,
    binwnorm=1.0,
    baseline=True,
    legtext_size=20,
    extra_text=["qtCutoff scan", "N$^{3+0}$LL+NNLO", "SCETlib+DYTurbo", "Z, $|Y|<2.5$"],
    extra_text_loc=(0.05, 0.92),
    yscale=1.35,
    ratio_legend=False,
    xlim=(0, 20),
)
name = "cutoff_scan_n3ll_nnlo_wums"
plot_tools.save_pdf_and_png(OUT, name)
try:
    output_tools.write_index_and_log(OUT, name)
except Exception as e:
    print("write_index_and_log:", e)
print("saved", OUT + "/" + name)
