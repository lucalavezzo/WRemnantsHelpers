"""Offline tests of the native lattice term (WRemnants lattice_cs_term.LatticeCSTerm), no big cache, no fitter.

A small cache (4 bins, pdf62_y35 runcard, 53 SCETlib parameters as in the fit) is loaded so that the kernel snapshot is
checked against real rules (status 1). A MOCK param model supplies scetlib_full_vector_tf with the real REPARAM maps
(alphaS 0.118 + 0.002 t, lambda2_nu 0.15 + 0.1 t, lambda4_nu 0 + 0.5 t, TNPs identity, TMD lambda2 0.4 + 0.5 t); the real
param model's function is exercised in the gated rabbit checks.

T1  load-time: stat-only lattice fit on SCETlib's kernel reproduces the design numbers (chi2 6.703, l2 0.1855, l4 -0.00597)
T2  V4: new chi2 == the OLD term's formula (same M, its tanh NP, k1 profiled) with the table pert replaced by SCETlib's
    pert at the same alpha_s / TNPs (<= 1e-10), at NOMSTIFF / LATCHI8 / LATFULL8-like lambdas and alpha_s 0.116/0.118/0.120,
    TNPs 0 and +-1.  Also new - old (table, pert=live) chi2 at those points: the kernel swap itself.
T3  V3 through the TF path the fitter uses: d penalty / d theta (tape) and the Hessian (nested tapes, and forward-over-
    reverse) vs Richardson FD of the penalty; exactly zero for a parameter the kernel does not depend on (TMD lambda2).
T4  exp(2 tau) compensation (tau=8 on the -r line) and deepcopy sharing.
"""

import copy
import json
import os
import sys
import time
import types

import numpy as np

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import tensorflow as tf  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)
sys.path.insert(0, os.path.join(WREM, "rabbit"))
from scetlib_tf import ScetlibCachedXsecTF  # noqa: E402

from wremnants.postprocessing.scetlib_ad import lattice_cs_chi2 as OLD  # noqa: E402
from wremnants.postprocessing.scetlib_ad import lattice_cs_term as NEW  # noqa: E402
from wremnants.postprocessing.scetlib_ad import xsec_backend as xb  # noqa: E402

CACHE = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_bilincut_test/"
    "subset_y0y9_q0q1/cache.npz"
)
conf, sigma = xb.configure(CACHE.replace("cache.npz", "cache.conf"), threads=8)
sing, nons = sigma.sub_pieces()
sing.set_pdf_eig_params(29)
nons.set_pdf_eig_params(29)
fn = ScetlibCachedXsecTF.load(CACHE, sing, nons)
names = list(fn.param_names)
anchor = np.array(fn.anchor, float)

# ---- mock param model: rabbit names, REPARAM maps, held + S . phys(theta)
FIT = [
    ("alphaS", "alphas", (0.118, 0.002)),
    ("lambda2", "np_eff_lambda2", (anchor[names.index("np_eff_lambda2")], 0.5)),
    ("lambda2_nu", "np_gnu_lambda2", (0.15, 0.1)),
    ("lambda4_nu", "np_gnu_lambda4", (0.0, 0.5)),
    ("resumTNP_gamma_cusp", "tnp_gamma_cusp", (0.0, 1.0)),
    ("resumTNP_gamma_nu", "tnp_gamma_nu", (0.0, 1.0)),
]


class MockPM:
    def __init__(self):
        self.params = np.array([f[0].encode() for f in FIT])
        self.nparams = len(FIT)
        self.npoi = 1
        self.scetlib_names = names
        self.core = types.SimpleNamespace(tf_fn=fn)
        self._p_base_anchor = anchor.copy()
        self._idx = np.array([names.index(f[1]) for f in FIT])
        self._c0 = np.array([f[2][0] for f in FIT])
        self._c1 = np.array([f[2][1] for f in FIT])
        held = anchor.copy()
        held[self._idx] = 0.0
        self._held = held
        S = np.zeros((len(names), len(FIT)))
        S[self._idx, np.arange(len(FIT))] = 1.0
        self._S = S

    def scetlib_full_vector_tf(self, param):
        p = tf.constant(self._c0) + tf.constant(self._c1) * tf.cast(
            param[: self.nparams], tf.float64
        )
        return tf.constant(self._held) + tf.linalg.matvec(tf.constant(self._S), p)

    def full_np(self, theta):
        return self._held + self._S @ (self._c0 + self._c1 * np.asarray(theta))


pm = MockPM()
assert (
    abs(anchor[names.index("alphas")] - 0.118) < 1e-15
    and abs(anchor[names.index("np_gnu_lambda_inf")] - 2) < 1e-15
)
res, checks = {}, []


def check(name, val, tol):
    ok = bool(val <= tol)
    checks.append(dict(name=name, value=float(val), tol=tol, ok=ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {val:.3e} (tol {tol:g})", flush=True)


def make_term(**kw):
    Map = NEW.LatticeCSTermMapping
    m = Map.parse_args(
        types.SimpleNamespace(channel_info={}, procs=[]),
        *[f"{k}={v}" for k, v in kw.items()],
    )
    T = NEW.LatticeCSTerm(m, tf.float64)
    T.param_model_override = pm
    T.set_expectations(None, None, parms=pm.params)
    return T


t0 = time.time()
T = make_term(syst="Jnf+Jbt", tau=8.0)
res["build_seconds"] = time.time() - t0
S = T.core.summary()
res["summary_default"] = S
fnom = T.core.fit_nominal
check(
    "T1 stat-only lattice fit chi2 vs design 6.703 (3 digits)",
    abs(fnom["chi2"] - 6.703),
    6e-4,
)
check("T1 lambda2_nu vs design 0.1855", abs(fnom["lam"][0] - 0.1855), 6e-5)
check("T1 lambda4_nu vs design -0.00597", abs(fnom["lam"][1] + 0.00597), 6e-6)
check(
    "T1 J-mapped syst leave the minimum unchanged: |lam_final - lam_stat|",
    float(np.max(np.abs(T.core.fit_final["lam"] - fnom["lam"]))),
    1e-7,
)

# ---- T2: V4 against the old term's formula
Tn = make_term(syst="none", tau=8.0)
old = OLD.LatticeCSCore(syst="none")
check(
    "T2 same data / covariance as the old inputs file",
    float(max(np.max(np.abs(old.y - Tn.core.y)), np.max(np.abs(old.M - Tn.core.M)))),
    0.0,
)
POINTS = dict(
    NOMSTIFF=(0.0643, 0.0),
    LATCHI8=(0.0295, 0.0073),
    LATLIVE8Y=(0.0339, 0.0080),
    anchor=(0.15, 0.0),
    W=(-1e-6, 0.0444),
)
res["T2"] = {}
worst = 0.0
for nm, (l2, l4) in POINTS.items():
    for a in (0.116, 0.118, 0.120):
        for tc, tn in ((0.0, 0.0), (1.0, -1.0)):
            th = np.array(
                [(a - 0.118) / 0.002, 0.0, (l2 - 0.15) / 0.1, l4 / 0.5, tc, tn]
            )
            p = pm.full_np(th)
            new = float(Tn.chi2_tf(tf.constant(th)))
            z5 = Tn.core.zeta(p)
            pp = p.copy()
            pp[names.index("np_gnu_lambda_inf")] = 0.0
            pert = Tn.core.zeta(pp)
            r = pert + old.np_zeta(old.u, 2.0, l2, l4) - old.y
            ref = float(r @ old.M @ r)
            worst = max(worst, abs(new - ref) / max(1.0, abs(ref)))
            tabl = old.chi2(
                dict(lambda_inf_nu=2.0, lambda2_nu=l2, lambda4_nu=l4),
                a - 0.118,
                {"resumTNP_gamma_nu": tn, "resumTNP_gamma_cusp": tc},
                mode="live",
            )
            res["T2"][f"{nm}|as{a}|tnp{tc:+g}{tn:+g}"] = dict(
                new=new,
                old_formula_scetlib_pert=ref,
                old_table=tabl,
                new_minus_table=new - tabl,
                np_part_diff=float(
                    np.max(np.abs((z5 - pert) - old.np_zeta(old.u, 2.0, l2, l4)))
                ),
            )
check("T2 V4 new chi2 == old formula with SCETlib pert (rel, all points)", worst, 1e-10)
check(
    "T2 SCETlib NP part == the old plugin's tanh (max)",
    max(v["np_part_diff"] for v in res["T2"].values()),
    1e-12,
)
for nm in POINTS:
    v = res["T2"][f"{nm}|as0.118|tnp+0+0"]
    print(
        f"     {nm:10s} alpha_s 0.118: chi2 new {v['new']:.4f}  old(table) {v['old_table']:.4f}  "
        f"new-old {v['new_minus_table']:+.4f}"
    )

# ---- T3: derivatives through the TF path
th0 = np.array([0.6, 0.3, (0.0339 - 0.15) / 0.1, 0.0080 / 0.5, 0.7, -0.4])
x = tf.Variable(th0)


def pen():
    return T.compute_nll_penalty(x, None)


with tf.GradientTape() as t2:
    with tf.GradientTape() as t1:
        L = pen()
    g = t1.gradient(L, x)
Hrr = t2.jacobian(g, x).numpy()
g = g.numpy()
v = np.array([0.3, -1.0, 0.5, 0.2, -0.7, 1.1])
with tf.autodiff.ForwardAccumulator(x, tf.constant(v)) as acc:
    with tf.GradientTape() as t:
        L = pen()
    gg = t.gradient(L, x)
hv = acc.jvp(gg).numpy()


def fval(th):
    return float(T.compute_nll_penalty(tf.constant(th), None))


SC = np.exp(
    -16.0
)  # the penalty carries 1/2 exp(-2 tau); FD on chi2 itself avoids differencing ~1e-7 numbers
HS = np.array([1e-3, 1e-3, 1e-3, 2e-5, 1e-2, 1e-2])


def cval(th):
    return 0.5 * float(T.chi2_tf(tf.constant(th))) * SC


H_fd = np.zeros((6, 6))
g_fd = np.zeros(6)
for i in range(6):

    def d1(h):
        e = np.eye(6)[i] * h
        return (cval(th0 + e) - cval(th0 - e)) / (2 * h)

    g_fd[i] = (4 * d1(HS[i] / 2) - d1(HS[i])) / 3
    for j in range(6):

        def d2(a, b):
            ei, ej = np.eye(6)[i] * a, np.eye(6)[j] * b
            return (
                cval(th0 + ei + ej)
                - cval(th0 + ei - ej)
                - cval(th0 - ei + ej)
                + cval(th0 - ei - ej)
            ) / (4 * a * b)

        H_fd[i, j] = (4 * d2(HS[i] / 2, HS[j] / 2) - d2(HS[i], HS[j])) / 3
sg = np.max(np.abs(g_fd))
sH = np.max(np.abs(H_fd))
check(
    "T3 tape gradient vs Richardson FD (rel to max)",
    float(np.max(np.abs(g - g_fd)) / sg),
    1e-8,
)
check(
    "T3 nested-tape Hessian vs Richardson FD (rel to max)",
    float(np.max(np.abs(Hrr - H_fd)) / sH),
    1e-6,
)
check(
    "T3 forward-over-reverse hessp == nested-tape H v (rel)",
    float(np.max(np.abs(hv - Hrr @ v)) / np.max(np.abs(hv))),
    1e-12,
)
check(
    "T3 TMD lambda2 (no kernel dependence): gradient and Hessian row exactly 0",
    float(abs(g[1]) + np.max(np.abs(Hrr[1])) + np.max(np.abs(Hrr[:, 1]))),
    0.0,
)
res["T3"] = dict(
    grad=g.tolist(), grad_fd=g_fd.tolist(), hess=Hrr.tolist(), hess_fd=H_fd.tolist()
)

# ---- T4: tau and deepcopy
half = 0.5 * (float(T.chi2_tf(tf.constant(th0))) - T.offset)
check(
    "T4 penalty == 1/2 (chi2 - offset) exp(-16) (rel)",
    abs(fval(th0) - half * np.exp(-16.0)) / abs(half * np.exp(-16)),
    1e-14,
)
T2c = copy.deepcopy(T)
check(
    "T4 deepcopy shares the core and gives the same penalty",
    (
        0.0
        if (
            T2c.core is T.core
            and float(T2c.compute_nll_penalty(tf.constant(th0), None)) == fval(th0)
        )
        else 1.0
    ),
    0.0,
)

# timing of one value+gradient through TF
t = time.time()
for _ in range(10):
    with tf.GradientTape() as tt:
        L = pen()
    tt.gradient(L, x)
res["tf_value_grad_seconds"] = (time.time() - t) / 10
print(
    f"TF value+grad: {res['tf_value_grad_seconds'] * 1e3:.1f} ms; build {res['build_seconds']:.1f} s"
)

# other syst sets: load-time summary only (impact inputs)
res["summaries"] = {}
for syst in ("Jnf+Jbt", "Jnf", "Jbt", "none", "direct_nf+Jbt"):
    Tx = make_term(syst=syst, tau=8.0)
    res["summaries"][syst] = Tx.core.summary()
res["checks"] = checks
res["n_fail"] = sum(not c["ok"] for c in checks)
json.dump(res, open(os.path.join(TASK, "test_term.json"), "w"), indent=1, default=float)
print(f"\n{len(checks) - res['n_fail']}/{len(checks)} PASS")
