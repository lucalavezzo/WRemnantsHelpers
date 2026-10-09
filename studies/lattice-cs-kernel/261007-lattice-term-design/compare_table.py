"""Cheap check: SCETlib's own CS kernel (AD-kernel gamma_nu_resummed, = qT::Gamma_nu analytic, the cache.conf
settings) vs the SHIPPED pert table of the current lattice plugin (WRemnants 3ef3efb9, built from our_cs_kernel.py
with the numerically EXACT RGE), at the 21 ASWZ points; and what the difference does to the lattice-only fit.

Inputs: proto/out_anchor.txt (gz_proto at alpha_s 0.118, TNPs 0, lambda (2, 0.15, 0)), the shipped npz.
Everything here is at the PUBLIC anchor (alpha_s(mZ) = 0.118): no fit result, nothing blinded.
"""

import importlib.util
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
MOD = os.path.join(WREM, "wremnants/postprocessing/scetlib_ad/lattice_cs_chi2.py")
spec = importlib.util.spec_from_file_location("lcs", MOD)
lcs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lcs)

d = np.load(lcs.DEFAULT_INPUTS)
rows = [
    np.array(l.split(), float)
    for l in open(os.path.join(HERE, "proto", "out_anchor.txt"))
    if not l.startswith("#")
]
A = np.array(rows)
b, z_cls_an, z_ker, z_cls_ex, z_ker_pert = A[:, 0], A[:, 1], A[:, 2], A[:, 3], A[:, 4]
grad = A[:, 5:11]  # d gamma_zeta / d (alphas, tnp_cusp, tnp_gnu, linf, l2, l4)
assert np.allclose(b, d["b_fm"], atol=1e-12)
np_part = z_ker - z_ker_pert
z_ex_pert = z_cls_ex - np_part

out = {}
sig = np.sqrt(np.diag(d["cov_stat"]))
out["max|kernel - class analytic| (zeta)"] = float(np.max(np.abs(z_ker - z_cls_an)))
out["max|exact-RGE class pert - shipped table pert|"] = float(
    np.max(np.abs(z_ex_pert - d["pert"]))
)
delta = z_ker_pert - d["pert"]
out["analytic(SCETlib fit default) - table: range"] = [
    float(delta.min()),
    float(delta.max()),
]
out["... in sigma_lat (stat diag): max"] = float(np.max(np.abs(delta) / sig))
# derivatives: SCETlib analytic (clad) vs shipped (exact-RGE FD) tables
for name, col, key in (
    ("d/d alpha_s", 0, "dpert_dalphas"),
    ("d/d theta_cusp", 1, "dpert_dtnp_cusp1"),
    ("d/d theta_gnu", 2, "dpert_dtnp_nu1"),
):
    t = d[key]
    out[f"{name}: max|clad(analytic) - table(exact)|"] = float(
        np.max(np.abs(grad[:, col] - t))
    )
    out[f"{name}: max rel"] = float(
        np.max(np.abs(grad[:, col] - t) / np.maximum(np.abs(t), 1e-12))
    )
# NP Jacobian (l2, l4) vs the plugin's analytic tanh derivative at (linf 2, l2 0.15, l4 0)
core = lcs.LatticeCSCore(syst="Jnf+Jbt")
u = core.u
th = np.tanh(0.15 * u / 2.0)
dz_dl2 = -0.5 * (1 - th**2) * u
dz_dl4 = -0.5 * (1 - th**2) * u * u
out["NP jac l2: max|clad - analytic tanh|"] = float(np.max(np.abs(grad[:, 4] - dz_dl2)))
out["NP jac l4: max|clad - analytic tanh|"] = float(np.max(np.abs(grad[:, 5] - dz_dl4)))
out["NP value: max|SCETlib NP - plugin np_zeta|"] = float(
    np.max(np.abs(np_part - core.np_zeta(u, 2.0, 0.15, 0.0)))
)


# what the analytic-vs-exact difference does to the lattice-only fit (syst Jnf+Jbt, linf = 2, k1 profiled)
def lattice_fit(pert):
    c = lcs.LatticeCSCore(syst="Jnf+Jbt")
    c.pert = pert
    c.c = c.pert - c.y
    res, lam = c.fit()
    return c, res, lam


c0, r0, l0 = lattice_fit(d["pert"])
c1, r1, l1 = lattice_fit(z_ker_pert)
out["lattice-only fit, table pert: chi2_min, l2, l4"] = [
    float(r0.fun),
    l0["lambda2_nu"],
    l0["lambda4_nu"],
]
out["lattice-only fit, SCETlib analytic pert: chi2_min, l2, l4"] = [
    float(r1.fun),
    l1["lambda2_nu"],
    l1["lambda4_nu"],
]
# shift in units of the stat+syst GN sigma (Jnf+Jbt: 0.0429, 0.00337 per 261006 Result 6)
out["shift (l2, l4) / sigma(Jnf+Jbt)"] = [
    (l1["lambda2_nu"] - l0["lambda2_nu"]) / 0.0429,
    (l1["lambda4_nu"] - l0["lambda4_nu"]) / 0.00337,
]
# Delta chi2 at fixed reference points when the pert part is swapped
for lab, lam in (
    (
        "NOMSTIFF (0.0643, 0)",
        dict(lambda_inf_nu=2.0, lambda2_nu=0.0643, lambda4_nu=0.0),
    ),
    (
        "LATCHI8 (0.0295, 0.0073)",
        dict(lambda_inf_nu=2.0, lambda2_nu=0.0295, lambda4_nu=0.0073),
    ),
):
    out[f"chi2 at {lab}: table, analytic"] = [c0.chi2(lam), c1.chi2(lam)]

json.dump(out, open(os.path.join(HERE, "compare_table.json"), "w"), indent=1)
for k, v in out.items():
    print(f"{k:70s} {v}")

# per-point d gamma_zeta / d alpha_s, and the alpha_s pull dchi2/dalpha_s at LATCHI8's CS point, table vs SCETlib
print("b_fm  dP/das table(exact)  clad(analytic)")
for i in np.argsort(b):
    print(f"{b[i]:.2f}  {d['dpert_dalphas'][i]: .4f}  {grad[i, 0]: .4f}")
lam8 = dict(lambda_inf_nu=2.0, lambda2_nu=0.0295, lambda4_nu=0.0073)
g_tab = float(2.0 * c0.r0(lam8) @ c0.M @ d["dpert_dalphas"])
g_an = float(2.0 * c1.r0(lam8) @ c1.M @ grad[:, 0])
out["dchi2/dalpha_s at LATCHI8 lambda (Jnf+Jbt): table, SCETlib, ratio"] = [
    g_tab,
    g_an,
    g_an / g_tab,
]
print(
    "dchi2/dalpha_s at LATCHI8 lambda (Jnf+Jbt): table, SCETlib, ratio",
    g_tab,
    g_an,
    g_an / g_tab,
)
json.dump(out, open(os.path.join(HERE, "compare_table.json"), "w"), indent=1)
