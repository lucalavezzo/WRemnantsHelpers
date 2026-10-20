"""Four-way comparison (reco/gen x NOLAT/LAT) from the fitresults.

BLINDING: alphaS is blinded. This script never prints a stored alphaS value; it prints only sigma(alphaS) and
DIFFERENCES of stored values between fits in the SAME blinding frame (all four are in the real-data frame: reco by
'auto' on integer data, gen by --blindingFrame data -- checked from the fit meta below). The difference of stored
values equals the physical difference because the offset is identical (same name, same frame).
"""

import argparse, json
import numpy as np
from rabbit import io_tools
from wremnants.postprocessing.scetlib_ad import np_function_plots as nfp

CE = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
FITS = {
    "RECO_NOLAT": f"{CE}/261016_nolat_postfit/fitresults_NOLAT_PF.hdf5",
    "RECO_LAT": f"{CE}/261016_face_held_impacts/fitresults_LAT_facefix.hdf5",
    "GEN_NOLAT": f"{CE}/261017_gen_nominal_fits/fitresults_GEN_NOLAT_PF.hdf5",
    "GEN_LAT": f"{CE}/261017_gen_nominal_fits/fitresults_GEN_LAT_PF.hdf5",
}
AS_SCALE = 2e-3  # alphaS parameter unit -> alpha_s(mZ) (261013-gen-reco-alphas-delta: 0.242 theta = 0.00048)
LAMS = ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]

p = argparse.ArgumentParser()
p.add_argument("--fits", nargs="*", default=list(FITS))
p.add_argument("-o", "--out", default=None)
a = p.parse_args()

res = {}
stored = {}
for k in a.fits:
    path = FITS[k]
    fr, meta = io_tools.get_fitresult(path, None, meta=True)
    args = meta["meta_info"]["args"]
    names = [str(n) for n in fr["parms"].get().axes[0]]
    i = names.index("alphaS")
    cov = np.asarray(fr["cov"].get().values(), float)
    sig = float(np.sqrt(cov[i, i]))
    stored[k] = float(fr["parms"].get().values()[i])
    r = dict(
        path=path,
        blindingFrame=args.get("blindingFrame", "n/a (pre-196bfca)"),
        toys=args.get("toys"),
        nllvalreduced=float(fr["nllvalreduced"]) if "nllvalreduced" in fr else None,
        nllval=float(fr["nllval"]) if "nllval" in fr else None,
        edmval=float(fr["edmval"]) if "edmval" in fr else None,
        sigma_alphaS_theta=sig,
        sigma_alphaS_1e3=sig * AS_SCALE * 1e3,
    )
    # physical NP lambdas + active faces (the NP plotter's reader)
    _, post, _, faces = nfp.read_ad_fitresult(path, n_toys=0)
    r["lambdas"] = {n: float(post.values[n]) for n in LAMS}
    r["faces"] = faces
    # grouped impacts on alphaS in units of 1e-3 alpha_s (as the impact plots: x AS_SCALE*1e3)
    for typ in ("traditional", "global"):
        try:
            imp, lab = io_tools.read_impacts_poi(
                fr, "alphaS", grouped=True, impact_type=typ
            )
            r[f"{typ}_grouped_1e3"] = {
                str(l): round(float(v) * AS_SCALE * 1e3, 3)
                for l, v in sorted(
                    zip(lab, imp), key=lambda t: -abs(t[1]) if np.isfinite(t[1]) else 0
                )
            }
        except Exception as e:
            r[f"{typ}_grouped_1e3"] = f"n/a ({type(e).__name__}: {e})"
    for key in ("chi2", "ndf"):
        if key in fr:
            r[key] = float(fr[key])
    res[k] = r

# differences only (same frame), in theta, alpha_s, and sigma units
diffs = {}


def d(a_, b_):
    if a_ in stored and b_ in stored:
        dt = stored[a_] - stored[b_]
        diffs[f"{a_} - {b_}"] = dict(
            theta=dt,
            alpha_s=dt * AS_SCALE,
            in_sigma_of_second=dt / res[b_]["sigma_alphaS_theta"],
        )


d("RECO_LAT", "RECO_NOLAT")
d("GEN_LAT", "GEN_NOLAT")
d("GEN_NOLAT", "RECO_NOLAT")
d("GEN_LAT", "RECO_LAT")
del stored
out = dict(fits=res, alphaS_differences=diffs)
s = json.dumps(out, indent=1, default=str)
print(s)
if a.out:
    open(a.out, "w").write(s)
