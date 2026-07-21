import pickle, numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OLD = "/work/submit/areimers/wmass/TheoryCorrections/SCETlib/com13_msht20_newnps_n3+0ll_lattice_fine/inclusive_Z_COM13_MSHT20_N3+0LL_lattice_fine_combined.pkl"
NEW = "/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20_newnps_n3+0ll_lattice_lambda4bugfix_central/inclusive_Z_COM13_MSHT20_N3+0LL_lattice_lambda4bugfix_central_combined.pkl"
OUT = "/home/submit/lavezzo/public_html/alphaS/260720_pdf_swap_msht20/260720_MSHT20_lambda4_resum_OLDvsNEW"


def central_ptv(path, absy_max=2.5):
    d = pickle.load(open(path, "rb"))
    h = d["hist"]
    vlabels = list(h.axes["vars"])
    cidx = 0
    for c in ("pdf0", "central", "nominal"):
        if c in vlabels:
            cidx = vlabels.index(c)
            break
    vals = h.values()
    Qe = np.asarray(h.axes["Q"].edges)
    qi = int(np.argmin(np.abs(Qe - 60.0)))
    Yc = np.asarray(h.axes["Y"].centers)
    ymask = np.abs(Yc) < absy_max
    qT_c = np.asarray(h.axes["qT"].centers)
    v = vals[qi, :, :, cidx][ymask, :].sum(axis=0)
    return qT_c, v


qT, old = central_ptv(OLD)
_, new = central_ptv(NEW)
ratio = new / old

fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 7), height_ratios=[2, 1], sharex=True)
a1.step(
    qT, old, where="mid", label="OLD (buggy $\\lambda_4$, pre-Apr22)", color="crimson"
)
a1.step(qT, new, where="mid", label="NEW (fixed $\\lambda_4$)", color="navy", ls="--")
a1.set_ylabel(r"$d\sigma/dq_T^{gen}$ (resummed, $|Y|<2.5$, $60<Q<120$)")
a1.legend()
a1.set_title(
    "MSHT20 resummed $\\sigma_{gen}$ at central NP tune: $\\lambda_4$-fix effect"
)
a1.set_xlim(0, 40)
a2.axhline(1.0, color="gray", lw=0.8)
a2.step(qT, ratio, where="mid", color="black")
a2.set_ylabel("NEW / OLD")
a2.set_xlabel(r"$q_T^{gen}$ (GeV)")
a2.set_ylim(0.99, 1.02)
a2.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT + ".png", dpi=110)
fig.savefig(OUT + ".pdf")
print("wrote", OUT + ".png")
with open(OUT + ".log", "w") as f:
    f.write(
        "MSHT20 resummed sigma_gen: fixed-lambda4 (NEW) vs buggy-lambda4 (OLD), central NP tune, |Y|<2.5, Q=[60,120]\n"
    )
    f.write(f"OLD={OLD}\nNEW={NEW}\n")
    f.write(
        f"ratio(sum)={new.sum()/old.sum():.6f}  bin0={ratio[0]:.5f}  min={ratio.min():.5f}  max={ratio.max():.5f}\n"
    )
    f.write(
        "Both at lambda2=0.25 lambda4=0.06 delta_lambda2=0.0 lambda2_nu=0.087 lambda4_nu=0.0074 lambda_inf_nu=1.6853 (tanh_2); only the SCETlib lambda4 code differs.\n"
    )
