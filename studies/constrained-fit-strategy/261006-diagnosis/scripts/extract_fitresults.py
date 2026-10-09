#!/usr/bin/env python3
"""Extract x, names, cov, edmval, nll from the reference fitresults into one npz per fit on ceph.

No cache load: reads only the fitresult hdf5 files. Run in the container (needs rabbit io_tools).
alphaS stays in its blinded frame; nothing absolute is printed.
"""
import os
import sys

import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
OUT = f"{A}/261006_constrained_fit_diagnosis"
FITS = {
    "NOMSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
    "XWSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
    "XL4ZSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XL4ZSTIFF.hdf5",
    "CMR1A": f"{A}/261005_cold_min_restart/fitresults_CMR1A.hdf5",
    "CMR1B": f"{A}/261005_cold_min_restart/fitresults_CMR1B.hdf5",
    "HESSTCA": f"{A}/261005_trust_constr_nominal/fitresults_HESSTCA.hdf5",
    "TCA": f"{A}/261005_trust_constr_nominal/fitresults_TCA.hdf5",
    "TCB1": f"{A}/261005_trust_constr_nominal/fitresults_TCB1.hdf5",
}
SNAPS = {
    "CMR1A_snap": f"{A}/261005_cold_min_restart/snapshot_fitresults_CMR1A.hdf5",
    "CENS03R_snap": f"{A}/261001_census_nominal/snapshot_fitresults_CENS03R.hdf5",
    "TCB2_snap": f"{A}/261005_trust_constr_nominal/snapshot_fitresults_TCB2.hdf5",
}
os.makedirs(OUT, exist_ok=True)
for name, path in FITS.items():
    fr = io_tools.get_fitresult(path, None)
    h = fr["parms"].get()
    names = np.array([str(n) for n in h.axes[0]])
    d = dict(
        names=names,
        x=np.asarray(h.values(), float),
        var=np.asarray(h.variances(), float),
    )
    for k in ("nllvalreduced", "nllvalfull", "edmval"):
        try:
            d[k] = float(fr[k])
        except Exception:
            pass
    try:
        d["cov"] = np.asarray(fr["cov"].get().values(), float)
    except Exception as ex:
        print(f"{name}: no cov ({ex})")
    np.savez(f"{OUT}/{name}.npz", **d)
    print(
        name,
        len(names),
        {k: d[k] for k in ("nllvalreduced", "edmval") if k in d},
        "cov" in d,
    )
import h5py

for name, path in SNAPS.items():
    with h5py.File(path, "r") as f:
        print(name, list(f.keys()), dict(f.attrs))
        grp = f
        keys = list(f.keys())
        d = {}
        for k in keys:
            try:
                d[k] = np.asarray(f[k][()])
            except Exception:
                pass
    np.savez(f"{OUT}/{name}.npz", **{k: v for k, v in d.items() if v.dtype != object})
    print(name, {k: v.shape for k, v in d.items()})
