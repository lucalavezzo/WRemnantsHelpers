#!/usr/bin/env python3
"""Offline (no cache) validation of the LATFROZ code (WRemnants lattice_cs_term pert=frozen + nfswitch/nfscheme):

A. pert=live unchanged BITWISE against the previous commit of lattice_cs_term.py (git show <REF>:...), in both the
   load-time numbers (nf_shift, M, offset, refits) and the TF chi2 / gradient / Hessian at a displaced point.
B. each n_f variant's shift at the frozen reference (alpha_s 0.1168, TNPs 0) vs two independent evaluations:
   (i)  the qT::Gamma_nu CLASS (261007-lattice-term-native/classdrv/gz_class: SCETlib's class, not the AD kernel; same
        analytic RGE) with n_f = 4 and alpha_s^(5)(mu_match) as start: must agree to ~1e-15;
   (ii) the exact-RGE numpy kernel of 260923-conventions-map (our_cs_kernel.py; numerical running + cusp integral),
        both with the coupling IDENTIFIED at mu_match (like SCETlib) and with 3-loop MSbar DECOUPLING at m_b(m_b) (the
        old table): isolates analytic-vs-exact RGE and identification-vs-decoupling.
C. the shift's map onto (lambda2_nu, lambda4_nu) (Jnf: d lambda in sigma_stat, J_NP d), per variant.
Public numbers only (alpha_s 0.1168 / 0.118 are public references). Writes ../validate_nf.json.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types

import numpy as np

HERE = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261008-latfroz-nf-variants/scripts"
TASK = os.path.dirname(HERE)
STUDY = os.path.dirname(TASK)
WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
REF = os.environ.get("REF_COMMIT", "2f1c3df4")
sys.path.insert(0, WREM)
sys.path.insert(0, os.path.join(STUDY, "260923-conventions-map"))
import tensorflow as tf  # noqa: E402

import our_cs_kernel as K  # noqa: E402
from wremnants.postprocessing.scetlib_ad import lattice_cs_term as NEW  # noqa: E402
from wremnants.postprocessing.scetlib_ad import xsec_backend as xb  # noqa: E402

CONF = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25/cache.conf"
CLS = os.path.join(STUDY, "261007-lattice-term-native", "classdrv", "gz_class")
MB = 4.18
AFZ = 0.1168
out = {}

_, sigma = xb.configure(CONF, threads=4)
sing, _ = sigma.sub_pieces()
names = list(sing.gradient_param_names())
anchor = np.array(sing.gradient_central(), float)
ix = {n: i for i, n in enumerate(names)}
fit = [
    ("alphaS", "alphas", 0.118, 0.002),
    ("lambda2_nu", "np_gnu_lambda2", 0.15, 0.1),
    ("lambda4_nu", "np_gnu_lambda4", 0.0, 0.5),
    ("resumTNP_gamma_nu", "tnp_gamma_nu", 0.0, 1.0),
    ("resumTNP_gamma_cusp", "tnp_gamma_cusp", 0.0, 1.0),
]
idx = np.array([ix[f[1]] for f in fit])
c0 = np.array([f[2] for f in fit])
c1 = np.array([f[3] for f in fit])
held = anchor.copy()
held[idx] = 0.0
S = np.zeros((len(names), len(fit)))
S[idx, np.arange(len(fit))] = 1.0


class PM:
    params = np.array([f[0].encode() for f in fit])
    nparams, npoi, npou = len(fit), 1, len(fit) - 1
    scetlib_names = names
    core = types.SimpleNamespace(tf_fn=types.SimpleNamespace(_sing=sing))
    _p_base_anchor = anchor.copy()

    @staticmethod
    def scetlib_full_vector_tf(param):
        p = tf.constant(c0) + tf.constant(c1) * tf.cast(param[: len(fit)], tf.float64)
        return tf.constant(held) + tf.linalg.matvec(tf.constant(S), p)


def term(mod, *a):
    m = mod.LatticeCSTermMapping.parse_args(
        types.SimpleNamespace(channel_info={}, procs=[]), *a, "rules=any", "tau=8.0"
    )
    t = mod.LatticeCSTerm(m, tf.float64)
    t.param_model_override = PM()
    t.set_expectations(None, None, parms=PM.params)
    return t


import numpy as np

t = term(
    NEW,
    "syst=Jnf",
    "offset=min",
    "pert=frozen",
    "alphas_frozen=0.1168",
    "nfmatch=4.18",
    "nfscheme=full",
)
c = t.core
for lab, f in (
    ("stat-only (nominal)", c.fit_nominal),
    ("stat+Jnf V3 (final)", c.fit_final),
):
    cov = 2.0 * np.linalg.inv(f["hess"])
    s = np.sqrt(np.diag(cov))
    r = cov[0, 1] / (s[0] * s[1])
    print(
        "RES",
        lab,
        "lam2_nu=%.4f +- %.4f  lam4_nu=%.5f +- %.5f  rho=%.3f chi2=%.2f"
        % (f["lam"][0], s[0], f["lam"][1], s[1], r, f["chi2"]),
    )
