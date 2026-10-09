"""Gate (b), cheap half (no SCETlib cache): at NOMSTIFF's x, the trust-constr constraint
values must equal the wall's condition values (margin 0), the Jacobian must touch only the
fitted lambdas, and the stiff penalty NOMSTIFF carried is computed so that
NLL_noPenalty(NOMSTIFF) = nllvalreduced - penalty can be checked against the trust-constr
start-loss line of fit A. Runs Fitter._constraint_val_jac itself (unbound) on a stand-in.
Never prints alphaS."""

import json
from types import SimpleNamespace

import numpy as np
import tensorflow as tf

from rabbit import inputdata, io_tools
from rabbit.fitter import Fitter
from rabbit.mappings import helpers as mh

import npwall_tc

REF = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
CARD = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5"
TAU = 8.0

fr, meta = io_tools.get_fitresult(REF, None, meta=True)
h = fr["parms"].get()
names = np.array([str(n) for n in h.axes[0]])
x = np.asarray(h.values(), dtype=np.float64)
nll_nom = float(fr["nllvalreduced"])

indata = inputdata.FitInputData(CARD)
mapping = mh.load_mapping(
    "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
    indata,
    "margin=0",
)
reg = npwall_tc.NPDampingWallTC(mapping, dtype=tf.float64)
reg.set_expectations(tf.constant(x), None, parms=names)

xt = tf.constant(x)
vals, lbs = reg.constraint_spec(xt, None)
vals, lbs = vals.numpy(), lbs.numpy()
phys = {k: float(v) for k, v in reg._physical(xt).items()}
face = np.array([float(c.value(phys, npwall_tc._w.numpy_relu2)) for c in reg._active])
pen_raw = float(reg.compute_nll_penalty(xt, None))
pen = pen_raw * np.exp(2 * TAU)
pen_np = sum(
    float(npwall_tc._w.numpy_relu2(c.bound - v)) for c, v in zip(reg._active, face)
) * np.exp(2 * TAU)

# the fitter's own constraint code path, on a stand-in object
stand = SimpleNamespace(
    regularizers=[reg],
    x=tf.Variable(xt),
    frozen_indices=np.array([]),
    _constraint_row_mask=None,
)
cv, jac = Fitter._constraint_val_jac(stand, x)
nz_cols = sorted(set(np.nonzero(np.abs(jac) > 0)[1].tolist()))

out = dict(
    nparms=len(names),
    lambdas_in_vector=[n for n in names if "lambda" in n],
    physical_lambdas={k: v for k, v in phys.items()},
    labels=[c.label for c in reg._active],
    constraint_values=vals.tolist(),
    lower_bounds=lbs.tolist(),
    face_values_numpy=face.tolist(),
    max_abs_diff_tf_vs_numpy=float(np.max(np.abs(vals - face))),
    fitter_path_max_abs_diff=float(np.max(np.abs(cv - vals))),
    jacobian_nonzero_columns=[str(names[i]) for i in nz_cols],
    penalty_tf_times_exp2tau=pen,
    penalty_numpy_times_exp2tau=pen_np,
    nllvalreduced_NOMSTIFF=nll_nom,
    nll_minus_penalty=nll_nom - pen,
)
print(json.dumps(out, indent=1))
json.dump(
    out,
    open(
        "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/trust-constr-nominal/261005-trust-constr-port/gate_b_constraints.json",
        "w",
    ),
    indent=1,
)
