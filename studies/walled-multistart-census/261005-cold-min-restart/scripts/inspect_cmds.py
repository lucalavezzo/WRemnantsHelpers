#!/usr/bin/env python3
"""Print the stored meta_info commands + param counts of the three reference fits (no alphaS values)."""
import shlex
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
for name, p in [
    ("NOMSTIFF", f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"),
    ("XWSTIFF", f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5"),
    ("CCWALLCOLDR", f"{A}/260917_cc_fits_wall/fitresults_CCWALLCOLDR.hdf5"),
]:
    fr, meta = io_tools.get_fitresult(p, None, meta=True)
    print("=====", name)
    print(meta["meta_info"]["command"])
    print("keys:", list(fr.keys())[:40])
    parms = fr["parms"].get()
    print(
        "nparms",
        len(parms.axes[0]),
        "nllvalreduced",
        float(fr["nllvalreduced"]),
        "edm",
        float(fr["edmval"]) if "edmval" in fr else None,
    )
