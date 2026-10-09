"""Check: CS-kernel toy band (as np_function_plots draws it) vs exact curves at lambda2_nu +- sigma."""

import json
import numpy as np
from wremnants.postprocessing.scetlib_np import np_function_plots as NPF
from wremnants.postprocessing.scetlib_np.np_function_plots import (
    _raw_toys,
    _DEFAULT_LAMBDAS,
    NPLambdas,
)

T = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261005-np-forms-lattice"
cases = {
    "prefit": (
        "lambda2=0.4,lambda4=0.4,delta_lambda2=0,lambda_inf=1,lambda2_nu=0.134549,lambda4_nu=0,lambda_inf_nu=2",
        f"{T}/cov_prefit_lattice.json",
    ),
    "NOMSTIFF": (
        "lambda2=0.025581,lambda4=0.087583,delta_lambda2=-0.004093,lambda_inf=1,lambda2_nu=0.06427,lambda4_nu=0,lambda_inf_nu=2",
        f"{T}/cov_NOMSTIFF.json",
    ),
}
bT = np.array([0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4.0])
for name, (lstr, covp) in cases.items():
    base = {
        **_DEFAULT_LAMBDAS,
        **{k: float(v) for k, v in (kv.split("=") for kv in lstr.split(","))},
    }
    spec = json.load(open(covp))
    sig = (
        spec["sigma"]["lambda2_nu"]
        if "sigma" in spec
        else np.sqrt(
            np.array(spec["cov"])[spec["names"].index("lambda2_nu")][
                spec["names"].index("lambda2_nu")
            ]
        )
    )
    for n_toys in (1000, 100000):
        toys = _raw_toys(covp, base, "tanh_2", "tanh_2", n_toys, 0)
        G = np.array([NPF.gamma_nu_curve(bT, t.gnu) for t in toys])
        lo, hi = np.percentile(G, [16, 84], axis=0)

        def g(l2nu):
            return NPF.gamma_nu_curve(
                bT,
                NPLambdas.from_flat(
                    {**base, "lambda2_nu": l2nu}, "tanh_2", "tanh_2"
                ).gnu,
            )

        up, dn = g(base["lambda2_nu"] - sig), g(
            base["lambda2_nu"] + sig
        )  # gamma decreasing in l2nu
        c = g(base["lambda2_nu"])
        print(f"{name} sigma(l2nu)={sig:.5f} n_toys={n_toys}")
        for i, b in enumerate(bT):
            print(
                f"  b={b:3.1f} central={c[i]:+.4f}  exact[+1s,-1s]=[{dn[i]:+.4f},{up[i]:+.4f}]  toys[16,84]=[{lo[i]:+.4f},{hi[i]:+.4f}]  "
                f"rel diff lo={(lo[i]-dn[i])/(c[i]-dn[i]):+.3f} hi={(hi[i]-up[i])/(up[i]-c[i]):+.3f}"
            )
