"""Physical NP lambdas, wall penalty and lattice term at a rabbit snapshot (x vector), card-A l4zero setup."""

import sys, h5py, numpy as np
from rabbit import inputdata
from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall

CARD = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5"
f = h5py.File(sys.argv[1], "r")
names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["parms"][...]]
th = dict(zip(names, f["x"][...]))
inp = wall.resolve_wall_inputs(inputdata.FitInputData(CARD))
phys = {
    n: (
        float(wall.physical_from_theta(inp["specs"][n], th[n]))
        if n in th
        else float(inp["anchors"][n])
    )
    for n in inp["names"]
}
conds = wall.damping_conditions(inp["np_model"], inp["np_model_nu"], inp["ymax"])
held = {"lambda_inf", "lambda_inf_nu", "lambda4_nu"}
pen = sum(
    c.penalty(phys, wall.numpy_relu2) for c in conds if not set(c.names) <= held
) * np.exp(10.0)
with h5py.File(CARD) as g:
    t = g["external_terms/lattice_cs"]
    gr = t["grad_values"][...]
    H = t["hess_dense"][...].reshape(1, 1)
x = np.array([th["lambda2_nu"]])
lext = float(gr @ x + 0.5 * x @ H @ x) + 0.5 * float(gr @ np.linalg.inv(H) @ gr)
print({k: round(v, 6) for k, v in phys.items()})
print(
    f"wall penalty (tau=5, active conditions) = {pen:.6f}   lattice lext = {lext:.6f}"
)
