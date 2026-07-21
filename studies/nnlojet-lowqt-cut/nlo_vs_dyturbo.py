"""Validate: NNLOJET 'nlo' (= alpha_s^1+alpha_s^2 spectrum) vs DYTurbo N2LO FO.
|Y|<2.5, 60<Q<120, central scale (mur=muf=mll both). Ratio + pulls."""

import numpy as np, glob, re, os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wremnants.utilities.io_tools import input_tools

Z = "/ceph/submit/data/user/l/lavezzo/zstuff"
S2 = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse_nnlo_sing/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_nnlo_sing_combined.pkl"
R3 = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_combined.pkl"
DY = "/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-MSHT20aN3LO-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-MSHT20an3lo_as118-{scale}-scetlibmatch.txt"
RDIR = "/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2/result/final"
OUT = os.path.expanduser("~/public_html/alphaS/260714_fo_vs_matched")

_, hs2_ = input_tools.read_scetlib_resum_and_fosing(
    R3, S2, ("Q", "Y", "qT"), charge=0, coeff=None
)
hdy = input_tools.read_dyturbo_vars_hist(
    DY, var_axis=hs2_.axes["vars"], axes=("Q", "Y", "qT"), charge=0
)
hdy = hdy[{"Q": slice(complex(0, 60), complex(0, 120)), "vars": "pdf0"}]
names = hdy.axes.name
v = hdy.values()
keep = [names.index("Y"), names.index("qT")]
v = v.sum(axis=tuple(i for i in range(v.ndim) if i not in keep))
if names.index("Y") > names.index("qT"):
    v = v.T
yax = hdy.axes["Y"]
dyv = v[yax.index(-2.5) : yax.index(2.5)].sum(axis=0)
qte = hdy.axes["qT"].edges
dybins = [
    (a, b, dyv[j] / (b - a))
    for j, (a, b) in enumerate(zip(qte[:-1], qte[1:]))
    if b <= 100
]

f = {}
fe2 = {}


def num(x):
    return float(x.replace("p", "."))


for fn in glob.glob(f"{RDIR}/nlo.ptz__*.dat"):
    g = re.search(r"ptz__(-?[\dp.]+)__(-?[\dp.]+)\.dat", fn)
    if num(g.group(1)) < -2.5 or num(g.group(2)) > 2.5:
        continue
    for line in open(fn):
        if line.startswith("#"):
            continue
        c = line.split()
        if len(c) < 5:
            continue
        k = int(float(c[0]))
        if k < 100:
            f[k] = f.get(k, 0) + float(c[3]) * 1e-3
            fe2[k] = fe2.get(k, 0) + (float(c[4]) * 1e-3) ** 2
x = []
nj = []
er = []
dyt = []
# sub-GeV dyturbo bins: aggregate into 1-GeV integrals keyed by integer edge
acc = {}
for a, b, dens in dybins:
    if b - a < 1.0:
        acc.setdefault(int(a), [0.0, 0.0])
        acc[int(a)][0] += dens * (b - a)
        acc[int(a)][1] += b - a
for k, (integ, w) in sorted(acc.items()):
    if k < 1 or k not in f or abs(w - 1.0) > 1e-6:
        continue
    x.append(k + 0.5)
    dyt.append(integ)
    nj.append(f[k])
    er.append(np.sqrt(fe2[k]))
# >=1 GeV dyturbo bins: aggregate NNLOJET onto dyturbo edges (densities)
for a, b, dens in dybins:
    if b - a < 1.0 or a < 1:
        continue
    kk = [k for k in range(int(a), int(b)) if k in f]
    if len(kk) != int(b - a):
        continue
    x.append((a + b) / 2)
    dyt.append(dens)
    nj.append(sum(f[k] for k in kk) / (b - a))
    er.append(np.sqrt(sum(fe2[k] for k in kk)) / (b - a))
x = np.array(x)
nj = np.array(nj)
er = np.array(er)
dyt = np.array(dyt)
r = nj / dyt
rerr = er / dyt
m0 = er > 0
x, nj, er, dyt, r, rerr = x[m0], nj[m0], er[m0], dyt[m0], (nj / dyt)[m0], (er / dyt)[m0]
pulls = (nj - dyt) / er
fig, (a1, a2) = plt.subplots(
    2, 1, figsize=(8, 8), sharex=True, gridspec_kw={"hspace": 0.07}
)
a1.plot(x, dyt, lw=2, color="#5790fc", label="DYTurbo N$^2$LO FO")
a1.errorbar(
    x,
    nj,
    yerr=er,
    fmt=".",
    ms=4,
    color="#e42536",
    label="NNLOJET 'nlo' ($\\alpha_s+\\alpha_s^2$)",
)
a1.set_ylabel(r"d$\sigma$/d$q_T$ [pb/GeV]")
a1.set_yscale("log")
a1.legend(fontsize=10)
a1.set_title(
    r"$\mathcal{O}(\alpha_s^2)$ FO: NNLOJET vs DYTurbo — Z, $|Y|<2.5$, $60<Q<120$ GeV"
)
a2.errorbar(x, r, yerr=rerr, fmt=".", ms=4, color="#964a8b")
a2.axhline(1, color="gray", lw=0.8)
a2.set_ylim(0.95, 1.05)
a2.set_xlim(0, 100)
a2.set_xlabel(r"$q_T$ [GeV]")
a2.set_ylabel("NNLOJET / DYTurbo")
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/nlo_nnlojet_vs_dyturbo.{ext}", dpi=150, bbox_inches="tight")
print(f"bins: {len(x)} | ratio: mean {r.mean():.4f}  median {np.median(r):.4f}")
print(
    f"pulls: mean {pulls.mean():+.2f}  rms {pulls.std():.2f}  |pull|>3: {(abs(pulls)>3).sum()}"
)
for lo, hi in [(1, 5), (5, 10), (10, 20), (20, 50), (50, 100)]:
    m = (x > lo) & (x < hi)
    print(
        f"  qT {lo:>2}-{hi:<3}: mean ratio {r[m].mean():.4f} ± {rerr[m].mean()/np.sqrt(m.sum()):.4f}  pull rms {pulls[m].std():.2f}"
    )
