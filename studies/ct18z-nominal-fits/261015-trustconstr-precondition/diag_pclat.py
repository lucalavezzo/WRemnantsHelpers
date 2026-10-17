"""Why is PCLAT (preconditioned trust-constr, cold) slower than LAT? Cheap diagnosis, no AD cache.

(1) Where PCLAT's iterate (its periodic snapshot) has moved, vs the cold anchor and LAT's converged minimum,
    per parameter class (ParamModel params / constrained nuisances / unconstrained nuisances).
(2) The real NPDomainConstraints rows (margin=0): values at anchor, PCLAT iterate, LAT minimum (which row is
    violated in PCLAT).
(3) The chain rule on the REAL rows: rabbit's adapter in y vs finite differences of c(x_ref + T y), T a dense
    spectral transform from a synthetic ill-conditioned matrix, at the PCLAT iterate.
Run inside the container with the pinned rabbit first on PYTHONPATH.
"""

import os

os.environ.setdefault("HDF5_USE_FILE_LOCKING", "FALSE")

import h5py
import numpy as np
import scipy
import tensorflow as tf
from wums import ioutils

from rabbit import preconditioner as precond
from rabbit.constraints import scipy_adapter
from rabbit.inputdata import FitInputData

CARD = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
V = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_tc_precond_validation"
N = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits"


def snap(path):
    with h5py.File(path, "r") as f:
        names = [
            n.decode() if isinstance(n, bytes) else str(n) for n in f["parms"][...]
        ]
        return names, np.asarray(f["x"][...], dtype=np.float64)


names, x_pc = snap(f"{V}/snapshot_fitresults_PCLAT.hdf5")
names_l, x_lat = snap(f"{N}/snapshot_fitresults_LAT.hdf5")
assert names == names_l
# the cold anchor: PCLAT's own output file is still open for writing, so take the prefit vector of a finished
# fit with the same card and model (V2, 2026-10-13); the prefit point does not depend on priors / regularizers
with h5py.File(
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261013_constraints_class_validation/fitresults_V2.hdf5",
    "r",
) as f:
    res = ioutils.pickle_load_h5py(f["results"])
    hp = res["parms_prefit"].get()
pnames = [str(a) for a in hp.axes[0]]
assert pnames == names, "prefit parms order differs"
x0 = np.asarray(hp.values(), dtype=np.float64)
print(
    "anchor (V2 prefit): max|x0| over nuisances",
    np.max(np.abs(x0[-len(FitInputData(CARD).systs) :])),
)

indata = FitInputData(CARD)
nsyst = len(indata.systs)
npm = len(names) - nsyst
cw = np.asarray(indata.constraintweights)
cls = np.array(["model"] * npm + ["nuis_constr" if w > 0 else "nuis_free" for w in cw])
print(
    f"params: {len(names)} = {npm} ParamModel + {nsyst} systs ({int((cw > 0).sum())} constrained)"
)

d_pc, d_lat = x_pc - x0, x_lat - x0
print(
    "\n(1) displacement from the cold anchor (fitter coordinates; constrained nuisances in prior sigma)"
)
for c in ("model", "nuis_constr", "nuis_free"):
    m = cls == c
    if not m.any():
        continue
    print(
        f"  {c:12s} n={m.sum():5d}  |d|_2 PCLAT {np.linalg.norm(d_pc[m]):9.3g}  LAT-min {np.linalg.norm(d_lat[m]):9.3g}"
        f"   max|d| PCLAT {np.max(np.abs(d_pc[m])):8.3g}  LAT-min {np.max(np.abs(d_lat[m])):8.3g}"
    )
m = cls == "nuis_constr"
print(
    f"  prior term sum(theta^2)/2 over constrained nuisances: PCLAT {0.5*np.sum(x_pc[m]**2):.4g}  LAT-min {0.5*np.sum(x_lat[m]**2):.4g}"
)
# fraction of the way to LAT's minimum, along LAT's displacement, per class
for c in ("model", "nuis_constr"):
    mm = cls == c
    proj = d_pc[mm] @ d_lat[mm] / max(d_lat[mm] @ d_lat[mm], 1e-300)
    print(
        f"  {c}: projection of PCLAT's move on LAT's (1 = arrived): {proj:.3f}; orthogonal part {np.linalg.norm(d_pc[mm] - proj*d_lat[mm]):.3g}"
    )
print("  model params, anchor / PCLAT / LAT-min:")
for i in range(npm):
    print(
        f"    {names[i]:28s} {x0[i]:+10.4f} {x_pc[i]:+10.4f} {x_lat[i]:+10.4f}"
        if names[i] != "alphaS"
        else f"    {'alphaS':28s} (not printed: blinded)"
    )
top = np.argsort(-np.abs(d_pc))[:15]
print(
    "  largest PCLAT moves:",
    ", ".join(
        f"{names[i]}({cls[i]}) {d_pc[i]:+.3g} [LAT {d_lat[i]:+.3g}]"
        for i in top
        if names[i] != "alphaS"
    ),
)

print("\n(2) NPDomainConstraints rows (margin=0)")
from wremnants.postprocessing.scetlib_ad import np_damping_wall as W  # noqa: E402

con = W.NPDomainConstraints(indata, "margin=0")
con.set_layout(np.array(names))
for lab, lo, a, b, c in zip(
    con.labels,
    con.lower,
    con.values(tf.constant(x0)).numpy(),
    con.values(tf.constant(x_pc)).numpy(),
    con.values(tf.constant(x_lat)).numpy(),
):
    print(
        f"  {lab:45s} lb {lo:+.3g}: anchor {a:+.5g}  PCLAT {b:+.5g}{'  VIOLATED' if b < lo else ''}  LAT-min {c:+.5g}"
    )

print("\n(3) chain rule on the real rows at the PCLAT iterate")
cols = np.asarray(con.parameter_indices())
n = len(names)
rng = np.random.default_rng(1)
# synthetic ill-conditioned reference matrix over every parameter: dense coupling on the NP block + a scale spread
A = rng.normal(size=(n, n)) / np.sqrt(n)
H = A @ A.T + np.diag(np.logspace(-3, 3, n)[rng.permutation(n)])
pc = precond.Preconditioner.from_hessian(
    H, x_pc, [("all", np.arange(n))], transform="spectral"
)
assert pc.enabled


def val_jac(x):
    xv = tf.Variable(x)
    with tf.GradientTape() as t:
        c = con.values(xv)
    return c.numpy(), t.jacobian(c, xv).numpy()


def hvp(x, v):
    def mv(p):
        xv = tf.Variable(x)
        with tf.GradientTape() as t2:
            with tf.GradientTape() as t1:
                s = tf.tensordot(con.values(xv), tf.constant(v), 1)
            g = t1.gradient(s, xv)
        return t2.gradient(g, xv, output_gradients=tf.constant(np.ravel(p))).numpy()

    return scipy.sparse.linalg.LinearOperator(
        (n, n), matvec=mv, rmatvec=mv, dtype=np.float64
    )


(nlc,), info = scipy_adapter.build_nonlinear_constraints(
    val_jac,
    hvp,
    x_pc,
    con.lower,
    con.upper,
    con.labels,
    to_physical=pc.to_physical,
    jac_to_internal=pc.jac_to_internal,
    hessp_to_internal=pc.hessp_to_internal,
)
live = info["live"]
y = np.zeros(n)
Jy = nlc.jac(y)
h = 1e-6
# FD of c(theta(y)) along random directions (a full FD Jacobian would be n evaluations)
for k in range(3):
    p = rng.normal(size=n)
    fd = (nlc.fun(y + h * p) - nlc.fun(y - h * p)) / (2 * h)
    print(
        f"  J_y p vs FD: max rel err {np.max(np.abs(Jy @ p - fd) / np.maximum(np.abs(fd), 1e-12)):.2e}"
    )
    v = rng.normal(size=int(live.sum()))
    hfd = (nlc.jac(y + h * p) - nlc.jac(y - h * p)).T @ v / (2 * h)
    hy = nlc.hess(y, v).matvec(p)
    print(
        f"  (T^T d2c T) p vs FD of J_y: max abs err {np.max(np.abs(hy - hfd)):.2e} (scale {np.max(np.abs(hfd)):.2e})"
    )
