#!/usr/bin/env python3
"""Two anatomy plots with the NOMINAL matched (N3+0LL+N2LO) as ratio baseline.

A: fo_pieces_n3lln2lo_wums      — nominal matched + its own pieces
   (resummed N3+0LL, FO N2LO DYTurbo, singular O(as^2)).
B: fo_pieces_n4lln3lo_vs_n3lln2lo_wums — nominal matched + the alternative
   matched N4+0LL+N3LO and ITS pieces (resummed N4+0LL, FO N3LO NNLOJET,
   singular O(as^3)).
All |Y|<2.5, 60<Q<120, vars=pdf0, per-1-GeV-bin integrals (overlap regrid).
Usage: fo_anatomy_by_family_wums.py [qmax=40] [lin]
"""

import numpy as np, glob, re, os, sys, hist
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
QMAX = int(sys.argv[1]) if len(sys.argv) > 1 else 40
LOGY = "lin" not in sys.argv[2:]
RZOOM = "rzoom" in sys.argv[2:]


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


def regrid(vals, edges, nmax=100):
    out = np.zeros(nmax)
    for j, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        for k in range(int(np.floor(a)), min(int(np.ceil(b)), nmax)):
            ov = max(0.0, min(b, k + 1) - max(a, k))
            if ov > 0:
                out[k] += vals[j] * ov / (b - a)
    return out


# a2 family (nominal)
hm2 = input_tools.read_matched_scetlib_dyturbo_hist(
    R3,
    S2,
    DY,
    axes=("Q", "Y", "qT"),
    charge=0,
    zero_nons_bins=slice(0j, complex(0, 1.0)),
)
hr2 = input_tools.read_matched_scetlib_dyturbo_hist(
    R3,
    S2,
    DY,
    axes=("Q", "Y", "qT"),
    charge=0,
    zero_nons_bins=slice(0j, complex(0, 500.0)),
)
m2 = (
    regrid(*prof(hm2)[::1][:1] + (prof(hm2)[1].edges,))
    if False
    else regrid(prof(hm2)[0], prof(hm2)[1].edges)
)
r2 = regrid(prof(hr2)[0], prof(hr2)[1].edges)
_, hs2_ = input_tools.read_scetlib_resum_and_fosing(
    R3, S2, ("Q", "Y", "qT"), charge=0, coeff=None
)
s2v, qs2 = prof(hs2_)
s2 = regrid(s2v, qs2.edges)
hdy = input_tools.read_dyturbo_vars_hist(
    DY, var_axis=hs2_.axes["vars"], axes=("Q", "Y", "qT"), charge=0
)
hdy = hdy[{"Q": slice(complex(0, 60), complex(0, 120))}]
dyv, qdy = prof(hdy)
f2 = regrid(dyv, qdy.edges)
# a3 family
hm3 = input_tools.read_matched_scetlib_nnlojet_hist(
    R4,
    S3,
    NJ,
    axes=("Q", "Y", "qT"),
    charge=0,
    zero_nons_bins=slice(0j, complex(0, 1.0)),
    mass_edges=[60, 120],
)
hr4 = input_tools.read_matched_scetlib_nnlojet_hist(
    R4,
    S3,
    NJ,
    axes=("Q", "Y", "qT"),
    charge=0,
    zero_nons_bins=slice(0j, complex(0, 500.0)),
    mass_edges=[60, 120],
)
m3v, q3 = prof(hm3)
r4v, _ = prof(hr4)
m3 = regrid(m3v, q3.edges)
r4 = regrid(r4v, q3.edges)
f3 = np.zeros(100)
f3e2 = np.zeros(100)


def num(x):
    return float(x.replace("p", "."))


for fn in glob.glob(os.path.dirname(NJ) + "/nnlo.ptz__*.dat"):
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
            f3[k] += float(c[3]) * 1e-3
            f3e2[k] += (float(c[4]) * 1e-3) ** 2
sing3 = f3 - (m3 - r4)

n = QMAX
ax = hist.axis.Regular(n, 0, QMAX, name="qT")


def mk(vals, vars=0.0):
    h = hist.Hist(ax, storage=hist.storage.Weight())
    h.values()[...] = vals[:n]
    h.variances()[...] = np.asarray(vars)[:n] if np.ndim(vars) else vars
    return h


def draw(hists, labels, colors, styles, name, rlab="x/nominal", rr=None, ncols=2):
    fig = plot_tools.makePlotWithRatioToRef(
        hists,
        labels,
        colors=colors,
        linestyles=styles,
        xlabel=r"$q_T$ [GeV]",
        ylabel=r"d$\sigma$/d$q_T$ [pb/GeV]",
        rlabel=rlab,
        rrange=(rr if rr else ([0.9, 1.1] if RZOOM else [0.5, 1.6])),
        nlegcols=ncols,
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
            print("leg:", e)
    full = (
        name
        + (f"_qmax{QMAX}" if QMAX != 40 else "")
        + ("" if LOGY else "_liny")
        + ("_rzoom" if RZOOM else "")
    )
    plot_tools.save_pdf_and_png(OUT, full)
    try:
        output_tools.write_index_and_log(OUT, full)
    except Exception as e:
        print("idx:", e)
    print("saved", full)
    return fig


draw(
    [mk(m2), mk(r2), mk(f2), mk(s2), mk(m2 - r2)],
    [
        r"matched N$^{3+0}$LL+N$^2$LO",
        r"resummed N$^{3+0}$LL",
        r"FO N$^2$LO (DYTurbo)",
        r"singular $\mathcal{O}(\alpha_s^2)$",
        r"nonsingular (FO $-$ sing)",
    ],
    ["black", "#5790fc", "#964a8b", "#9c9ca1", "#e42536"],
    ["solid", "solid", "solid", "dashed", "solid"],
    "fo_pieces_n3lln2lo_wums",
)
draw(
    [mk(m2), mk(m3), mk(r4), mk(f3, f3e2), mk(sing3), mk(m3 - r4, f3e2)],
    [
        r"matched N$^{3+0}$LL+N$^2$LO",
        r"matched N$^{4+0}$LL+N$^3$LO",
        r"resummed N$^{4+0}$LL",
        r"FO N$^3$LO (NNLOJET)",
        r"singular $\mathcal{O}(\alpha_s^3)$",
        r"nonsingular (FO $-$ sing)",
    ],
    ["black", "#7a21dd", "#5790fc", "#f89c20", "#e42536", "#9c9ca1"],
    ["solid", "solid", "solid", "solid", "dashed", "solid"],
    "fo_pieces_n4lln3lo_vs_n3lln2lo_wums",
)
draw(
    [mk(f2), mk(s2)],
    [
        r"FO N$^2$LO (DYTurbo)",
        r"singular $\mathcal{O}(\alpha_s^2)$ (SCETlib N$^{3}$LL)",
    ],
    ["#964a8b", "#5790fc"],
    ["solid", "dashed"],
    "fo_dyturbo_vs_singular_wums",
    rlab="x/FO",
)
draw(
    [mk(m2 - r2), mk(m3 - r4, f3e2)],
    [
        r"nonsingular $\mathcal{O}(\alpha_s^2)$ [N$^{3+0}$LL match]",
        r"nonsingular $\mathcal{O}(\alpha_s^3)$ [N$^{4+0}$LL match]",
    ],
    ["#5790fc", "#e42536"],
    ["solid", "solid"],
    "nonsingular_orderconsistent_wums",
    rlab=r"$\alpha_s^3$/$\alpha_s^2$",
    rr=[0, 3.5],
    ncols=1,
)
draw(
    [mk(m3), mk(r4), mk(f3, f3e2), mk(sing3), mk(m3 - r4, f3e2)],
    [
        r"matched N$^{4+0}$LL+N$^3$LO",
        r"resummed N$^{4+0}$LL",
        r"FO N$^3$LO (NNLOJET)",
        r"singular $\mathcal{O}(\alpha_s^3)$",
        r"nonsingular (FO $-$ sing)",
    ],
    ["black", "#5790fc", "#f89c20", "#e42536", "#9c9ca1"],
    ["solid", "solid", "solid", "dashed", "solid"],
    "fo_pieces_n4lln3lo_wums",
    rlab="x/matched",
)
figr = draw(
    [mk(m2), mk(m3, f3e2)],
    [r"matched N$^{3+0}$LL+N$^2$LO (nominal)", r"matched N$^{4+0}$LL+N$^3$LO"],
    ["#5790fc", "#e42536"],
    ["solid", "solid"],
    "matched_orderratio_wums",
    rlab="x/nominal",
    rr=[0.94, 1.06],
    ncols=1,
)
# post-hoc NNLOJET stat band on the ratio panel (plotRatio hard-codes yerr=False)
axr = figr.axes[1]
eg = np.arange(0, QMAX + 1, 1.0)
xs = np.repeat(eg, 2)[1:-1]
sig = np.sqrt(f3e2[:QMAX])
lo = np.repeat((m3[:QMAX] - sig) / m2[:QMAX], 2)
hi = np.repeat((m3[:QMAX] + sig) / m2[:QMAX], 2)
axr.fill_between(
    xs, lo, hi, color="#e42536", alpha=0.22, linewidth=0, label="NNLOJET stat"
)
full = (
    "matched_orderratio_wums"
    + (f"_qmax{QMAX}" if QMAX != 40 else "")
    + ("" if LOGY else "_liny")
)
plot_tools.save_pdf_and_png(OUT, full)
print("saved", full, "(with ratio band)")

# --- matched order ratio in the reco (fit) ptll binning ---
RECO = [
    0,
    1,
    1.5,
    2,
    2.5,
    3,
    3.5,
    4,
    4.5,
    5,
    5.5,
    6,
    6.5,
    7,
    7.5,
    8,
    8.5,
    9,
    9.5,
    10,
    10.5,
    11,
    11.5,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    22,
    24,
    26,
    28,
    30,
    33,
    37,
    44,
]


def to_reco(vals, var=None):
    out = np.zeros(len(RECO) - 1)
    vo = np.zeros(len(RECO) - 1)
    for i, (a, b) in enumerate(zip(RECO[:-1], RECO[1:])):
        for k in range(int(np.floor(a)), int(np.ceil(b))):
            f = max(0.0, min(b, k + 1) - max(a, k))
            if f > 0:
                out[i] += vals[k] * f
                if var is not None:
                    vo[i] += var[k] * f * f
    return (out, vo) if var is not None else out


m2r = to_reco(m2)
m3r, v3r = to_reco(m3, f3e2)
axr_ = hist.axis.Variable(RECO, name="qT")


def mkr(vals, vars=0.0):
    h = hist.Hist(axr_, storage=hist.storage.Weight())
    h.values()[...] = vals
    h.variances()[...] = vars if np.ndim(vars) else 0.0
    return h


figr2 = draw(
    [mkr(m2r), mkr(m3r, v3r)],
    [r"matched N$^{3+0}$LL+N$^2$LO (nominal)", r"matched N$^{4+0}$LL+N$^3$LO"],
    ["#5790fc", "#e42536"],
    ["solid", "solid"],
    "matched_orderratio_recobins_wums",
    rlab="x/nominal",
    rr=[0.94, 1.06],
    ncols=1,
)
axb = figr2.axes[1]
xs = np.repeat(np.array(RECO, dtype=float), 2)[1:-1]
sig = np.sqrt(v3r)
lo = np.repeat((m3r - sig) / m2r, 2)
hi = np.repeat((m3r + sig) / m2r, 2)
axb.fill_between(xs, lo, hi, color="#e42536", alpha=0.22, linewidth=0)
full = (
    "matched_orderratio_recobins_wums"
    + (f"_qmax{QMAX}" if QMAX != 40 else "")
    + ("" if LOGY else "_liny")
    + ("_rzoom" if RZOOM else "")
)
plot_tools.save_pdf_and_png(OUT, full)
print("saved", full, "(reco bins, ratio band)")


# --- NNLOJET coefficients separately: as, as^2, as^3 ---
def nj_coeff(pref):
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


lo_, loe2 = nj_coeff("lo")
n1, n1e2 = nj_coeff("nlo_only")
n2o, n2e2 = nj_coeff("nnlo_only")
draw(
    [mk(lo_, loe2), mk(n1, n1e2), mk(n2o, n2e2)],
    [
        r"$\mathcal{O}(\alpha_s)$ (LO)",
        r"$\mathcal{O}(\alpha_s^2)$ (NLO-only)",
        r"$\mathcal{O}(\alpha_s^3)$ (NNLO-only)",
    ],
    ["#5790fc", "#f89c20", "#e42536"],
    ["solid", "solid", "solid"],
    "nnlojet_coeffs_wums",
    rlab=r"x / $\mathcal{O}(\alpha_s)$",
    rr=[-1.2, 1.2],
    ncols=1,
)
draw(
    [mk(lo_, loe2), mk(n1, n1e2), mk(n2o, n2e2)],
    [
        r"$\mathcal{O}(\alpha_s)$ (LO)",
        r"$\mathcal{O}(\alpha_s^2)$ (NLO-only)",
        r"$\mathcal{O}(\alpha_s^3)$ (NNLO-only)",
    ],
    ["#5790fc", "#f89c20", "#e42536"],
    ["solid", "solid", "solid"],
    "nnlojet_coeffs_zoomratio_wums",
    rlab=r"x / $\mathcal{O}(\alpha_s)$",
    rr=[-0.4, 0.1],
    ncols=1,
)
# --- FO N3LO and its nonsingular (vs the N4+0LL a3 singular) ---
draw(
    [mk(f3, f3e2), mk(sing3)],
    [r"FO N$^3$LO (NNLOJET)", r"singular $\mathcal{O}(\alpha_s^3)$ (N$^{4+0}$LL)"],
    ["#964a8b", "#5790fc"],
    ["solid", "dashed"],
    "fo_singular_a3_wums",
    rlab="x/FO",
    rr=[0.85, 1.15],
    ncols=1,
)

# --- as^3-only coefficient: FO (nnlo_only) vs singular (n3lo_sing - nnlo_sing) ---
sing_a3only = sing3 - s2
draw(
    [mk(n2o, n2e2), mk(sing_a3only), mk(n2o - sing_a3only, n2e2)],
    [
        r"FO coeff $\mathcal{O}(\alpha_s^3)$ (NNLO-only)",
        r"singular coeff $\mathcal{O}(\alpha_s^3)$ [n3lo$-$nnlo sing]",
        r"difference (coeff-level nonsingular)",
    ],
    ["#e42536", "#5790fc", "#9c9ca1"],
    ["solid", "dashed", "solid"],
    "coeff_a3_fo_vs_sing_wums",
    rlab="x/FO coeff",
    rr=[-0.5, 2.5],
    ncols=1,
)
