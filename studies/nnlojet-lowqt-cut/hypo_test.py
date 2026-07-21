import numpy as np, glob, re
from wremnants.utilities.io_tools import input_tools

BASE = "/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib"
RESUM = f"{BASE}/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine_combined.pkl"
SING = f"{BASE}/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing_combined.pkl"
RDIR = "/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2/result/final"
hresum, hfo_sing = input_tools.read_scetlib_resum_and_fosing(
    RESUM, SING, ("Y", "qT"), charge=0, coeff=None
)
qte = hresum.axes["qT"].edges
ye = hresum.axes["Y"].edges
wq = np.diff(qte)
wy = np.diff(ye)
i0, i1 = list(ye).index(-2.5), list(ye).index(2.5)


def qt1gev(h, hypo):
    v = h[{"vars": 0}].values().squeeze()
    if hypo in ("qtdens", "qtydens"):
        v = v * wq[None, :]
    if hypo == "qtydens":
        v = v * wy[:, None]
    vy = v[i0:i1].sum(axis=0)
    out = {}
    for j, (a, b) in enumerate(zip(qte[:-1], qte[1:])):
        if b <= 30:
            out[int(a)] = out.get(int(a), 0) + vy[j]
    return out


# NNLOJET 1-GeV integrals |y|<2.5
f = {}


def num(x):
    return float(x.replace("p", "."))


for fn in glob.glob(f"{RDIR}/nnlo.ptz__*.dat"):
    m = re.search(r"ptz__(-?[\dp.]+)__(-?[\dp.]+)\.dat", fn)
    ylo, yhi = num(m.group(1)), num(m.group(2))
    if ylo < -2.5 or yhi > 2.5:
        continue
    for line in open(fn):
        if line.startswith("#"):
            continue
        v = line.split()
        if len(v) < 5:
            continue
        if float(v[0]) >= 30:
            continue
        f[int(float(v[0]))] = f.get(int(float(v[0])), 0) + float(v[3]) * 1e-3
print("NNLOJET sum qT[1,30], |y|<2.5:", f"{sum(f.values()):.0f} pb")
for hypo in ("int", "qtdens", "qtydens"):
    r = qt1gev(hresum, hypo)
    s = qt1gev(hfo_sing, hypo)
    print(
        f"\nhypo={hypo}: resum(qT<30)={sum(r.values()):.0f}  sing(qT<30)={sum(s.values()):.0f}"
    )
    for k in (5, 10, 15, 20, 25, 29):
        print(f"   qT {k}-{k+1}: FO/sing={f[k]/s[k]:6.3f}  sing/resum={s[k]/r[k]:6.3f}")
