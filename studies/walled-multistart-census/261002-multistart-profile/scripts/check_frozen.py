#!/usr/bin/env python3
"""check_frozen.py PF [file]: is x[alphaS] in the fit output (snapshot or fitresult) bit-identical to the seed's?
Prints only the blinded DIFFERENCE (in sigma_NOM) and a bit-equality flag; never an absolute value.
"""
import sys
import h5py
import numpy as np

O = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261002_multistart_profile"
pf = sys.argv[1]
f = sys.argv[2] if len(sys.argv) > 2 else f"{O}/snapshot_fitresults_{pf}.hdf5"
with h5py.File(f"{O}/seeds/{pf}.hdf5", "r") as h:
    xs, ns = h["x"][...], h["parms"][...].astype(str)
ia = int(np.where(ns == "alphaS")[0][0])
with h5py.File(f, "r") as h:
    if "x" in h:
        x, n, reason = h["x"][...], h["parms"][...].astype(str), h.attrs.get("reason")
    else:
        from rabbit import io_tools

        fr = io_tools.get_fitresult(f, None)
        hp = fr["parms"].get()
        x, n, reason = (
            np.asarray(hp.values()),
            np.array(hp.axes[0]).astype(str),
            "fitresult",
        )
assert np.array_equal(n, ns)
d = x - xs
print(
    f"{pf} [{reason}] alphaS bit-identical to seed: {x[ia] == xs[ia]} ; |dx_alphaS| = {abs(d[ia]):.3e} ; "
    f"other params moved: max|dx| = {np.max(np.abs(np.delete(d, ia))):.3g}"
)
