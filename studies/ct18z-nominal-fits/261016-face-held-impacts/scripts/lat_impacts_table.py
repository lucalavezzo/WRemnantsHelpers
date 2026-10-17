"""Read the LAT_facefix fitresult: covariance vs LAT's stored one, traditional and global grouped impacts on
the POI (alphaS), consistency checks. Prints sigmas / impacts only (never the alphaS value). Units: rabbit's
POI units; pullsAndImpacts.sh plots x2 (alpha_s in 1e-3)."""

import sys
import numpy as np
from rabbit import io_tools

NEW = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_face_held_impacts/fitresults_LAT_facefix.hdf5"
OLD = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits/fitresults_LAT.hdf5"
new, old = io_tools.get_fitresult(NEW), io_tools.get_fitresult(OLD)
C, C0 = new["cov"].get().values(), old["cov"].get().values()
p = 0
print("constraints_postfit:", new["constraints_postfit"])
print(
    f"sigma_tot new {np.sqrt(C[p, p]):.6f}  stored LAT {np.sqrt(C0[p, p]):.6f};  max|C-C_LAT|/max|C_LAT| = "
    f"{np.abs(C - C0).max() / np.abs(C0).max():.2e}"
)
names = list(np.array(new["parms"].get().axes["parms"]))
for nm in ("lambda2", "delta_lambda2"):
    i = names.index(nm)
    print(f"  sigma({nm}) = {np.sqrt(C[i, i]):.4g}")
rows = {}
for base in ("impacts", "global_impacts"):
    h = new[f"{base}_grouped"].get()
    labs = list(h.axes["impacts"])
    v = h.values()[p]
    rows[base] = dict(zip(labs, v))
    hu = new[base].get().values()[p]
    print(
        f"\n== {base}_grouped (alphaS row), {len(labs)} groups; finite: {np.all(np.isfinite(v))}"
    )
    for l, x in sorted(zip(labs, v), key=lambda t: -np.nan_to_num(t[1], nan=9)):
        print(f"   {l:40s} {x:.5f}   (x2 = {2 * x:.4f})")
    if base == "global_impacts":
        tot2 = (
            np.sum(hu**2)
            + rows[base]["binByBinStat"] ** 2
            + np.nan_to_num(rows[base]["stat"]) ** 2
        )
        print(
            f"   sum(per-source^2) + bbb^2 + stat^2 = {tot2:.6f}  vs  sigma_tot^2 = {C[p, p]:.6f}"
        )
        print(
            f"   remainder var_total - var_x0 - var_beta0 = {C[p, p] - np.sum(hu**2) - rows[base]['binByBinStat']**2:.6f}"
        )
    else:
        st, bb = rows[base]["stat"], rows[base]["binByBinStat"]
        print(
            f"   stat^2 + bbb^2 = {st**2 + bb**2:.6f} (= var with all constrained nuisances frozen); "
            f"syst = sqrt(tot^2 - that) = {np.sqrt(C[p, p] - st**2 - bb**2):.5f}"
        )
