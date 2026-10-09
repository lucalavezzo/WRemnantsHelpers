#!/usr/bin/env python3
"""Print non-command meta_info keys (git hashes etc.) of the reference fits."""
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
for name, p in [
    ("NOMSTIFF", f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"),
    ("XWSTIFF", f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5"),
    ("CCWALLCOLDR", f"{A}/260917_cc_fits_wall/fitresults_CCWALLCOLDR.hdf5"),
]:
    fr, meta = io_tools.get_fitresult(p, None, meta=True)
    mi = meta["meta_info"]
    print("=====", name, list(meta.keys()))
    for k, v in mi.items():
        if k != "command":
            print("  ", k, str(v)[:300])
