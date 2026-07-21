#!/usr/bin/env python3
"""Nonsingular (and FO, singular) as fraction of the MATCHED prediction vs qT,
0.5-GeV bins, low qT. Matched (N3+0LL+N2LO, qtCutoff=1) density interpolated
from its native 1-GeV grid (smooth, positive -> safe denominator everywhere).
NOTE: not makePlotWithRatioToRef — curves at -3% and +300% of matched cannot
share one wums ratio panel; two-panel matplotlib with CMS colors instead."""

import numpy as np, glob, os, sys
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wremnants.utilities.io_tools import input_tools

Z = "/ceph/submit/data/user/l/lavezzo/zstuff"
R3 = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_combined.pkl"
S2 = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse_nnlo_sing/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_nnlo_sing_combined.pkl"
FINE = glob.glob(
    "/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_n3+0ll_fine_nnlo_sing/*combined.pkl"
)[0]
DY = "/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-MSHT20aN3LO-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-MSHT20an3lo_as118-{scale}-scetlibmatch.txt"
OUT = os.path.expanduser("~/public_html/alphaS/260714_fo_vs_matched")


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


# matched, native 1-GeV
hm = input_tools.read_matched_scetlib_dyturbo_hist(
    R3,
    S2,
    DY,
    axes=("Q", "Y", "qT"),
    charge=0,
    zero_nons_bins=slice(0j, complex(0, 1.0)),
)
mv, qm = prof(hm)
mdens = mv / np.diff(qm.edges)
mcent = qm.centers
# fine singular + dyturbo, native 0.5-GeV
hs = input_tools.read_scetlib_hist(FINE, charge=0)[
    {"Q": slice(complex(0, 60), complex(0, 120))}
]
sv, qs = prof(hs)
hd = input_tools.read_dyturbo_vars_hist(
    DY, var_axis=hs.axes["vars"], axes=("Q", "Y", "qT"), charge=0
)
hd = hd[{"Q": slice(complex(0, 60), complex(0, 120)), "vars": "pdf0"}]
dv, qd = prof(hd)
assert np.allclose(qs.edges, qd.edges)
nb = int(np.searchsorted(qs.edges, 10.0))
e = qs.edges[: nb + 1]
w = np.diff(e)
x = 0.5 * (e[:-1] + e[1:])
fo = dv[:nb] / w
si = sv[:nb] / w
ns = fo - si
md = np.interp(x, mcent, mdens)
B, G, R = "#5790fc", "#9c9ca1", "#e42536"
M = "#964a8b"
fig, (a1, a2) = plt.subplots(
    2, 1, figsize=(8, 8), sharex=True, gridspec_kw={"hspace": 0.07}
)
a1.step(x, fo / md * 100, where="mid", color=M, lw=2, label=r"FO N$^2$LO (DYTurbo)")
a1.step(
    x,
    si / md * 100,
    where="mid",
    color=B,
    lw=2,
    ls="--",
    label=r"singular $\mathcal{O}(\alpha_s^2)$",
)
a1.axhline(100, color="gray", lw=0.6, ls=":")
a1.axhline(0, color="gray", lw=0.6)
a1.axvline(1, color="gray", lw=1, ls="--")
a1.set_ylim(-1000, 600)
a1.set_ylabel("x / matched  [%]")
a1.legend(fontsize=11, loc="lower right")
a1.set_title(
    r"Low-$q_T$ pieces vs matched N$^{3+0}$LL+N$^2$LO — Z, $|Y|<2.5$, 0.5 GeV bins"
)
ABS = "abs" in sys.argv[1:]
if ABS:
    a2.step(x, ns, where="mid", color=R, lw=2, label=r"nonsingular (FO $-$ sing)")
    a2.set_ylim(-3, 2)
    a2.set_ylabel(r"FO $-$ sing  [pb/GeV]")
    for xx, yy in [(0.25, ns[0]), (0.75, ns[1])]:
        if abs(yy) > 3:
            a2.annotate(f"{yy:+.0f}", (xx, 1.6), fontsize=8, color=R, ha="center")
else:
    a2.step(
        x,
        ns / md * 100,
        where="mid",
        color=R,
        lw=2,
        label=r"nonsingular (FO $-$ sing) / matched",
    )
    a2.set_ylim(-6, 2)
    a2.set_ylabel("nonsingular / matched  [%]")
    for xx, yy in [(0.25, ns[0] / md[0] * 100), (0.75, ns[1] / md[1] * 100)]:
        if yy > 2:
            a2.annotate(f"+{yy:.0f}%", (xx, 1.6), fontsize=8, color=R, ha="center")
a2.axhline(0, color="gray", lw=0.7)
a2.axvline(1, color="gray", lw=1, ls="--")
a2.text(1.05, a2.get_ylim()[0] * 0.9, "qtCutoff", fontsize=9, color="gray")
a2.set_xlim(0, 10)
a2.set_xlabel(r"$q_T$ [GeV]")
a2.legend(fontsize=11, loc="lower right")
for ext in ("png", "pdf"):
    fig.savefig(
        f"{OUT}/nonsingular_frac_lowqt{"_abs" if ABS else ""}.{ext}",
        dpi=150,
        bbox_inches="tight",
    )
with open(f"{OUT}/nonsingular_frac_lowqt.log", "w") as L:
    L.write("script: studies/nnlojet-lowqt-cut/fo_nonsingular_frac_lowqt.py\n")
print("saved")
for i in range(nb):
    print(f"{e[i]:4.1f}-{e[i+1]:<4.1f}: nons/matched = {ns[i]/md[i]*100:+7.2f}%")
