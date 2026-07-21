import numpy as np
from wremnants.utilities.io_tools import input_tools

RESUM = "/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_combined.pkl"
SING = "/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse_nnlo_sing/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_nnlo_sing_combined.pkl"
FO = "/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-MSHT20aN3LO-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-MSHT20an3lo_as118-{scale}-scetlibmatch.txt"


def matched(zero):
    return input_tools.read_matched_scetlib_dyturbo_hist(
        RESUM, SING, FO, axes=("Q", "Y", "qT"), charge=0, zero_nons_bins=zero
    )


hm = matched(slice(0j, complex(0, 1.0)))
hall = matched(slice(0j, complex(0, 500.0)))
print("axes:", [(a.name, a.size) for a in hm.axes])


def prof(h):
    hc = h[{"vars": "pdf0"}] if "vars" in h.axes.name else h
    names = hc.axes.name
    v = hc.values()
    # sum everything except Y,qT
    keep = [names.index("Y"), names.index("qT")]
    oth = [i for i in range(v.ndim) if i not in keep]
    v = v.sum(axis=tuple(oth)) if oth else v
    if names.index("Y") > names.index("qT"):
        v = v.T
    yax = hc.axes["Y"]
    i0, i1 = yax.index(-2.5), yax.index(2.5)
    return v[i0:i1].sum(axis=0)


m = prof(hm)
r = prof(hall)
qt = hm.axes["qT"]
fo = m - r
print(
    f"\nSCETlib(N3+0LL) + DYTurbo(N2LO) matched, |Y|<2.5, Q 60-120  (blessed inputs, qtCutoff=1)"
)
print(f"{'qT bin':>10} | {'FO-term/matched':>15}")
edges = qt.edges
for i in range(len(qt)):
    lo, hi = edges[i], edges[i + 1]
    if lo >= 60:
        break
    print(f"{lo:5.1f}-{hi:<5.1f} | {fo[i]/m[i]*100:14.2f}%")
for X in (5, 10, 20, 30):
    ix = qt.index(X)
    print(
        f"integral qT<{X:>2}: FO-term = {fo[:ix].sum()/m[:ix].sum()*100:6.2f}% of matched"
    )
