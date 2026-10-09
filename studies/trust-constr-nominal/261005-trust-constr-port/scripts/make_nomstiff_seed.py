"""NOMSTIFF's x as a flat seed (x + parms, NO cov): --noHessian refuses to load an external covariance.
The fitresult's parms histogram values ARE the raw Fitter.x vector (blinded coordinates), so this seed is exactly
NOMSTIFF's point. Never prints alphaS."""

import h5py, numpy as np
from rabbit import io_tools

REF = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
SEED = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/census_ref_seed_check"
OUT = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261005_trust_constr_nominal/seed_NOMSTIFF_nocov.hdf5"
ref_seed = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261001_census_nominal/seeds/cold_000.hdf5"
with h5py.File(ref_seed) as f:
    pdt = f["parms"].dtype
fr = io_tools.get_fitresult(REF, None)
h = fr["parms"].get()
names = np.array(h.axes["parms"]).astype(str)
x = np.asarray(h.values(), np.float64)
with h5py.File(OUT, "w") as f:
    f.create_dataset("x", data=x)
    f.create_dataset(
        "parms",
        data=(
            names.astype(pdt) if pdt.kind == "S" else names.astype(h5py.string_dtype())
        ),
    )
with h5py.File(OUT) as f:
    back = f["parms"][...].astype(str)
    assert (back == names).all() and np.array_equal(f["x"][...], x) and "cov" not in f
print("wrote", OUT, len(x), "parms dtype", pdt)
