import numpy as np, glob, re
from wremnants.utilities.io_tools import input_tools

RESUM = "/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_combined.pkl"
SING = "/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse_nnlo_sing/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_nnlo_sing_combined.pkl"
FO = "/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-MSHT20aN3LO-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-MSHT20an3lo_as118-{scale}-scetlibmatch.txt"
RDIR = "/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2/result/final"


def matched(zero):
    return input_tools.read_matched_scetlib_dyturbo_hist(
        RESUM, SING, FO, axes=("Q", "Y", "qT"), charge=0, zero_nons_bins=zero
    )


hm = matched(slice(0j, complex(0, 1.0)))
hall = matched(slice(0j, complex(0, 500.0)))


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
r = prof(hall)
qt = hm.axes["qT"]
fo_term = m - r
# NNLOJET f, sigma_f per 1-GeV bin |y|<2.5, pb
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
        if k >= 30:
            continue
        f[k] = f.get(k, 0) + float(v[3]) * 1e-3
        fe2[k] = fe2.get(k, 0) + (float(v[4]) * 1e-3) ** 2
print(
    f"{'qT':>7} | {'matched pb':>10} | {'FOterm/m':>8} | {'NNLOJET FO/m':>12} | {'NNLOJET stat/m':>14}"
)
edges = qt.edges
for i in range(len(qt)):
    lo, hi = edges[i], edges[i + 1]
    if lo >= 15:
        break
    k = int(lo)
    print(
        f"{lo:3.0f}-{hi:<3.0f} | {m[i]:10.1f} | {fo_term[i]/m[i]*100:7.2f}% | {f.get(k,0)/m[i]*100:11.1f}% | {np.sqrt(fe2.get(k,0))/m[i]*100:13.2f}%"
    )
