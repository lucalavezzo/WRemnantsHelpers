import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"


def get(f):
    r = io_tools.get_fitresult(f"{A}/{f}")
    h = r["parms"].get()
    n = [str(x) for x in h.axes[0]]
    C = r["cov"].get().values()
    return n, h.values(), C


n2, v2, C2 = get("260917_cc_fits_wall/fitresults_CCWALLWARMPF.hdf5")
for k, f in [
    ("P1DWALL", "260925_1d_fits/P1DWALL/fitresults_P1DWALL.hdf5"),
    ("P1DUNW", "260925_1d_fits/P1DUNW/fitresults_P1DUNW.hdf5"),
]:
    n, v, C = get(f)
    ia, idl = n.index("alphaS"), n.index("delta_lambda2")
    dd = v[idl] - v2[n2.index("delta_lambda2")]
    pred = (
        C[ia, idl] / C[idl, idl] * dd
    )  # linear regression of alphaS on delta_lambda2 within the 1D fit
    obs = v[ia] - v2[n2.index("alphaS")]
    print(
        f"{k}: d(delta_lambda2) theta 1D-2D = {dd:+.3f}; alphaS shift predicted from it = {2*pred:+.2f}e-3; observed (vs CCWALLWARMPF) = {2*obs:+.2f}e-3"
    )
