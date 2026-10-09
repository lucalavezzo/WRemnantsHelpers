"""The SCETlib-native n_f-scheme alternative (gamma_nu_points nf=4, mu_match=1) vs the qT::Gamma_nu class, and the
resulting alternative kernel vs the old table's (m_b-decoupled, exact-RGE) one.

  alt(b) = 1/2 gamma^(5)(b, mu = 1 GeV) + 1/2 [gamma^(4)(b, 2 GeV) - gamma^(4)(b, 1 GeV)]
  gamma^(4): n_f = 4 in beta, cusp and boundary; alpha_s^(4)(1 GeV) := alpha_s^(5)(1 GeV)   ("n_f identified at 1 GeV")

i.e. our n_f = 5 kernel at 1 GeV, evolved to 2 GeV with the n_f = 4 cusp, which is the construction of the old table's
`pert_nf5_mu1match` (260923-scetlib-kernel-fit/kernel_fit.py::pert_tables), with alpha_s^(4) identified at 1 GeV instead
of decoupled at m_b(m_b), and SCETlib's analytic RGE instead of the exact one.

agent_setup.sh --scetlib /work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build -- python3 <this>
"""

import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)
from wremnants.postprocessing.scetlib_ad import xsec_backend as xb  # noqa: E402

CONF = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/ad_scetlib_caches/pdf62_y35_260921_y25/cache.conf"
D = np.load(
    os.path.join(
        WREM, "wremnants/postprocessing/scetlib_ad/data/lattice_aswz_inputs.npz"
    )
)
b_fm = np.array(D["b_fm"], float)
bT = b_fm * float(D["fm_to_gevinv"])
sig = np.sqrt(np.diag(D["cov_stat"]))
conf, sigma = xb.configure(CONF, threads=4)
sing, _ = sigma.sub_pieces()
names = list(sing.gradient_param_names())
p = np.array(sing.gradient_central(), float)
ix = {n: i for i, n in enumerate(names)}
p[ix["np_gnu_lambda_inf"]] = 0.0  # pert only
CLS = os.path.join(TASK, "classdrv", "gz_class")


def cls(mu, env):
    a = [
        repr(float(p[ix[n]])) for n in ("alphas", "tnp_gamma_cusp", "tnp_gamma_nu")
    ] + ["0.0", "0.15", "0.0", "0", repr(mu)]
    out = subprocess.run(
        [CLS, *a, *[repr(float(b)) for b in b_fm]],
        capture_output=True,
        text=True,
        check=True,
        env=dict(os.environ, **env),
    ).stdout
    return np.array(
        [float(ln.split()[2]) for ln in out.splitlines() if ln.strip()]
    )  # pert column


def g(mu, nf=0, mm=0.0):
    return 0.5 * np.asarray(sing.gamma_nu_points(bT, mu, p, 0, nf, mm)["value"])


res = {}
z4_2, z4_1 = g(2.0, 4, 1.0), g(1.0, 4, 1.0)
c4_2, c4_1 = cls(2.0, {"GZ_NF": "4", "GZ_ASMATCH": "1.0"}), cls(
    1.0, {"GZ_NF": "4", "GZ_ASMATCH": "1.0"}
)
res["nf4_vs_class_mu2"] = float(np.max(np.abs(z4_2 - c4_2)))
res["nf4_vs_class_mu1"] = float(np.max(np.abs(z4_1 - c4_1)))
z5_1, z5_2 = g(1.0), g(2.0)
res["nf5_mu1_vs_class"] = float(np.max(np.abs(z5_1 - cls(1.0, {}))))
alt = z5_1 + (z4_2 - z4_1)
shift_new = alt - z5_2
old_shift = np.array(D["pert_nf5_mu1match"], float) - np.array(D["pert"], float)
res["shift_new"] = list(shift_new)
res["shift_old_table"] = list(old_shift)
res["shift_new_range"] = [float(shift_new.min()), float(shift_new.max())]
res["shift_old_range"] = [float(old_shift.min()), float(old_shift.max())]
res["shift_new_minus_old_max"] = float(np.max(np.abs(shift_new - old_shift)))
res["shift_new_minus_old_rel"] = float(
    np.max(np.abs(shift_new - old_shift) / np.abs(old_shift))
)
res["shift_new_over_sigma_max"] = float(np.max(np.abs(shift_new) / sig))
for k, v in res.items():
    if not isinstance(v, list):
        print(f"{k:32s} {v}")
print("b_fm  shift_new  shift_old")
for b, a, o in zip(b_fm, shift_new, old_shift):
    print(f"{b:.2f} {a:+.6f} {o:+.6f}")
ok = (
    res["nf4_vs_class_mu2"] < 1e-12
    and res["nf4_vs_class_mu1"] < 1e-12
    and res["nf5_mu1_vs_class"] < 1e-12
)
res["PASS_class_identity"] = bool(ok)
print("class identity (nf=4 alternative and nf=5 at mu = 1):", "PASS" if ok else "FAIL")
json.dump(res, open(os.path.join(TASK, "test_nf_alt.json"), "w"), indent=1)
