"""Per-qT-bin anatomy of the matched prediction: FO/matched and (FO-sing)/matched.
Blessed inputs (print_command.py on scetlib_dyturbo_NewVars_MSHT20aN3LO corr):
SCETlib N3+0LL newvals_coarse resum + nnlo_sing, DYTurbo N2LO FO; NNLOJET N3LO FO
overlaid from as118_seedfix_clean_v2. |Y|<2.5, Q 60-120, vars=pdf0."""

import numpy as np, glob, re, sys, os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wremnants.utilities.io_tools import input_tools

RESUM = "/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_combined.pkl"
SING = "/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse_nnlo_sing/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_nnlo_sing_combined.pkl"
FO = "/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-MSHT20aN3LO-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-MSHT20an3lo_as118-{scale}-scetlibmatch.txt"
RDIR = "/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2/result/final"
OUT = os.path.expanduser("~/public_html/alphaS/260714_fo_vs_matched")
os.makedirs(OUT, exist_ok=True)


def matched(zero):
    return input_tools.read_matched_scetlib_dyturbo_hist(
        RESUM, SING, FO, axes=("Q", "Y", "qT"), charge=0, zero_nons_bins=zero
    )


hm = matched(slice(0j, complex(0, 1.0)))  # production matched (qtCutoff=1)
hres = matched(slice(0j, complex(0, 500.0)))  # nonsing zeroed everywhere -> resum only


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
r = prof(hres)
nons = m - r
qt = hm.axes["qT"]
edges = qt.edges
centers = qt.centers
widths = np.diff(edges)

# DYTurbo full FO on the same grid: FO = nons + sing; get sing from the pkl pair via
# the same production readers/rebinning (use matched with nonsing kept, minus resum, plus... )
# simpler: read FO directly like the production function does
hresum_, hfo_sing_ = input_tools.read_scetlib_resum_and_fosing(
    RESUM, SING, ("Q", "Y", "qT"), charge=0, coeff=None
)
hfo_ = input_tools.read_dyturbo_vars_hist(
    FO, var_axis=hfo_sing_.axes["vars"], axes=("Q", "Y", "qT"), charge=0
)
from wums import boostHistHelpers as hh

for ax in ["Y", "Q", "qT"]:
    hfo_, hfo_sing_, hresum_ = hh.rebinHistsToCommon([hfo_, hfo_sing_, hresum_], ax)
fo2 = prof(hfo_)
sing = prof(hfo_sing_)

# NNLOJET N3LO FO from dat, |y|<2.5, pb, 1-GeV bins
f = {}
fe2 = {}


def num(x):
    return float(x.replace("p", "."))


for fn in glob.glob(f"{RDIR}/nnlo.ptz__*.dat"):
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
        if k >= 100:
            continue
        f[k] = f.get(k, 0) + float(v[3]) * 1e-3
        fe2[k] = fe2.get(k, 0) + (float(v[4]) * 1e-3) ** 2
# map NNLOJET 1-GeV bins onto the matched qT grid (sum where matched bins are wider)
f3 = np.zeros(len(qt))
f3e2 = np.zeros(len(qt))
for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
    for k in range(int(a), int(min(b, 100))):
        f3[i] += f.get(k, 0)
        f3e2[i] += fe2.get(k, 0)

sel = (edges[:-1] >= 1) & (edges[:-1] < 100)
x = centers[sel]
fig, (a1, a2) = plt.subplots(
    2,
    1,
    figsize=(8, 9),
    sharex=True,
    gridspec_kw={"height_ratios": [1, 1], "hspace": 0.06},
)
a1.plot(x, (r / m * 100)[sel], label="resummed (SCETlib)", lw=2)
a1.plot(x, (fo2 / m * 100)[sel], label="FO (DYTurbo N2LO)", lw=2)
a1.plot(x, (f3 / m * 100)[sel], label="FO (NNLOJET N3LO)", lw=2, ls="--")
a1.plot(x, (sing / m * 100)[sel], label="singular (SCETlib exp.)", lw=2, ls=":")
a1.axhline(100, color="gray", lw=0.7)
a1.set_ylim(-50, 200)
a1.set_ylabel("component / matched  [%]")
a1.legend(fontsize=9)
a1.set_title(r"Anatomy of matched $q_T$ spectrum, Z, $|Y|<2.5$, $60<Q<120$")
a2.plot(
    x,
    (nons / m * 100)[sel],
    label=r"nonsingular FO$-$sing (DYTurbo N2LO)",
    color="tab:red",
    lw=2,
)
n3 = f3 - sing
a2.plot(
    x,
    (n3 / m * 100)[sel],
    label=r"nonsingular FO$-$sing (NNLOJET N3LO)",
    color="tab:purple",
    lw=1.5,
    ls="--",
)
a2.fill_between(
    x,
    ((n3 - np.sqrt(f3e2)) / m * 100)[sel],
    ((n3 + np.sqrt(f3e2)) / m * 100)[sel],
    color="tab:purple",
    alpha=0.2,
    label="NNLOJET stat.",
)
a2.axhline(0, color="gray", lw=0.7)
a2.set_ylim(-15, 15)
a2.set_xlabel(r"$q_T$ [GeV]")
a2.set_ylabel("nonsingular / matched  [%]")
a2.legend(fontsize=9)
a2.set_xlim(0, 100)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/fo_vs_matched.{ext}", dpi=150, bbox_inches="tight")

with open(f"{OUT}/fo_vs_matched_table.md", "w") as t:
    t.write(
        "| qT (GeV) | matched (pb) | FO(N2LO)/m | FO(N3LO)/m | nons(N2LO)/m | nons(N3LO)/m | N3LO stat/m |\n|---|---|---|---|---|---|---|\n"
    )
    for i in range(len(qt)):
        a, b = edges[i], edges[i + 1]
        if a < 1 or a >= 100:
            continue
        t.write(
            f"| {a:.0f}-{b:.0f} | {m[i]:.1f} | {fo2[i]/m[i]*100:.1f}% | {f3[i]/m[i]*100:.1f}% | {nons[i]/m[i]*100:+.2f}% | {(f3[i]-sing[i])/m[i]*100:+.2f}% | {np.sqrt(f3e2[i])/m[i]*100:.2f}% |\n"
        )
with open(f"{OUT}/fo_vs_matched.log", "w") as L:
    L.write(
        "command: "
        + " ".join(sys.argv)
        + "\nscript: /tmp/fo_anatomy_plot.py (copy in WRemnantsHelpers/studies/nnlojet-lowqt-cut/)\n"
    )
    L.write(f"inputs:\n {RESUM}\n {SING}\n {FO}\n {RDIR}\n")
print("saved to", OUT)
