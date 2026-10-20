"""Provenance check of the gen-level card + its upstream unfolding (real data? toys? binning?). No alpha_s values read."""

import sys, h5py, numpy as np
from wums import ioutils

CE = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
cards = {
    "iter0": f"{CE}/261009_ad_genlevel_iter0/sigmaUL_iter0_ad_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_adcorrAV_alphaS.hdf5",
    "y5": f"{CE}/261013_ad_genlevel_y5/sigmaUL_y5_ad_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_adcorrAV_alphaS.hdf5",
}


def walk(m, depth=0, path=""):
    if isinstance(m, dict):
        for k, v in m.items():
            if k in ("command", "args"):
                s = str(v)
                print(f"{'  '*depth}{path}/{k}: {s[:1500]}")
            elif isinstance(v, dict) and depth < 6:
                walk(v, depth + 1, path + "/" + str(k))


for tag, p in cards.items():
    print("=" * 30, tag, p)
    with h5py.File(p, "r") as f:
        print(list(f.keys()))
        meta = ioutils.pickle_load_h5py(f["meta"])
        ci = meta["channel_info"]
        for ch, info in ci.items():
            print(
                ch,
                [(a.name, list(np.round(a.edges, 3))) for a in info["axes"]],
                "masked",
                info.get("masked"),
            )
        d = f["hdata_obs"][...] if "hdata_obs" in f else None
        print(
            "nsysts",
            len(f["hsysts"]) if "hsysts" in f else None,
            "systs:",
            [s.decode() if isinstance(s, bytes) else s for s in f["hsysts"][...]][:20],
        )
        walk(meta)
