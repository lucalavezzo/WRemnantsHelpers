"""Exact ASWZ lattice CS-kernel chi2 as a rabbit ``Regularizer`` (prototype, task 261006-lattice-chi2-in-fit).

Adds 1/2 * (chi2_lat - offset) to the NLL, where

    chi2_lat(lambda) = min_k1  r^T C^-1 r ,
    r_i = pert_i + 1/2 gamma_nu^NP(b_i; lambda_inf_nu, lambda2_nu, lambda4_nu[, lambda6_nu]) + k1 a_i/b_i - y_i

over the 21 ASWZ per-ensemble points (arXiv:2402.06725), i.e. a SIMULTANEOUS fit of the lattice data with the Z data,
in exactly the conventions of lattice-cs-kernel/260923-scetlib-kernel-fit (kernel_fit.py):
  * pert_i: our SCETlib perturbative kernel (n_f = 5, mu = 2 GeV, N3LL, alpha_s(mZ) = 0.118), a frozen 21-point table
    (scripts/build_inputs.py). The lattice gamma_q == SCETlib gamma_zeta == gamma_nu / 2 (260923-conventions-map).
  * gamma_nu^NP = -linf tanh(P(u)/linf), P(u) = l2 u + l4 u^2 (+ l6 u^3 for tanh_6), u = b_T^2 at the BARE b_T.
  * k1 (lattice-spacing artefact) is PROFILED ANALYTICALLY. The term is quadratic in k1, so
        chi2_lat = r0^T M r0 ,  M = W - (W v)(W v)^T / (v^T W v) ,  W = C^-1 , v = a/b , r0 = r(k1 = 0) ,
        k1_hat = -(v^T W r0) / (v^T W v).
    This is EXACTLY equivalent to a free k1 parameter: same minimum, and the Hessian of the profiled term in the other
    parameters is the Schur complement, i.e. the k1-marginal curvature. (A rabbit regularizer cannot own fit parameters.)
  * C = the block-diagonal lattice covariance + an additive systematic covariance on the points (``syst=``):
        J          (default) the 2D card term's three systematic groups (n_f scheme, k-form, b_T window), each chosen
                   parameter shift d_g mapped onto the points as J_NP d_g at the lattice best fit. By Woodbury the
                   profiled (l2, l4) covariance is then the card term's stat+syst covariance, and the minimum and
                   chi2_min are unchanged (linear limit).
        direct_nf  as J, but the n_f group as the direct point shift pert(n_f=5 matched at mu=1) - pert(n_f=5).
        none       stat only.
  * alpha_s: the pert table is frozen at alpha_s(mZ) = 0.118 (``alphas=frozen``, default, like-for-like with the
    Gaussian card terms, which have no alpha_s dependence either). ``alphas=live`` adds the LINEAR response
    (alpha_s - 0.118) * d pert / d alpha_s(mZ) per point, reading the POI from rabbit's ``get_x()`` -- which is the
    PHYSICAL (offset-applied) value the model itself is evaluated at, so the term is blinding-consistent; it is never
    printed. Linear is exact to 2.2e-3 sigma_lat (per point) over +-0.002 (test_lattice_cs_chi2.py).
  * offset: by default the lattice-only chi2_min at lambda_inf_nu = 2 (l2, l4, k1 free, same covariance), so the term is
    1/2 Delta chi2_lat -- zero at the lattice best fit, like the Gaussian card terms it replaces.

THE exp(2 tau) COMPENSATION. rabbit multiplies EVERY regularizer penalty by exp(2 tau) (one common ``fitter.tau`` =
``--regularizationStrength``, meant for the NPDampingWall). A likelihood term must not be scaled, so this term divides
it back out with the LIVE ``fitter.tau`` variable, found at ``set_expectations`` time (rabbit calls it from
``Fitter.arm_regularizers``). If no fitter is on the call stack (offline harness), ``tau=<float>`` on the -r line is
used, else exp(0) = 1. If both are present they must agree, or construction fails.

theta -> physical: the SAME map as NPDampingWall (np_damping_wall.resolve_wall_inputs: params.REPARAM width + the
correction runcard's anchor), lambdas resolved BY NAME, held lambdas (lambda_inf_nu, frozen) at the anchor.
The term reads only the CS lambdas (POUs, never blinded); it never reads the POI.

Invoke (composes with the wall; both on their own -r):

    rabbit_fit.py ... --regularizationStrength 8 \\
      -r wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall \\
         wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping margin=0 \\
      -r lattice_cs_chi2.LatticeCSChi2 lattice_cs_chi2.LatticeCSMapping [syst=J|direct_nf|none] [offset=min|0]
         [inputs=<npz>] [tau=<float>] [alphas=frozen|live]
"""

import inspect
import os

import numpy as np

DEFAULT_INPUTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "lattice_aswz_inputs.npz",
)
CS_NAMES = ("lambda_inf_nu", "lambda2_nu", "lambda4_nu", "lambda6_nu")
SYST_MODES = ("J", "direct_nf", "none")
ALPHAS_TABLE = (
    0.118  # alpha_s(mZ) of the frozen pert table (= the AD cache's alphas_mu0)
)
LINF_REF = 2.0  # lambda_inf_nu of the reference lattice-only minimum used as the offset


class LatticeCSCore:
    """Backend-agnostic exact lattice chi2 (numpy here; the TF path uses the same constants)."""

    def __init__(self, inputs=DEFAULT_INPUTS, syst="J"):
        if syst not in SYST_MODES:
            raise ValueError(f"syst={syst!r}; choose one of {SYST_MODES}")
        d = np.load(inputs)
        self.inputs, self.syst = inputs, syst
        self.b_fm, self.a_fm, self.y = d["b_fm"], d["a_fm"], d["y"]
        self.u = (self.b_fm * float(d["fm_to_gevinv"])) ** 2  # GeV^-2
        self.v = self.a_fm / self.b_fm
        self.pert = d["pert"]
        self.dpert_dalphas = d["dpert_dalphas"]
        cov = np.array(d["cov_stat"], float)
        if syst == "J":
            S = d["syst_J"]
        elif syst == "direct_nf":
            S = d["syst_direct_nf"]
        else:
            S = np.zeros((0, len(self.y)))
        self.csyst = sum((np.outer(s, s) for s in S), np.zeros_like(cov))
        self.cov = cov + self.csyst
        W = np.linalg.inv(self.cov)
        W = 0.5 * (W + W.T)
        self.W = W
        self.Wv = W @ self.v
        self.vWv = float(self.v @ self.Wv)
        M = W - np.outer(self.Wv, self.Wv) / self.vWv
        self.M = 0.5 * (M + M.T)
        self.c = self.pert - self.y  # r0 = c + npz(lambda)

    @staticmethod
    def np_zeta(u, linf, l2, l4, l6=0.0, tanh=np.tanh):
        return -0.5 * linf * tanh((l2 * u + l4 * u * u + l6 * u * u * u) / linf)

    def r0(self, lam, dalphas=0.0):
        g = self.np_zeta(
            self.u,
            lam["lambda_inf_nu"],
            lam["lambda2_nu"],
            lam.get("lambda4_nu", 0.0),
            lam.get("lambda6_nu", 0.0),
        )
        return self.c + dalphas * self.dpert_dalphas + g

    def chi2(self, lam, dalphas=0.0):
        r = self.r0(lam, dalphas)
        return float(r @ self.M @ r)

    def k1hat(self, lam, dalphas=0.0):
        return float(-(self.Wv @ self.r0(lam, dalphas)) / self.vWv)

    def fit(self, free=("lambda2_nu", "lambda4_nu"), fixed=None, x0=None):
        """Lattice-only minimum (scipy), for the offset and the closure."""
        from scipy.optimize import minimize

        fixed = dict(
            dict(lambda_inf_nu=LINF_REF, lambda4_nu=0.0, lambda6_nu=0.0),
            **(fixed or {}),
        )
        x0 = np.array(x0 if x0 is not None else [0.15, 0.0][: len(free)], float)

        def f(x):
            return self.chi2(dict(fixed, **dict(zip(free, x))))

        best = None
        for s in [x0, x0 * 0.5 + 0.05, x0 + 0.01]:
            r = minimize(
                f,
                s,
                method="Nelder-Mead",
                options=dict(xatol=1e-12, fatol=1e-13, maxiter=40000, maxfev=80000),
            )
            r = minimize(f, r.x, method="BFGS", options=dict(gtol=1e-11))
            if best is None or r.fun < best.fun:
                best = r
        return best, dict(fixed, **dict(zip(free, best.x)))


def _make_mapping_class():
    from rabbit.mappings.mapping import BaseMapping

    class LatticeCSMapping(BaseMapping):
        """Carries the -r options to LatticeCSChi2: inputs=<npz>, syst=<J|direct_nf|none>, offset=<min|0|float>,
        tau=<float> (only used, and cross-checked, when no fitter is found on the call stack), alphas=<frozen|live>.
        """

        def __init__(
            self,
            indata,
            key,
            inputs=DEFAULT_INPUTS,
            syst="J",
            offset="min",
            tau=None,
            alphas="frozen",
        ):
            super().__init__(indata, key)
            self.indata = indata
            self.inputs, self.syst, self.offset, self.tau, self.alphas = (
                inputs,
                syst,
                offset,
                tau,
                alphas,
            )

        @classmethod
        def parse_args(cls, indata, *args):
            kw = {}
            for a in args:
                if "=" not in a:
                    raise ValueError(f"LatticeCSMapping: args are key=value, got {a!r}")
                k, v = a.split("=", 1)
                if k not in ("inputs", "syst", "offset", "tau", "alphas"):
                    raise ValueError(f"LatticeCSMapping: unknown key {k!r}")
                kw[k] = float(v) if k == "tau" else v
            key = " ".join([cls.__name__, *args])
            return cls(indata, key, **kw)

    return LatticeCSMapping


def _find_fitter_tau():
    """The live fitter.tau tf.Variable, if set_expectations is being called from Fitter.arm_regularizers."""
    fr = inspect.currentframe()
    try:
        f = fr.f_back
        for _ in range(6):
            if f is None:
                return None
            obj = f.f_locals.get("self")
            if obj is not None and hasattr(obj, "tau") and hasattr(obj, "regularizers"):
                return obj.tau
            f = f.f_back
    finally:
        del fr
    return None


def _make_regularizer_class():
    import tensorflow as tf
    from rabbit.regularization.regularizer import Regularizer
    from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall

    class LatticeCSChi2(Regularizer):
        """1/2 (chi2_lat - offset) / exp(2 tau): exact ASWZ lattice chi2, k1 profiled; see the module docstring."""

        needs_observables = False

        def __init__(self, mapping, dtype):
            super().__init__(mapping, dtype)
            self.dtype = dtype
            self.mapping = mapping
            self.core = LatticeCSCore(
                getattr(mapping, "inputs", DEFAULT_INPUTS),
                getattr(mapping, "syst", "J"),
            )
            inp = wall.resolve_wall_inputs(mapping.indata)
            if inp["np_model_nu"] not in ("tanh_2", "tanh_6"):
                raise ValueError(
                    f"LatticeCSChi2: np_model_nu={inp['np_model_nu']!r} (need tanh_2 / tanh_6)"
                )
            self.form = inp["np_model_nu"]
            self.specs = {n: inp["specs"][n] for n in CS_NAMES if n in inp["specs"]}
            self.anchors = {
                n: inp["anchors"][n] for n in CS_NAMES if n in inp["anchors"]
            }
            off = getattr(mapping, "offset", "min")
            if off == "min":
                res, lam = self.core.fit()
                self.offset = float(res.fun)
                self.offset_point = lam
            else:
                self.offset, self.offset_point = float(off), None
            self.tau_arg = getattr(mapping, "tau", None)
            self.alphas_mode = getattr(mapping, "alphas", "frozen")
            if self.alphas_mode not in ("frozen", "live"):
                raise ValueError(
                    f"LatticeCSChi2: alphas={self.alphas_mode!r} (frozen|live)"
                )
            self.as_spec = None
            if self.alphas_mode == "live":
                from wremnants.postprocessing.scetlib_ad.response import (
                    corr_config_from_meta,
                )

                cfg = corr_config_from_meta(mapping.indata.metadata)["config"]
                self.as_spec = wall.physical_spec(cfg, "alphaS")
                anchor = self.as_spec[1][0] if self.as_spec[0] == "quad" else None
                if anchor is None or abs(anchor - ALPHAS_TABLE) > 1e-12:
                    raise ValueError(
                        f"LatticeCSChi2: alphaS map {self.as_spec} is not anchored at the table's {ALPHAS_TABLE}"
                    )
            self._ias = None
            self._tau = None
            self._idx, self._held = {}, {}
            c = lambda a: tf.constant(np.asarray(a, float), dtype=dtype)  # noqa: E731
            self.tf_u, self.tf_c, self.tf_M = (
                c(self.core.u),
                c(self.core.c),
                c(self.core.M),
            )
            self.tf_das = c(self.core.dpert_dalphas)
            print(
                f"[LatticeCSChi2] {len(self.core.y)} ASWZ points, inputs {self.core.inputs}, syst={self.core.syst}, "
                f"form {self.form}, k1 profiled analytically, alpha_s {self.alphas_mode} (table at {ALPHAS_TABLE}"
                + (f", map {self.as_spec}" if self.as_spec else "")
                + f"). offset (chi2_min at lambda_inf_nu={LINF_REF}) = "
                f"{self.offset:.6f} at {self.offset_point}. theta->physical: "
                + ", ".join(f"{n}: {self.specs[n]}" for n in self.specs),
                flush=True,
            )

        def set_expectations(self, initial_params, initial_observables, parms=None):
            if parms is None:
                raise ValueError(
                    "LatticeCSChi2 needs parms= (names) to resolve the CS lambdas"
                )
            names = list(np.asarray(parms).astype(str))
            self._idx, self._held = {}, {}
            for n in CS_NAMES:
                if n == "lambda6_nu" and self.form != "tanh_6":
                    continue
                if n in names:
                    self._idx[n] = names.index(n)
                else:
                    a = self.anchors.get(n)
                    if a is None:
                        raise ValueError(
                            f"LatticeCSChi2: {n} neither fitted nor carried by the correction runcard"
                        )
                    self._held[n] = float(a)
            self._ias = None
            if self.alphas_mode == "live":
                if "alphaS" not in names:
                    raise ValueError(
                        "LatticeCSChi2: alphas=live but alphaS is not a fit parameter"
                    )
                self._ias = names.index("alphaS")
            if "lambda2_nu" not in self._idx:
                raise ValueError(
                    "LatticeCSChi2: lambda2_nu is not a fit parameter -- the term would be a constant"
                )
            tau = _find_fitter_tau()
            if tau is not None:
                if (
                    self.tau_arg is not None
                    and abs(float(tau.numpy()) - self.tau_arg) > 1e-12
                ):
                    raise ValueError(
                        f"LatticeCSChi2: tau={self.tau_arg} on the -r line but fitter.tau = {float(tau.numpy())}"
                    )
                self._tau = tau
                src = f"fitter.tau (live variable, now {float(tau.numpy()):g})"
            else:
                self._tau = None
                src = (
                    f"tau={self.tau_arg} from the -r line"
                    if self.tau_arg is not None
                    else "NONE (scale 1)"
                )
            print(
                f"[LatticeCSChi2] armed: fitted {sorted(self._idx)}, held {self._held}; exp(2 tau) compensation from {src}",
                flush=True,
            )

        def physical(self, params):
            vals = {n: tf.constant(v, dtype=self.dtype) for n, v in self._held.items()}
            for n, i in self._idx.items():
                vals[n] = wall.physical_from_theta(self.specs[n], params[i], exp=tf.exp)
            return vals

        def chi2_tf(self, params):
            lam = self.physical(params)
            z = tf.constant(0.0, dtype=self.dtype)
            g = LatticeCSCore.np_zeta(
                self.tf_u,
                lam["lambda_inf_nu"],
                lam["lambda2_nu"],
                lam.get("lambda4_nu", z),
                lam.get("lambda6_nu", z),
                tanh=tf.tanh,
            )
            r = self.tf_c + g
            if (
                self._ias is not None
            ):  # physical alpha_s (offset-applied get_x value); never printed
                das = wall.physical_from_theta(
                    self.as_spec, params[self._ias]
                ) - tf.constant(ALPHAS_TABLE, dtype=self.dtype)
                r = r + das * self.tf_das
            return tf.tensordot(r, tf.linalg.matvec(self.tf_M, r), 1)

        def compute_nll_penalty(self, params, observables):
            half = 0.5 * (
                self.chi2_tf(params) - tf.constant(self.offset, dtype=self.dtype)
            )
            if self._tau is not None:
                return half * tf.exp(-2.0 * tf.cast(self._tau, self.dtype))
            if self.tau_arg is not None:
                return half * tf.constant(np.exp(-2.0 * self.tau_arg), dtype=self.dtype)
            return half

    return LatticeCSChi2


def __getattr__(name):
    if name == "LatticeCSMapping":
        cls = _make_mapping_class()
        globals()[name] = cls
        return cls
    if name == "LatticeCSChi2":
        cls = _make_regularizer_class()
        globals()[name] = cls
        return cls
    raise AttributeError(name)
