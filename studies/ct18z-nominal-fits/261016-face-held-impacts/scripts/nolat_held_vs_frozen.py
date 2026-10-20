"""PR #196 real-data check on NOLAT: face-held impacts (both faces held) vs lambda2_nu FROZEN (cubic face held),
at the same point. Holding the bound face lambda2_nu >= 0 must equal freezing lambda2_nu. Also the held result vs
the earlier NOLAT_PF (all3-local, which still had the global-stat curvature correction). Sigmas / impacts only.
"""

import numpy as np
from rabbit import io_tools

D = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_pr_validation/"
H = io_tools.get_fitresult(D + "fitresults_PR196_NOLAT_held.hdf5")
F = io_tools.get_fitresult(D + "fitresults_PR196_NOLAT_frozen.hdf5")
PF = io_tools.get_fitresult(
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_nolat_postfit/fitresults_NOLAT_PF.hdf5"
)
names = list(np.array(H["parms"].get().axes["parms"]))
i = names.index("lambda2_nu")
other = [k for k in range(len(names)) if k != i]
print(
    "held faces  :",
    [
        (a["label"], round(a["multiplier"], 3))
        for a in H["constraints_postfit"]["active"]
    ],
)
print(
    "frozen faces:",
    [
        (a["label"], round(a["multiplier"], 3))
        for a in F["constraints_postfit"]["active"]
    ],
)
CH, CF = H["cov"].get().values(), F["cov"].get().values()


def rel(a, b):
    a, b = np.asarray(a), np.asarray(b)
    scale = np.max(np.abs(b))
    return (
        float(np.max(np.abs(a - b)) / scale)
        if scale > 0
        else float(np.max(np.abs(a - b)))
    )


print(f"sigma_tot held {np.sqrt(CH[0, 0]):.6f}  frozen {np.sqrt(CF[0, 0]):.6f}")
print(
    f"cov (lambda2_nu excluded): max|diff|/max = {rel(CH[np.ix_(other, other)], CF[np.ix_(other, other)]):.2e}"
)
print(f"held cov row lambda2_nu exactly 0: {np.all(CH[i] == 0)}")
for k in ("impacts", "impacts_grouped", "global_impacts", "global_impacts_grouped"):
    h, f = H[k].get(), F[k].get()
    lh, lf = list(h.axes["impacts"]), list(f.axes["impacts"])
    common = [l for l in lh if l in lf]
    vh = h.values()[0][[lh.index(l) for l in common]]
    vf = f.values()[0][[lf.index(l) for l in common]]
    fin = np.isfinite(vh) & np.isfinite(vf)
    nanmatch = np.array_equal(np.isnan(vh), np.isnan(vf))
    extra = sorted(set(lh) ^ set(lf))
    print(
        f"{k:24s} n={len(common):5d} max|held-frozen| = {np.max(np.abs(vh[fin] - vf[fin])):.2e} "
        f"(max rel {rel(vh[fin], vf[fin]):.1e}); NaN pattern equal: {nanmatch}; only in one: {extra}"
    )
    if k == "impacts":
        print(
            f"   held impact of lambda2_nu on the POI: {h.values()[0][lh.index('lambda2_nu')]}"
        )
# vs NOLAT_PF (all3-local): traditional identical algebra; global stat differs by the removed correction
for k in ("impacts_grouped", "global_impacts_grouped"):
    h, p = H[k].get(), PF[k].get()
    lh, lp = list(h.axes["impacts"]), list(p.axes["impacts"])
    vh = h.values()[0]
    vp = p.values()[0][[lp.index(l) for l in lh]]
    d = np.abs(vh - vp)
    j = int(np.nanargmax(d))
    print(f"held vs NOLAT_PF {k:24s}: largest |diff| {d[j]:.3e} at {lh[j]}")
    s = lh.index("stat")
    print(
        f"   stat: held {vh[s]:.6f}  NOLAT_PF {vp[s]:.6f}  stat_PF^2 - stat_held^2 = {vp[s]**2 - vh[s]**2:.4e}"
    )
g = H["impacts_grouped"].get()
lg = list(g.axes["impacts"])
v = g.values()[0]
print(
    "held traditional grouped (rabbit units; x2 = alphaS 1e-3):",
    {
        l: round(float(v[lg.index(l)]), 4)
        for l in (
            "stat",
            "binByBinStat",
            "resumNonpert",
            "scetlibNPFeff",
            "scetlibNPgammaNu",
            "pdfEig",
            "resumTNP",
        )
    },
)
gg = H["global_impacts_grouped"].get()
lgg = list(gg.axes["impacts"])
vg = gg.values()[0]
print("held global stat:", vg[lgg.index("stat")], " total:", np.sqrt(CH[0, 0]))
