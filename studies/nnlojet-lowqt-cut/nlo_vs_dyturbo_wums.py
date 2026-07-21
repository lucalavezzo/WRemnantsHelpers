"""NNLOJET 'nlo' vs DYTurbo N2LO, wums-styled. Bin-integral comparison on aligned edges."""

import numpy as np, glob, re, os, hist
import matplotlib

matplotlib.use("Agg")
from wremnants.utilities.io_tools import input_tools
from wums import plot_tools, output_tools

Z = "/ceph/submit/data/user/l/lavezzo/zstuff"
S2 = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse_nnlo_sing/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_nnlo_sing_combined.pkl"
R3 = f"{Z}/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_Z_COM13_MSHT20aN3LO_N3+0LL_lattice_newvals_coarse_combined.pkl"
DY = "/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-MSHT20aN3LO-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-MSHT20an3lo_as118-{scale}-scetlibmatch.txt"
RDIR = "/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2/result/final"
OUT = os.path.expanduser("~/public_html/alphaS/260714_fo_vs_matched")

# DYTurbo via production reader: Q slice 60-120, central scale, |Y|<2.5 sum
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

# NNLOJET nlo per 1-GeV bin, |y|<2.5 sum, pb (x1e-3 like read_nnlojet_file)
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

# aligned common edges: 1-GeV where dyturbo is sub-GeV (sum pairs), dyturbo edges where wider
rows = []  # (lo,hi,dy_integral,nj_integral,nj_var)
acc = {}
for j, (a, b) in enumerate(zip(qte[:-1], qte[1:])):
    if b > 100:
        continue
    if b - a < 1.0:
        acc.setdefault(int(a), [0.0, 0.0])
        acc[int(a)][0] += dyv[j]
        acc[int(a)][1] += b - a
    else:
        kk = [k for k in range(int(a), int(b)) if k in f]
        if len(kk) == int(b - a) and a >= 1:
            rows.append((a, b, dyv[j], sum(f[k] for k in kk), sum(fe2[k] for k in kk)))
for k, (integ, w) in acc.items():
    if k >= 1 and k in f and abs(w - 1) < 1e-6:
        rows.append((k, k + 1, integ, f[k], fe2[k]))
rows.sort()
edges = np.array([r[0] for r in rows] + [rows[-1][1]])
ax = hist.axis.Variable(edges, name="qT")
h_dy = hist.Hist(ax, storage=hist.storage.Weight())
h_dy.values()[...] = [r[2] for r in rows]
h_dy.variances()[...] = 0.0
h_nj = hist.Hist(ax, storage=hist.storage.Weight())
h_nj.values()[...] = [r[3] for r in rows]
h_nj.variances()[...] = [r[4] for r in rows]

fig = plot_tools.makePlotWithRatioToRef(
    [h_dy, h_nj],
    ["DYTurbo N$^2$LO FO", r"NNLOJET nlo ($\alpha_s+\alpha_s^2$)"],
    colors=["#5790fc", "#e42536"],
    xlabel=r"$q_T$ [GeV]",
    ylabel=r"d$\sigma$/d$q_T$ [pb/GeV]",
    rlabel="x/DYTurbo",
    rrange=[0.98, 1.02],
    nlegcols=1,
    binwnorm=1.0,
    baseline=True,
    yerr=True,
    logy=True,
    legtext_size=20,
    extra_text=[
        r"$\mathcal{O}(\alpha_s^2)$ FO comparison",
        "Z, $|Y|<2.5$",
        "$60<Q<120$ GeV",
        r"$\mu_R=\mu_F=m_{\ell\ell}$",
    ],
    extra_text_loc=(0.05, 0.55),
    xlim=(0, 100),
    ratio_legend=False,
)
name = "nlo_nnlojet_vs_dyturbo_wums"
plot_tools.save_pdf_and_png(OUT, name)
try:
    output_tools.write_index_and_log(OUT, name)
except Exception as e:
    print("index/log:", e)
print("saved", name)
