import pickle, numpy as np

OLD = "/work/submit/areimers/wmass/TheoryCorrections/SCETlib/com13_msht20_newnps_n3+0ll_lattice_fine/inclusive_Z_COM13_MSHT20_N3+0LL_lattice_fine_combined.pkl"
NEW = "/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20_newnps_n3+0ll_lattice_lambda4bugfix_central/inclusive_Z_COM13_MSHT20_N3+0LL_lattice_lambda4bugfix_central_combined.pkl"


def central_ptv(path, absy_max=2.5):
    d = pickle.load(open(path, "rb"))
    h = d["hist"]
    vlabels = list(h.axes["vars"])
    # pick central variation
    cidx = 0
    for c in ("pdf0", "central", "nominal"):
        if c in vlabels:
            cidx = vlabels.index(c)
            break
    vals = h.values()  # (Q, Y, qT, vars)
    Qe = np.asarray(h.axes["Q"].edges)
    # Z window Q bin = the one whose edges are [60,120]
    qi = int(np.argmin(np.abs(Qe - 60.0)))
    Yc = np.asarray(h.axes["Y"].centers)
    ymask = np.abs(Yc) < absy_max
    qT_c = np.asarray(h.axes["qT"].centers)
    # sum over the Z Q-bin (index qi) and |Y|<absy_max, take central var
    v = vals[qi, :, :, cidx]  # (Y, qT)
    v = v[ymask, :].sum(axis=0)  # (qT,)
    return qT_c, v, vlabels[cidx]


qT, old, oldlab = central_ptv(OLD)
qT2, new, newlab = central_ptv(NEW)
assert np.allclose(qT, qT2)
ratio = new / old
print(f"OLD central var='{oldlab}'   NEW central var='{newlab}'")
print(
    f"Sum OLD={old.sum():.4f}  Sum NEW={new.sum():.4f}  ratio(sum)={new.sum()/old.sum():.5f}"
)
print(f"per-qT NEW/OLD (fixed-lambda4 / buggy-lambda4), |Y|<2.5, Q=[60,120]:")
print(f"  min={ratio.min():.5f}  max={ratio.max():.5f}  mean={ratio.mean():.5f}")
print(f"  bin0(qT~{qT[0]:.2f})={ratio[0]:.5f}   tail(qT~{qT[-1]:.1f})={ratio[-1]:.5f}")
print(f"{'qT':>7} {'OLD':>12} {'NEW':>12} {'NEW/OLD':>10}")
for i in range(len(qT)):
    if i < 12 or i % 5 == 0 or i >= len(qT) - 3:
        print(f"{qT[i]:7.2f} {old[i]:12.5f} {new[i]:12.5f} {ratio[i]:10.5f}")
