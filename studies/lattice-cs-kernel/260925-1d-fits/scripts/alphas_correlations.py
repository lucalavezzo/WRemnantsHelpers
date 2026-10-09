import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
for k, f in [
    ("P1DWALL", "260925_1d_fits/P1DWALL/fitresults_P1DWALL.hdf5"),
    ("P1DUNW", "260925_1d_fits/P1DUNW/fitresults_P1DUNW.hdf5"),
    ("CCWALLWARMPF", "260917_cc_fits_wall/fitresults_CCWALLWARMPF.hdf5"),
    ("CCKRYLOVWARM", "260917_cc_fits_hvpfix/fitresults_CCKRYLOVWARM.hdf5"),
]:
    r = io_tools.get_fitresult(f"{A}/{f}")
    h = r["parms"].get()
    n = [str(x) for x in h.axes[0]]
    C = r["cov"].get().values()
    i = n.index("alphaS")
    s = np.sqrt(np.diag(C))
    rho = C[i] / (s[i] * s)
    top = sorted(
        [(n[j], rho[j], h.values()[j], s[j]) for j in range(len(n)) if j != i],
        key=lambda x: -abs(x[1]),
    )[:8]
    print(f"== {k}: rho(alphaS, x) top:")
    for nm, rr, v, e in top:
        print(f"   {nm:45s} rho={rr:+.2f}  theta={v:+.2f} +- {e:.2f}")
