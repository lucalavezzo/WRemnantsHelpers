"""State of a snapshot (x + parms): physical NP lambdas, constraint values (c - lb), Delta alphaS / sigma_XW against
XWSTIFF / XL4ZSTIFF / CMR1B. BLINDED: differences only. Usage: snapshot_state.py [PF]"""

import sys

import h5py
import numpy as np
import tensorflow as tf

import npwall_tc
from rabbit import inputdata, io_tools
from rabbit.mappings import helpers as mh

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD = (
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
REFS = {
    "XWSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
    "XL4ZSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XL4ZSTIFF.hdf5",
    "CMR1B": f"{A}/261005_cold_min_restart/fitresults_CMR1B.hdf5",
}
pf = sys.argv[1] if len(sys.argv) > 1 else "TCC1"
snap = f"{A}/261006_tc_from_C/snapshot_fitresults_{pf}.hdf5"


def load(p):
    h = io_tools.get_fitresult(p, None)["parms"].get()
    return (
        np.array([str(n) for n in h.axes[0]]),
        np.asarray(h.values(), float),
        np.sqrt(np.asarray(h.variances())),
    )


names, xw, sw = load(REFS["XWSTIFF"])
ip = int(np.where(names == "alphaS")[0][0])
with h5py.File(snap) as f:
    n = np.array(
        [v.decode() if isinstance(v, bytes) else str(v) for v in f["parms"][...]]
    )
    x = np.asarray(f["x"][...], float)
    at = dict(f.attrs)
assert (n == names).all()
wall = npwall_tc.NPDampingWallTC(
    mh.load_mapping(
        "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
        inputdata.FitInputData(CARD),
        "margin=0",
    ),
    dtype=tf.float64,
)
wall.set_expectations(tf.constant(xw), None, parms=names)
v, lb = wall.constraint_spec(tf.constant(x), None)
print(
    f"snapshot iteration {at.get('iteration')} loss {at.get('loss'):.6f} (-XW nopen {at.get('loss')-371.3283536451:+.5f})"
)
print(
    "c - lb [λ4_ν, λ2_ν, L2(0), B(0), L2(2.5), B(2.5)] =",
    np.array2string(v.numpy() - lb.numpy(), precision=5),
)
print(
    "lambdas:",
    {k: round(float(val), 6) for k, val in wall._physical(tf.constant(x)).items()},
)
for rn, p in REFS.items():
    nm, xr, _ = load(p)
    print(
        f"Delta alphaS vs {rn} = {(x[ip] - xr[list(nm).index('alphaS')]) / sw[ip]:+.4f} sigma_XW"
    )
