"""DYTurbo N2LO vs NNLOJET full-N3LO vs HYBRID (DYTurbo a+a2 + NNLOJET nnlo_only).
Shape effect of the as^3 term + stat-precision gain of the hybrid. wums-styled."""

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


def coeff(pref):
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
            c = line.split()
            if len(c) < 5:
                continue
            k = int(float(c[0]))
            if k < 100:
                f[k] = f.get(k, 0) + float(c[3]) * 1e-3
                e2[k] = e2.get(k, 0) + (float(c[4]) * 1e-3) ** 2
    return f, e2


fN, fNe2 = coeff("nnlo")
f3, f3e2 = coeff("nnlo_only")
f2, f2e2 = coeff("nlo")

# aligned edges (1-GeV below where dyturbo is 0.5, dyturbo edges where wider)
rows = []  # (lo,hi,dy,nnlo,nnlo_var,only3,only3_var)
acc = {}
for j, (a, b) in enumerate(zip(qte[:-1], qte[1:])):
    if b > 100:
        continue
    if b - a < 1.0:
        acc.setdefault(int(a), [0.0, 0.0])
        acc[int(a)][0] += dyv[j]
        acc[int(a)][1] += b - a
    else:
        kk = [k for k in range(int(a), int(b)) if k in fN]
        if len(kk) == int(b - a) and a >= 1:
            rows.append(
                (
                    a,
                    b,
                    dyv[j],
                    sum(fN[k] for k in kk),
                    sum(fNe2[k] for k in kk),
                    sum(f3[k] for k in kk),
                    sum(f3e2[k] for k in kk),
                    sum(f2[k] for k in kk),
                    sum(f2e2[k] for k in kk),
                )
            )
for k, (integ, w) in acc.items():
    if k >= 1 and k in fN and abs(w - 1) < 1e-6:
        rows.append((k, k + 1, integ, fN[k], fNe2[k], f3[k], f3e2[k], f2[k], f2e2[k]))
rows.sort()
edges = np.array([r[0] for r in rows] + [rows[-1][1]])
ax = hist.axis.Variable(edges, name="qT")


def mk(vals, vars):
    h = hist.Hist(ax, storage=hist.storage.Weight())
    h.values()[...] = vals
    h.variances()[...] = vars
    return h


h_dy = mk([r[2] for r in rows], 0.0)
h_nj = mk([r[3] for r in rows], [r[4] for r in rows])
h_hy = mk(
    [r[2] + r[5] for r in rows], [r[6] for r in rows]
)  # DYTurbo a+a2  +  NNLOJET as^3-only
h_n2 = mk([r[7] for r in rows], [r[8] for r in rows])  # NNLOJET nlo (a+a2)

fig = plot_tools.makePlotWithRatioToRef(
    [h_dy, h_n2, h_nj, h_hy],
    [
        "DYTurbo N$^2$LO",
        "NNLOJET N$^2$LO",
        "NNLOJET full N$^3$LO",
        "hybrid: DYTurbo + NNLOJET $\\alpha_s^3$",
    ],
    colors=["#5790fc", "#964a8b", "#f89c20", "#e42536"],
    xlabel=r"$q_T$ [GeV]",
    ylabel=r"d$\sigma$/d$q_T$ [pb/GeV]",
    rlabel="x/DYTurbo",
    rrange=[0.85, 1.2],
    nlegcols=1,
    binwnorm=1.0,
    baseline=True,
    yerr=True,
    logy=True,
    legtext_size=20,
    extra_text=[
        "FO only, Z, $|Y|<2.5$",
        "$60<Q<120$ GeV",
        r"$\mu_R=\mu_F=m_{\ell\ell}$",
    ],
    extra_text_loc=(0.05, 0.45),
    xlim=(0, 100),
    ratio_legend=False,
)
name = "fo_hybrid_vs_full_wums"
plot_tools.save_pdf_and_png(OUT, name)
try:
    output_tools.write_index_and_log(OUT, name)
except Exception as e:
    print("idx:", e)

lo_ = np.array([r[0] for r in rows])
dy = np.array([r[2] for r in rows])
nj = np.array([r[3] for r in rows])
nje = np.sqrt([r[4] for r in rows])
hy = dy + np.array([r[5] for r in rows])
hye = np.sqrt([r[6] for r in rows])
print(
    f"{'qT range':>9} | {'full rel err':>12} | {'hybrid rel err':>14} | {'gain err_full/err_hyb':>20}"
)
for a, b in [(1, 5), (5, 10), (10, 20), (20, 50), (50, 100)]:
    m = (lo_ >= a) & (lo_ < b)
    rf = np.median(nje[m] / np.abs(nj[m])) * 100
    rh = np.median(hye[m] / np.abs(hy[m])) * 100
    g = np.median(nje[m] / hye[m])
    print(f"{a:>3}-{b:<5} | {rf:11.2f}% | {rh:13.2f}% | {g:20.3f}")
