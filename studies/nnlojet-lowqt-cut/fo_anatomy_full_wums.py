#!/usr/bin/env python3
"""Full anatomy of the N4+0LL+N3LO matched prediction, wums-styled.

Hists (all |Y|<2.5 summed, 60<Q<120, vars=pdf0, per-1-GeV-bin integrals in pb):
  matched   = read_matched_scetlib_nnlojet_hist (blessed args, qtCutoff=1)  [ratio baseline]
  resum     = same call with nonsingular zeroed everywhere (pure N4+0LL)
  FO N3LO   = NNLOJET result/final/nnlo.ptz y-slices (x1e-3, quad errors)
  sing a3   = FO N3LO - (matched - resum)   [= the O(as^3) counterterm]
  FO N2LO   = DYTurbo (production reader, Q bin 60-120 selected)
  sing a2   = nnlo_sing pkl (N3+0LL config), read like the resum
Run inside the WRemnants container + setup.sh.
"""

import numpy as np, glob, re, os, hist
import matplotlib

matplotlib.use("Agg")
from wremnants.utilities.io_tools import input_tools
from wums import plot_tools, output_tools

Z = "/ceph/submit/data/user/l/lavezzo/zstuff"
R4 = f"{Z}/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_newvals_coarse_combined.pkl"
S3 = f"{Z}/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Newvals_Coarse_n3lo_sing/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_newvals_coarse_n3lo_sing_combined.pkl"
R3 = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_combined.pkl"
S2 = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse_nnlo_sing/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_nnlo_sing_combined.pkl"
DY = "/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-MSHT20aN3LO-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-MSHT20an3lo_as118-{scale}-scetlibmatch.txt"
NJ = "/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2/result/final/nnlo.ptz"
OUT = os.path.expanduser("~/public_html/alphaS/260714_fo_vs_matched")
import sys

QMAX = int(sys.argv[1]) if len(sys.argv) > 1 else 60
LOGY = "lin" not in sys.argv[2:]


def prof(h):
    hc = h[{"vars": "pdf0"}] if "vars" in h.axes.name else h
    names = hc.axes.name
    v = hc.values()
    keep = [names.index("Y"), names.index("qT")]
    v = v.sum(axis=tuple(i for i in range(v.ndim) if i not in keep))
    if names.index("Y") > names.index("qT"):
        v = v.T
    yax = hc.axes["Y"]
    return v[yax.index(-2.5) : yax.index(2.5)].sum(axis=0), hc.axes["qT"]


hm = input_tools.read_matched_scetlib_nnlojet_hist(
    R4,
    S3,
    NJ,
    axes=("Q", "Y", "qT"),
    charge=0,
    zero_nons_bins=slice(0j, complex(0, 1.0)),
    mass_edges=[60, 120],
)
hm2 = input_tools.read_matched_scetlib_dyturbo_hist(
    R3,
    S2,
    DY,
    axes=("Q", "Y", "qT"),
    charge=0,
    zero_nons_bins=slice(0j, complex(0, 1.0)),
)
hres = input_tools.read_matched_scetlib_nnlojet_hist(
    R4,
    S3,
    NJ,
    axes=("Q", "Y", "qT"),
    charge=0,
    zero_nons_bins=slice(0j, complex(0, 500.0)),
    mass_edges=[60, 120],
)
m, qt = prof(hm)
r, _ = prof(hres)
m2v, qm2 = prof(hm2)
assert np.allclose(np.diff(qt.edges[:QMAX]), 1.0), "expects 1-GeV grid"


def nnlojet_coeff(pref):
    f = np.zeros(100)
    e2 = np.zeros(100)

    def num(x):
        return float(x.replace("p", "."))

    for fn in glob.glob(os.path.dirname(NJ) + f"/{pref}.ptz__*.dat"):
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
                f[k] += float(c[3]) * 1e-3
                e2[k] += (float(c[4]) * 1e-3) ** 2
    return f, e2


f3, f3e2 = nnlojet_coeff("nnlo")
nons = m - r
sing3 = f3[: len(m)] - nons

# a2 family: DYTurbo FO + nnlo_sing, via production readers
hr3_, hs2_ = input_tools.read_scetlib_resum_and_fosing(
    R3, S2, ("Q", "Y", "qT"), charge=0, coeff=None
)
s2, qs2 = prof(hs2_)
hdy = input_tools.read_dyturbo_vars_hist(
    DY, var_axis=hs2_.axes["vars"], axes=("Q", "Y", "qT"), charge=0
)
hdy = hdy[{"Q": slice(complex(0, 60), complex(0, 120))}]
dyv, qdy = prof(hdy)


def regrid(vals, edges, nmax=100):
    """overlap-weighted redistribution of per-bin integrals onto 1-GeV grid"""
    out = np.zeros(nmax)
    for j, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        for k in range(int(np.floor(a)), min(int(np.ceil(b)), nmax)):
            ov = max(0.0, min(b, k + 1) - max(a, k))
            if ov > 0:
                out[k] += vals[j] * ov / (b - a)
    return out


f2 = regrid(dyv, qdy.edges)
m2g = regrid(m2v, qm2.edges)
s2g = regrid(s2, qs2.edges)

n = QMAX
ax = hist.axis.Regular(n, 0, QMAX, name="qT")


def mk(vals, vars=0.0):
    h = hist.Hist(ax, storage=hist.storage.Weight())
    h.values()[...] = vals[:n]
    h.variances()[...] = vars[:n] if np.ndim(vars) else vars
    return h


hists = [mk(m), mk(m2g), mk(r), mk(f3, f3e2), mk(sing3), mk(f2), mk(s2g)]
labels = [
    r"matched N$^{4+0}$LL+N$^3$LO",
    r"matched N$^{3+0}$LL+N$^2$LO",
    r"resummed N$^{4+0}$LL",
    r"FO N$^3$LO (NNLOJET)",
    r"singular $\mathcal{O}(\alpha_s^3)$",
    r"FO N$^2$LO (DYTurbo)",
    r"singular $\mathcal{O}(\alpha_s^2)$ (N$^{3}$LL)",
]
colors = ["black", "#7a21dd", "#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1"]
fig = plot_tools.makePlotWithRatioToRef(
    hists,
    labels,
    colors=colors,
    linestyles=["solid", "solid", "solid", "solid", "dashed", "solid", "dashed"],
    xlabel=r"$q_T$ [GeV]",
    ylabel=r"d$\sigma$/d$q_T$ [pb/GeV]",
    rlabel="x/matched",
    rrange=[0.5, 1.6],
    nlegcols=2,
    binwnorm=1.0,
    baseline=True,
    yerr=True,
    logy=LOGY,
    legtext_size=15,
    extra_text=["Z, $|Y|<2.5$", "$60<Q<120$ GeV"],
    extra_text_loc=(0.72, 0.92) if not LOGY else (0.05, 0.42),
    xlim=(0, QMAX),
    ratio_legend=False,
    cutoff=1e-3,
)
if not LOGY:
    try:
        leg = fig.axes[0].get_legend()
        try:
            leg.set_loc("lower right")
        except Exception:
            leg._set_loc(4)
    except Exception as e:
        print("leg move:", e)
name = (
    f"fo_anatomy_full_wums"
    + (f"_qmax{QMAX}" if QMAX != 60 else "")
    + ("" if LOGY else "_liny")
)
plot_tools.save_pdf_and_png(OUT, name)
try:
    output_tools.write_index_and_log(OUT, name)
except Exception as e:
    print("idx:", e)
print("saved", name)
# numeric check around the previously-suspect bins
for k in (28, 29, 56, 57):
    print(
        f"qT {k}: resum/m={r[k]/m[k]:.3f}  sing3/m={sing3[k]/m[k]:.3f}  f3/m={f3[k]/m[k]:.3f}"
    )
