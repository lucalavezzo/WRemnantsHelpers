#!/usr/bin/env python3
"""Dump the command / args / parameter lists / NLL of every fit in the comparison (no cache)."""
import json, sys
import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
FITS = dict(
    LAT=f"{A}/261015_ct18z_nominal_fits/fitresults_LAT.hdf5",
    LAT_snap=f"{A}/261015_ct18z_nominal_fits/snapshot_fitresults_LAT.hdf5",
    LAT_FF=f"{A}/261016_face_held_impacts/fitresults_LAT_facefix.hdf5",
    NOLAT_snap=f"{A}/261015_ct18z_nominal_fits/snapshot_fitresults_NOLAT.hdf5",
    NOLAT_PF=f"{A}/261016_nolat_postfit/fitresults_NOLAT_PF.hdf5",
    V3=f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5",
    V2=f"{A}/261013_constraints_class_validation/fitresults_V2.hdf5",
    HESSV2=f"{A}/261013_constraints_class_validation/fitresults_HESSV2.hdf5",
    XWSTIFF=f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
    NOMSTIFF=f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
    NOMTMDFREE=f"{A}/261005_tmd_priors_free/fitresults_NOMTMDFREE.hdf5",
    C2A=f"{A}/261008_c2_wall_test/fitresults_C2A.hdf5",
    V1=f"{A}/261013_constraints_class_validation/fitresults_V1.hdf5",
)
for k, p in FITS.items():
    try:
        fr, meta = io_tools.get_fitresult(p, None, meta=True)
    except Exception as e:
        print(f"== {k}: FAILED {e}")
        continue
    mi = meta.get("meta_info", {})
    h = fr["parms"].get()
    nm = [str(n) for n in h.axes[0]]
    keys = list(fr.keys())
    print(f"== {k}  {p}")
    print("  keys:", keys)
    for kk in ("nllvalreduced", "nllvalfull", "edmval"):
        if kk in fr:
            print(f"  {kk} = {fr[kk]!r}")
    print("  nparms", len(nm), "first 50:", nm[:50])
    print("  command:", mi.get("command", "")[:4000])
    pp = meta.get("param_priors")
    if pp is not None:
        pn = [n.decode() if isinstance(n, bytes) else str(n) for n in pp["params"]]
        msk = np.asarray(pp["mask"])
        sg = np.asarray(pp["sigmas"], float)
        print(
            "  param_priors: n",
            len(pn),
            "masked",
            int(msk.sum()),
            "free:",
            [n for i, n in enumerate(pn) if not msk[i]],
        )
        print(
            "   TMD/CS sig:",
            {n: float(sg[i]) for i, n in enumerate(pn) if "lambda" in n},
        )
    print("  meta keys:", list(meta.keys()), " meta_info keys:", list(mi.keys())[:30])
