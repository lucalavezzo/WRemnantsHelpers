"""Pure-coefficient decomposition of the FO vs the matched total:
lo, nlo_only, nnlo_only (= O(as),O(as^2),O(as^3) coefficients of the qT spectrum)
each as % of the N4+0LL+N3LO matched prediction. |Y|<2.5, Q 60-120, pdf0."""

import numpy as np, glob, re, os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wremnants.utilities.io_tools import input_tools

Z = "/ceph/submit/data/user/l/lavezzo/zstuff"
R4 = f"{Z}/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_newvals_coarse_combined.pkl"
S3 = f"{Z}/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Newvals_Coarse_n3lo_sing/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_newvals_coarse_n3lo_sing_combined.pkl"
NJ = "/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2/result/final/nnlo.ptz"
RDIR = os.path.dirname(NJ)
OUT = os.path.expanduser("~/public_html/alphaS/260714_fo_vs_matched")

hm = input_tools.read_matched_scetlib_nnlojet_hist(
    R4,
    S3,
    NJ,
    axes=("Q", "Y", "qT"),
    charge=0,
    zero_nons_bins=slice(0j, complex(0, 1.0)),
    mass_edges=[60, 120],
)


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


m = prof(hm)
qt = hm.axes["qT"]
edges = qt.edges


def read_coeff(pref):
    f = {}
    e2 = {}

    def num(x):
        return float(x.replace("p", "."))

    for fn in glob.glob(f"{RDIR}/{pref}.ptz__*.dat"):
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
                f[k] = f.get(k, 0) + float(v[3]) * 1e-3
                e2[k] = e2.get(k, 0) + (float(v[4]) * 1e-3) ** 2
    a = np.zeros(len(qt))
    ae2 = np.zeros(len(qt))
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        for k in range(int(lo), int(min(hi, 100))):
            a[i] += f.get(k, 0)
            ae2[i] += e2.get(k, 0)
    return a, ae2


lo, _ = read_coeff("lo")
nlo1, _ = read_coeff("nlo_only")
nn1, nn1e2 = read_coeff("nnlo_only")

x = qt.centers
sel = (edges[:-1] >= 1) & (edges[:-1] < 100)
fig, (a1, a2) = plt.subplots(
    2, 1, figsize=(8, 9), sharex=True, gridspec_kw={"hspace": 0.06}
)
a1.plot(x[sel], (lo / m * 100)[sel], label=r"LO coeff  $\mathcal{O}(\alpha_s)$", lw=2)
a1.plot(
    x[sel],
    (nlo1 / m * 100)[sel],
    label=r"NLO-only coeff  $\mathcal{O}(\alpha_s^2)$  [DYTurbo-precision available]",
    lw=2,
)
a1.plot(
    x[sel],
    (nn1 / m * 100)[sel],
    label=r"NNLO-only coeff  $\mathcal{O}(\alpha_s^3)$  [needs NNLOJET]",
    lw=2,
    color="tab:purple",
)
a1.axhline(0, color="gray", lw=0.7)
a1.axhline(100, color="gray", lw=0.5, ls=":")
a1.set_ylim(-60, 190)
a1.set_ylabel("FO coefficient / matched  [%]")
a1.legend(fontsize=9)
a1.set_title(r"FO $\alpha_s$-coefficients vs matched total, Z, $|Y|<2.5$, $60<Q<120$")
a2.plot(
    x[sel],
    (nn1 / m * 100)[sel],
    color="tab:purple",
    lw=2,
    label=r"$\mathcal{O}(\alpha_s^3)$ coeff / matched",
)
a2.fill_between(
    x[sel],
    ((nn1 - np.sqrt(nn1e2)) / m * 100)[sel],
    ((nn1 + np.sqrt(nn1e2)) / m * 100)[sel],
    color="tab:purple",
    alpha=0.25,
    label="NNLOJET stat (current run)",
)
a2.axhline(0, color="gray", lw=0.7)
a2.set_ylim(-20, 20)
a2.set_xlabel(r"$q_T$ [GeV]")
a2.set_ylabel(r"$\mathcal{O}(\alpha_s^3)$ / matched  [%]")
a2.legend(fontsize=9)
a2.set_xlim(0, 100)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/alpha3_coeff_vs_matched.{ext}", dpi=150, bbox_inches="tight")
with open(f"{OUT}/alpha3_coeff_vs_matched_table.md", "w") as t:
    t.write(
        "| qT (GeV) | matched (pb) | LO/m | NLOonly/m | NNLOonly/m | NNLOonly stat/m |\n|---|---|---|---|---|---|\n"
    )
    for i in range(len(qt)):
        a, b = edges[i], edges[i + 1]
        if a < 1 or a >= 100:
            continue
        t.write(
            f"| {a:.0f}-{b:.0f} | {m[i]:.1f} | {lo[i]/m[i]*100:.1f}% | {nlo1[i]/m[i]*100:+.1f}% | {nn1[i]/m[i]*100:+.2f}% | {np.sqrt(nn1e2[i])/m[i]*100:.2f}% |\n"
        )
print("saved")
for k in (2, 5, 10, 15, 20, 30, 50):
    i = qt.index(k)
    print(
        f"qT {k:>2}: as3-only/m = {nn1[i]/m[i]*100:+6.2f}%  stat/m = {np.sqrt(nn1e2[i])/m[i]*100:5.2f}%"
    )
