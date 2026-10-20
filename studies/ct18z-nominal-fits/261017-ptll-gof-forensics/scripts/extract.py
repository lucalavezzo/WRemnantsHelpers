"""Extract the arrays this task needs from the existing fitresults into one npz per config.

No fit, no cache load: reads only the saved rabbit fitresults (M0 = analysis fit, M1 = the
saturated ptll-projection sub-fit). alphaS is never printed; its (blinded) value is stored
only so indices line up and is masked by the analysis script.

Usage: python extract.py <outdir>
"""

import sys

import h5py
import numpy as np
from wums import ioutils

BASE = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CONFIGS = {
    # M0 parms/cov: face-held rerun of LAT; M1: converged combined-fix sub-fit (SATWSPC).
    "LAT": dict(
        m0=f"{BASE}/261016_face_held_impacts/fitresults_LAT_facefix.hdf5",
        m1=f"{BASE}/261016_saturated_subfit_diagnosis/fitresults_SATWSPC_LAT.hdf5",
        m0plain=f"{BASE}/261015_ct18z_nominal_fits/fitresults_LAT.hdf5",
    ),
    "NOLAT": dict(
        m0=f"{BASE}/261016_nolat_postfit/fitresults_NOLAT_PF.hdf5",
        m1=f"{BASE}/261016_nolat_postfit/fitresults_NOLAT_PF.hdf5",
        m0plain=None,
    ),
}
MAP = "Project ch0 ptll"


_OPEN = []


def load(path):
    f = h5py.File(path, "r")
    _OPEN.append(f)  # keep open: the proxies read lazily
    return ioutils.pickle_load_h5py(f["results"]), ioutils.pickle_load_h5py(f["meta"])


def main(outdir):
    for cfg, paths in CONFIGS.items():
        out = {}
        r0, meta0 = load(paths["m0"])
        P0 = r0["parms"].get()
        out["names0"] = np.array(list(P0.axes[0]))
        out["x0"] = P0.values()
        out["cov0"] = r0["cov"].get().values()
        Pp = r0["parms_prefit"].get()
        out["names_prefit"] = np.array(list(Pp.axes[0]))
        out["x_prefit"] = Pp.values()
        out["var_prefit"] = Pp.variances()
        if "cov_released" in r0:
            out["cov0_released"] = r0["cov_released"].get().values()
        out["nll0"] = float(r0["nllvalreduced"])
        mp = r0["mappings"][MAP]
        for k in ("chi2", "ndf", "chi2_prefit"):
            out[k] = float(mp[k])
        ch = mp["channels"]["ch0"]
        for k in ch:
            h = ch[k].get()
            out[f"h_{k}"] = h.values()
            if h.variances() is not None:
                out[f"hvar_{k}"] = h.variances()
            out["edges"] = h.axes[0].edges

        r1, _ = load(paths["m1"])
        sf = r1["mappings"][MAP]["saturated_fit"]
        P1 = sf["parms"].get()
        out["names1"] = np.array(list(P1.axes[0]))
        out["x1"] = P1.values()
        out["cov1"] = sf["cov"].get().values()
        out["nll1"] = float(sf["nllvalreduced"])
        out["nll0_m1file"] = float(r1["nllvalreduced"])
        out["q"] = float(r1["mappings"][MAP]["chi2_saturated"])
        ms = sf["minimizer_status"]
        out["m1_labels"] = np.array(ms.get("constraint_labels", []))
        out["m1_cvals"] = np.array(ms.get("constraint_values", []), dtype=float)
        out["m1_mult"] = np.array(ms.get("multipliers", []), dtype=float)
        # M0 x from the M1 file too (to check consistency)
        out["x0_m1file"] = r1["parms"].get().values()
        np.savez(f"{outdir}/arrays_{cfg}.npz", **out)
        print(cfg, "saved", len(out["names0"]), len(out["names1"]), "q", out["q"])


if __name__ == "__main__":
    main(sys.argv[1])
