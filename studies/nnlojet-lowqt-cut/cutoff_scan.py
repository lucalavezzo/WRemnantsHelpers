"""Matched (N3+0LL + NNLO dyturbo) spectrum with qtCutoff = 1..5 GeV:
ratio to the cutoff=1 baseline per qT bin + integral shifts. |Y|<2.5, Q 60-120, pdf0."""

import numpy as np, os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wremnants.utilities.io_tools import input_tools

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
    return v[yax.index(-2.5) : yax.index(2.5)].sum(axis=0)


cuts = [1, 2, 3, 4, 5]
spectra = {}
for X in cuts:
    h = input_tools.read_matched_scetlib_dyturbo_hist(
        RESUM,
        SING,
        FO,
        axes=("Q", "Y", "qT"),
        charge=0,
        zero_nons_bins=slice(0j, complex(0, float(X))),
    )
    spectra[X] = prof(h)
    qt = h.axes["qT"]
base = spectra[1]
x = qt.centers
edges = qt.edges
fig, ax = plt.subplots(figsize=(8, 5.5))
for X in cuts[1:]:
    ax.step(
        x, (spectra[X] / base - 1) * 100, where="mid", lw=2, label=f"qtCutoff = {X} GeV"
    )
ax.axhline(0, color="gray", lw=0.8)
ax.set_xlim(0, 20)
ax.set_ylim(-1, 6)
ax.set_xlabel(r"$q_T$ [GeV]")
ax.set_ylabel("change vs qtCutoff = 1 GeV  [%]")
ax.set_title(r"Matched N$^{3+0}$LL+NNLO vs nonsingular cutoff, Z, $|Y|<2.5$")
ax.legend(fontsize=9)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/cutoff_scan_n3ll_nnlo.{ext}", dpi=150, bbox_inches="tight")
print(
    f"{'cut':>4} | {'per-bin shifts in affected bins':>34} | {'d sigma(qT<10)':>13} | {'d sigma(qT<20)':>13} | {'d sigma(all)':>12}"
)
for X in cuts[1:]:
    r = spectra[X] / base - 1
    shifts = " ".join(
        f"{r[i]*100:+.2f}%" for i in range(len(qt)) if edges[i] < X and edges[i] >= 1
    )

    def integ(hi):
        ix = qt.index(hi)
        return (spectra[X][:ix].sum() / base[:ix].sum() - 1) * 100

    tot = (spectra[X].sum() / base.sum() - 1) * 100
    print(
        f"{X:>4} | {shifts:>34} | {integ(10):+12.3f}% | {integ(20):+12.3f}% | {tot:+11.3f}%"
    )
