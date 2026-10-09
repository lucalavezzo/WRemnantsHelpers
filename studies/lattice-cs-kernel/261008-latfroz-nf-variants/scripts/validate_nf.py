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

HERE = os.path.dirname(os.path.abspath(__file__))
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

src = subprocess.run(
    [
        "git",
        "-C",
        WREM,
        "show",
        f"{REF}:wremnants/postprocessing/scetlib_ad/lattice_cs_term.py",
    ],
    capture_output=True,
    text=True,
    check=True,
).stdout
tmp = tempfile.NamedTemporaryFile("w", suffix="_lattice_cs_term_ref.py", delete=False)
tmp.write(
    src.replace(
        "_HERE = os.path.dirname(os.path.abspath(__file__))",
        f"_HERE = {os.path.dirname(NEW.__file__)!r}",
    )
)
tmp.close()
spec = importlib.util.spec_from_file_location("lct_ref", tmp.name)
OLD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(OLD)

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


def ghess(t, th):
    x = tf.Variable(th)
    with tf.GradientTape() as t2:
        with tf.GradientTape() as t1:
            v = t.compute_nll_penalty(x, None)
        g = t1.gradient(v, x)
    return float(v), g.numpy(), t2.jacobian(g, x).numpy()


# ---- A. live bitwise vs REF
th = np.array([0.7, -0.6, 0.011, 0.4, -0.3])
A = {}
for lab, args in (
    ("default Jnf+Jbt", ()),
    ("Jnf", ("syst=Jnf",)),
    ("direct_nf+Jbt nfmatch=2", ("syst=direct_nf+Jbt", "nfmatch=2.0")),
):
    to, tn = term(OLD, *args), term(NEW, *args)
    vo, go, ho = ghess(to, th)
    vn, gn, hn = ghess(tn, th)
    ok = (
        vo == vn
        and np.array_equal(go, gn)
        and np.array_equal(ho, hn)
        and to.offset == tn.offset
        and np.array_equal(to.core.M, tn.core.M)
        and np.array_equal(to.core.nf_shift, tn.core.nf_shift)
        and to.core.summary()
        == {
            k: v
            for k, v in tn.core.summary().items()
            if k not in ("nf_switch", "nf_scheme")
        }
    )
    A[lab] = bool(ok)
    print(
        f"[A] live vs {REF} ({lab}): value/grad/Hessian/offset/M/nf_shift/summary bitwise equal: {ok}",
        flush=True,
    )
out["A_live_bitwise_vs_ref"] = A
out["ref_commit"] = REF

# ---- B. variants at the frozen reference
pfz = NEW.frozen_reference(names, anchor, AFZ)
VAR = {
    "V1": dict(
        args=("nfmatch=1.0",),
        cls=[(1.0, None, +1), (2.0, 1.0, +1), (1.0, 1.0, -1)],
        switch=1.0,
        match=1.0,
        full=False,
        desc="n_f=5 kernel at 1 GeV, n_f=4 evolution 1->2 GeV, coupling identified at 1 GeV",
    ),
    "V2": dict(
        args=("nfmatch=4.18", "nfswitch=1.0"),
        cls=[(1.0, None, +1), (2.0, MB, +1), (1.0, MB, -1)],
        switch=1.0,
        match=MB,
        full=False,
        desc="n_f=5 kernel at 1 GeV, n_f=4 evolution 1->2 GeV, alpha_s^(4) identified at m_b(m_b)",
    ),
    "V3": dict(
        args=("nfmatch=4.18", "nfscheme=full"),
        cls=[(2.0, MB, +1)],
        switch=None,
        match=MB,
        full=True,
        desc="whole kernel (boundary at mu0 + evolution) n_f=4, coupling identified at m_b(m_b)",
    ),
    "V3lit": dict(
        args=("nfmatch=4.18",),
        cls=[(MB, None, +1), (2.0, MB, +1), (MB, MB, -1)],
        switch=MB,
        match=MB,
        full=False,
        desc="literal nfmatch=4.18: n_f=5 kernel up to m_b, n_f=4 evolution m_b->2 GeV",
    ),
}
b_fm = None


def cls(alphas, mu, mm):
    env = dict(os.environ)
    if mm is not None:
        env.update(GZ_NF="4", GZ_ASMATCH=repr(mm))
    a = [repr(alphas), "0.0", "0.0", "0.0", "0.15", "0.0", "0", repr(mu)]
    r = subprocess.run(
        [CLS, *a, *[repr(float(b)) for b in b_fm]],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return np.array(
        [float(ln.split()[2]) for ln in r.stdout.splitlines() if ln.strip()]
    )


class IdCoupling:
    """n_f = 4 coupling identified with the exact-RGE alpha_s^(5) at mu_match (numpy reference)."""

    def __init__(self, alphas_mz, mm, nloop=4):
        self.nf = 4
        self.a_ref, self.mu_ref, self.nloop = (
            K.run_alphas(alphas_mz, K.MZ, mm, 5, nloop),
            mm,
            nloop,
        )

    def __call__(self, mu):
        return K.run_alphas(self.a_ref, self.mu_ref, mu, 4, self.nloop)


def np_shift(v, alphas, decouple):
    lam0 = {"lambda_inf_nu": 0.0}
    c5 = K.Coupling(alphas, "fit")
    c4 = (
        K.Coupling(alphas, "lattice")
        if (decouple and v["match"] == MB)
        else IdCoupling(alphas, v["match"])
    )
    z5 = lambda mu: K.our_cs_kernel(
        b_fm, lam0, alphas_mz=alphas, mu=mu, coupling=c5
    )  # noqa: E731
    z4 = lambda mu: K.our_cs_kernel(
        b_fm, lam0, alphas_mz=alphas, mu=mu, coupling=c4
    )  # noqa: E731
    if v["full"]:
        return z4(2.0) - z5(2.0)
    s = v["switch"]
    return z5(s) + z4(2.0) - z4(s) - z5(2.0)


out["B"] = {}
for k, v in VAR.items():
    t = term(NEW, "syst=Jnf", "pert=frozen", f"alphas_frozen={AFZ}", *v["args"])
    core = t.core
    b_fm = core.b_fm
    assert np.array_equal(core.p_ref, pfz)
    sh = core.nf_shift
    ref_cls = sum(sgn * cls(AFZ, mu, mm) for mu, mm, sgn in v["cls"]) - cls(
        AFZ, 2.0, None
    )
    rows = dict(
        desc=v["desc"],
        args=list(v["args"]),
        shift=sh.tolist(),
        shift_min=float(sh.min()),
        shift_max=float(sh.max()),
        flat_spread=float(np.ptp(sh)),
        max_abs_vs_class=float(np.max(np.abs(sh - ref_cls))),
    )
    for dec in (False, True):
        if dec and v["match"] != MB:
            continue
        r = np_shift(v, AFZ, dec)
        rows[f"numpy_exactRGE_{'decoupled' if dec else 'identified'}"] = dict(
            min=float(r.min()),
            max=float(r.max()),
            max_rel_scetlib_minus_numpy=float(
                np.max(np.abs(sh - r)) / np.max(np.abs(r))
            ),
        )
    info = core.syst_info["Jnf"]
    fs = core.fit_nominal
    cov_stat = np.linalg.inv(0.5 * fs["hess"])
    sstat = np.sqrt(np.diag(cov_stat))
    dl = np.array(info["dlam"])
    rows.update(
        dlam=dl.tolist(),
        dlam_over_sigma_stat=(dl / sstat).tolist(),
        Jnp_dlam=(core.J_np @ dl).tolist(),
        Jnp_dlam_range=[float((core.J_np @ dl).min()), float((core.J_np @ dl).max())],
        Jnp_dlam_over_sig_lat_max=float(
            np.max(np.abs(core.J_np @ dl) / np.sqrt(np.diag(core.cov_stat)))
        ),
        shift_over_sig_lat_max=float(
            np.max(np.abs(sh) / np.sqrt(np.diag(core.cov_stat)))
        ),
        lattice_only_stat=dict(
            lam=fs["lam"].tolist(), chi2=fs["chi2"], sigma=sstat.tolist()
        ),
        lattice_only_final=core.summary()["final_fit"],
        chi2_min=core.chi2_min,
    )
    out["B"][k] = rows
    print(
        f"[B] {k:5s} {v['desc']}\n     shift {sh.min():+.5f}..{sh.max():+.5f} (spread {np.ptp(sh):.1e}); "
        f"|SCETlib - class| {rows['max_abs_vs_class']:.1e}; "
        + "; ".join(
            f"{kk}: {vv['min']:+.5f}..{vv['max']:+.5f} (rel {vv['max_rel_scetlib_minus_numpy']:.3f})"
            for kk, vv in rows.items()
            if kk.startswith("numpy")
        )
        + f"\n     dlam = ({dl[0]:+.5f}, {dl[1]:+.6f}) = ({dl[0] / sstat[0]:+.2f}, {dl[1] / sstat[1]:+.2f}) sigma_stat; "
        f"J_NP dlam {rows['Jnp_dlam_range'][0]:+.5f}..{rows['Jnp_dlam_range'][1]:+.5f}; final lattice-only "
        f"lam {np.round(rows['lattice_only_final']['lam'], 6).tolist()} sigma "
        f"{np.round(rows['lattice_only_final']['sigma'], 5).tolist()}, chi2_min {core.chi2_min:.4f}",
        flush=True,
    )

# alpha_s^(4)(1 GeV) in the two conventions (public reference values)
cpl = {}
for a in (0.118, AFZ):
    cpl[str(a)] = dict(
        a5_1GeV=float(K.Coupling(a, "fit")(1.0)),
        a4_1GeV_decoupled_mb=float(K.Coupling(a, "lattice")(1.0)),
        a4_1GeV_identified_mb=float(IdCoupling(a, MB)(1.0)),
        a4_2GeV_decoupled_mb=float(K.Coupling(a, "lattice")(2.0)),
        a5_2GeV=float(K.Coupling(a, "fit")(2.0)),
    )
out["couplings_exactRGE_4loop"] = cpl
print("[B] couplings (exact 4-loop running):", json.dumps(cpl), flush=True)
json.dump(out, open(os.path.join(TASK, "validate_nf.json"), "w"), indent=1)
print("A all bitwise:", all(A.values()))
