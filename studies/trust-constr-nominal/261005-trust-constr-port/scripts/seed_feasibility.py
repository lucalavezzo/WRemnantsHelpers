"""Constraint values (margin 0) of each census seed, and its distance from NOMSTIFF in NOMSTIFF sigma units.
Never prints alphaS (only norms over all parameters)."""

import glob
import numpy as np
import tensorflow as tf
from rabbit import inputdata, io_tools
from rabbit.mappings import helpers as mh
import npwall_tc

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
REF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
CARD = f"{A}/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5"


def load(p):
    fr = io_tools.get_fitresult(p, None)
    h = fr["parms"].get()
    return (
        np.array([str(n) for n in h.axes[0]]),
        np.asarray(h.values(), float),
        np.sqrt(np.asarray(h.variances(), float)),
    )


names, xn, sn = load(REF)
indata = inputdata.FitInputData(CARD)
mapping = mh.load_mapping(
    "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
    indata,
    "margin=0",
)
reg = npwall_tc.NPDampingWallTC(mapping, dtype=tf.float64)
reg.set_expectations(tf.constant(xn), None, parms=names)
for p in sorted(glob.glob(f"{A}/261001_census_nominal/seeds/*.hdf5")):
    import h5py

    with h5py.File(p) as f:
        n = np.array(
            [v.decode() if isinstance(v, bytes) else str(v) for v in f["parms"][...]]
        )
        x = np.asarray(f["x"][...], float)
    assert (n == names).all()
    v, lb = reg.constraint_spec(tf.constant(x), None)
    v = v.numpy()
    d = (x - xn) / sn
    print(
        f"{p.split('/')[-1]:16s} min(c-lb)={np.min(v-lb.numpy()):+.4g} feasible={bool(np.all(v>=lb.numpy()))} "
        f"c=[{', '.join(f'{c:+.4f}' for c in v)}] ||dtheta/sig||={np.linalg.norm(d):.1f} max|d|={np.max(np.abs(d)):.1f}"
    )
