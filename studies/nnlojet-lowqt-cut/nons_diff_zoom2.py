"""3-panel low-qT zoom: (1) components of BOTH matchings, (2) nonsingulars, (3) difference."""

import numpy as np, glob, re, os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wremnants.utilities.io_tools import input_tools
from wums import boostHistHelpers as hh

Z = "/ceph/submit/data/user/l/lavezzo/zstuff"
R4 = f"{Z}/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_newvals_coarse_combined.pkl"
S3 = f"{Z}/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Newvals_Coarse_n3lo_sing/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_newvals_coarse_n3lo_sing_combined.pkl"
R3 = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_combined.pkl"
S2 = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse_nnlo_sing/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_nnlo_sing_combined.pkl"
DY = "/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-MSHT20aN3LO-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-MSHT20an3lo_as118-{scale}-scetlibmatch.txt"
NJ = "/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2/result/final/nnlo.ptz"
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


def two_pass(fn, *a, **k):
    hm = fn(*a, zero_nons_bins=slice(0j, complex(0, 1.0)), **k)
    hr = fn(*a, zero_nons_bins=slice(0j, complex(0, 500.0)), **k)
    m, qt = prof(hm)
    r, _ = prof(hr)
    return m, r, qt


m3, r3, qt3 = two_pass(
    input_tools.read_matched_scetlib_nnlojet_hist,
    R4,
    S3,
    NJ,
    ("Q", "Y", "qT"),
    0,
    mass_edges=[60, 120],
)
m2, r2, qt2 = two_pass(
    input_tools.read_matched_scetlib_dyturbo_hist, R3, S2, DY, ("Q", "Y", "qT"), 0
)
nons3 = m3 - r3
nons2v = m2 - r2
# dyturbo FO + a2 singular, production readers/rebinning
hr2_, hs2_ = input_tools.read_scetlib_resum_and_fosing(
    R3, S2, ("Q", "Y", "qT"), charge=0, coeff=None
)
hf2_ = input_tools.read_dyturbo_vars_hist(
    DY, var_axis=hs2_.axes["vars"], axes=("Q", "Y", "qT"), charge=0
)
hf2_ = hf2_[
    {"Q": slice(complex(0, 60), complex(0, 120))}
]  # drop the 10<Q<60 gamma* bin
for ax in ["Y", "Q", "qT"]:
    hf2_, hs2_, hr2_ = hh.rebinHistsToCommon([hf2_, hs2_, hr2_], ax)
f2, qtf2 = prof(hf2_)
s2, _ = prof(hs2_)
# NNLOJET FO + stat on qt3 grid
fv = {}
fe2 = {}


def num(x):
    return float(x.replace("p", "."))


for fn in glob.glob(os.path.dirname(NJ) + "/nnlo.ptz__*.dat"):
    g = re.search(r"ptz__(-?[\dp.]+)__(-?[\dp.]+)\.dat", fn)
    if num(g.group(1)) < -2.5 or num(g.group(2)) > 2.5:
        continue
    for line in open(fn):
        if line.startswith("#"):
            continue
        v = line.split()
        if len(v) < 5:
            continue
        k = int(float(v[0]))
        if k < 100:
            fv[k] = fv.get(k, 0) + float(v[3]) * 1e-3
            fe2[k] = fe2.get(k, 0) + (float(v[4]) * 1e-3) ** 2
e3 = qt3.edges
f3 = np.array(
    [
        sum(fv.get(k, 0) for k in range(int(a), int(min(b, 100))))
        for a, b in zip(e3[:-1], e3[1:])
    ]
)
f3e2 = np.array(
    [
        sum(fe2.get(k, 0) for k in range(int(a), int(min(b, 100))))
        for a, b in zip(e3[:-1], e3[1:])
    ]
)
sing3 = f3 - nons3
# map a2 family onto qt3 low-edge grid
i2 = [qt2.index(a) for a in e3[:-1]]
if2 = [qtf2.index(a) for a in e3[:-1]]
n2 = np.array([nons2v[j] / m2[j] for j in i2])
r2g = np.array([r2[j] / m2[j] for j in i2])
f2g = np.array([f2[j] for j in if2])
s2g = np.array([s2[j] for j in if2])
m2g = np.array([m2[j] for j in i2])
n3 = nons3 / m3
band = np.sqrt(f3e2) / m3
x = qt3.centers
sel = (e3[:-1] >= 1) & (e3[:-1] < 20)
B, O, R, P = "#5790fc", "#f89c20", "#e42536", "#7a21dd"
fig, (a1, a2, a3) = plt.subplots(
    3,
    1,
    figsize=(8, 11),
    sharex=True,
    gridspec_kw={"hspace": 0.07, "height_ratios": [1.2, 1, 1]},
)
a1.step(
    x[sel],
    (r3 / m3 * 100)[sel],
    where="mid",
    color=B,
    lw=2,
    label=r"resum N$^{4+0}$LL / m$_3$",
)
a1.step(
    x[sel],
    (r2g * 100)[sel],
    where="mid",
    color=B,
    lw=2,
    ls="--",
    label=r"resum N$^{3+0}$LL / m$_2$",
)
a1.step(
    x[sel],
    (f3 / m3 * 100)[sel],
    where="mid",
    color=O,
    lw=2,
    label=r"FO N$^3$LO (NNLOJET) / m$_3$",
)
a1.step(
    x[sel],
    (f2g / m2g * 100)[sel],
    where="mid",
    color=O,
    lw=2,
    ls="--",
    label=r"FO N$^2$LO (DYTurbo) / m$_2$",
)
a1.step(
    x[sel],
    (sing3 / m3 * 100)[sel],
    where="mid",
    color=R,
    lw=1.5,
    label=r"sing $\mathcal{O}(\alpha_s^3)$ / m$_3$",
)
a1.step(
    x[sel],
    (s2g / m2g * 100)[sel],
    where="mid",
    color=R,
    lw=1.5,
    ls="--",
    label=r"sing $\mathcal{O}(\alpha_s^2)$ / m$_2$",
)
a1.axhline(100, color="gray", lw=0.6, ls=":")
a1.set_ylim(-320, 400)
a1.set_ylabel("component / matched  [%]")
a1.legend(fontsize=9, ncol=2, loc="upper right")
a1.set_title(
    r"Matched-prediction components at low $q_T$ — Z, $|Y|<2.5$, $60<Q<120$ GeV"
)
a2.step(
    x[sel],
    n2[sel] * 100,
    where="mid",
    color=B,
    lw=2,
    label=r"nonsing $\mathcal{O}(\alpha_s^2)$ [DYTurbo $-$ $\alpha_s^2$ sing]",
)
a2.step(
    x[sel],
    (n3 * 100)[sel],
    where="mid",
    color=R,
    lw=2,
    label=r"nonsing $\mathcal{O}(\alpha_s^3)$ [NNLOJET $-$ $\alpha_s^3$ sing]",
)
a2.fill_between(
    x[sel],
    ((n3 - band) * 100)[sel],
    ((n3 + band) * 100)[sel],
    step="mid",
    color=R,
    alpha=0.2,
    label="NNLOJET stat",
)
a2.axhline(0, color="gray", lw=0.7)
a2.set_ylim(-14, 7)
a2.set_ylabel("nonsingular / matched  [%]")
a2.legend(fontsize=9, loc="lower right")
d = (n3 - n2) * 100
a3.step(
    x[sel],
    d[sel],
    where="mid",
    color=P,
    lw=2,
    label=r"$\mathcal{O}(\alpha_s^3)-\mathcal{O}(\alpha_s^2)$ nonsingular (= bridge syst.)",
)
a3.fill_between(
    x[sel],
    (d - band * 100)[sel],
    (d + band * 100)[sel],
    step="mid",
    color=P,
    alpha=0.2,
    label="NNLOJET stat",
)
a3.axhline(0, color="gray", lw=0.7)
a3.axvline(5, color="gray", lw=1, ls="--")
a3.text(5.2, 4.5, "proposed cut", fontsize=9, color="gray")
a3.set_ylim(-9, 7)
a3.set_xlim(0, 20)
a3.set_xlabel(r"$q_T$ [GeV]")
a3.set_ylabel(r"$\Delta$ nonsingular / matched  [%]")
a3.legend(fontsize=9, loc="lower right")
for ext in ("png", "pdf"):
    fig.savefig(
        f"{OUT}/nonsingular_order_diff_lowqt.{ext}", dpi=150, bbox_inches="tight"
    )
print("saved")
