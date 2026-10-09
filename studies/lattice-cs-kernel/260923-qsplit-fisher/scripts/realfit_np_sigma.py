"""Postfit Hessian sigma of the NP lambdas (theta units -> physical) in the main real-data card-A fit.
alphaS is deliberately NOT printed (blinded)."""

import h5py, numpy as np
from wums import ioutils

F = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260917_cc_fits_hvpfix/fitresults_CCKRYLOVWARM.hdf5"
f = h5py.File(F, "r")
r = ioutils.pickle_load_h5py(f["results"])
print(r.keys())
p = r["parms"].get() if hasattr(r["parms"], "get") else r["parms"]
names = [str(x) for x in p.axes[0]]
W = {
    "lambda2": 0.5,
    "lambda4": 0.5,
    "delta_lambda2": 0.5,
    "lambda2_nu": 0.1,
    "lambda4_nu": 0.5,
}
cov = r["cov"].get() if "cov" in r else None
C = cov.values() if cov is not None else None
for n, w in W.items():
    i = names.index(n)
    print(
        f"{n:14s} sigma_theta={np.sqrt(p.variances()[i]):.4f}  sigma_phys={np.sqrt(p.variances()[i])*w:.4f}"
    )
if C is not None:
    idx = [names.index(n) for n in W]
    s = np.sqrt(np.diag(C)[idx])
    print("rho(l2nu,L2)=", C[idx[3], idx[0]] / s[3] / s[0])
anc = {
    "lambda2": 0.4,
    "lambda4": 0.4,
    "delta_lambda2": 0.0,
    "lambda2_nu": 0.15,
    "lambda4_nu": 0.0,
}  # card/cache anchor (check vs meta)
for n, w in W.items():
    i = names.index(n)
    print(f"{n:14s} theta={p.values()[i]:+.4f}  physical~{anc[n]+w*p.values()[i]:+.4f}")
