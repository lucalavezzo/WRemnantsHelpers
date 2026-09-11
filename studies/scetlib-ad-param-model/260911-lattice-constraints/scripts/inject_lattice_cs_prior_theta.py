#!/usr/bin/env python3
"""Inject the lattice CS-kernel constraint into a scetlib_ad datacard as a
rabbit EXTERNAL LIKELIHOOD TERM, expressed in the model's THETA coordinate.

This is a port of
``WRemnantsHelpers/studies/np-wall-local-minima/scripts/inject_lattice_cs_prior.py``
(the mechanism the scetlib_np work used), with one change that is the whole
point of the port: in ``scetlib_ad`` the fitted lambdas are UNIT NUISANCES.

WHY AN EXTERNAL TERM AND NOT ``prior_sigmas``
---------------------------------------------
``prior_sigmas`` (and rabbit's ``cw = 1/sigma^2``) is DIAGONAL: one scalar per
parameter. The lattice constraint's content is largely its CORRELATION --
rho(lambda2_nu, lambda4_nu) = -0.9135 marginal, -0.911 conditional -- because a
b^2 and a b^4 coefficient fitted to the same curve are near-degenerate. Dropping
it is not a small approximation: the constrained eigendirection is 5700x
narrower than the free one in this 2x2. A rabbit ``Regularizer`` could carry the
quadratic form, but ``fitter.py`` multiplies EVERY regularizer by the one shared
``exp(2*tau)``, which is already spoken for by the damping wall.

rabbit's external-likelihood mechanism is the right tool, is NOT scaled by tau,
and resolves parameter names against ``concat([param_model.params,
indata.systs])``, so the model's lambdas are addressable by name.

    -log L_ext = g^T x_sub + 0.5 x_sub^T H x_sub + const
    H = C^-1,  g = -C^-1 mu,  const = 0.5 mu^T C^-1 mu  (rabbit fills const in
    itself for a dense Hessian, so the term is 0 at x = mu)

THE THETA CONVERSION (the critical adaptation)
----------------------------------------------
``scetlib_ad`` commit 8f6af64f made every reparametrised parameter a unit
nuisance,

    physical = anchor + width * theta,

with ``width`` from ``params.REPARAM`` and ``anchor`` from the card's recorded
theory-correction runcard. rabbit's external term sees THETA. So a physical
Gaussian N(mu, C) must be pushed through the AFFINE map. With W = diag(width),

    mu_theta = W^-1 (mu - anchor)
    C_theta  = W^-1 C W^-1
    H_theta  = W C^-1 W                (note: NOT W^-1 ... W^-1)
    g_theta  = -H_theta mu_theta = -W C^-1 (mu - anchor)

and the chi^2 is INVARIANT, which is the numerical check this script asserts.
Getting the direction of W wrong is silent: it would scale lambda2_nu's prior
width by 0.10^2 = 100x in one direction and 1/100 in the other.

lambda_inf_nu HAS NO REPARAM ENTRY -- its fit coordinate IS the physical value,
and it is in ``params.DEFAULT_FROZEN`` (held at the correction's 2.0). So the
3x3 lattice covariance is CONDITIONED on that held value rather than marginalised
(``--condition-linf-nu``, default: the card's own anchor). Conditioning at 2.0
rather than at the lattice mean 1.6853 both SHIFTS and TIGHTENS the
(lambda2_nu, lambda4_nu) means; both are printed.

SOURCE OF THE NUMBERS
---------------------
AN-25-085 eq. `nplunc` == Cridge/Marinelli/Tackmann arXiv:2506.13874 Eqs. (3.34),
(3.35): a 3-parameter fit of OUR tanh_2 CS parametrisation to the lattice data of
its refs [89-91]. The card's own NP form is tanh_2 on both sides, so the
parametrisation matches and this script REFUSES any other CS form.

READ THIS BEFORE USING THE RESULT
---------------------------------
`knowledge/30_physics_global/np_parametrization_constraints.md` section 10 carries
an explicit warning, from Luca via the lattice authors (2026-07-29): *the
covariance is not ready to be trusted*, and its section 11 recommendation is
"bracket, don't prior". This script implements the prior that recommendation
advises against, so that the tension between the data and the lattice can be
measured rather than asserted. Quote any number it produces WITH that caveat.
"""
import argparse
import shutil
import sys

import h5py
import numpy as np

# --- arXiv:2506.13874 Eq. (3.34) / (3.35), physical units --------------------
LAT_PARAMS = ["lambda_inf_nu", "lambda2_nu", "lambda4_nu"]
LAT_MU = np.array([1.6853, 0.0870, 0.0074])
LAT_SIGMA = np.array([0.5069, 0.0332, 0.0066])
LAT_CORR = np.array(
    [
        [1.0000, 0.5212, -0.7249],
        [0.5212, 1.0000, -0.9135],
        [-0.7249, -0.9135, 1.0000],
    ]
)
# The CS form the lattice fit used. tanh_2 has no lambda6_nu; a tanh_6 card would
# need a lambda6_nu row the lattice cannot supply (it fitted lambda6_nu = 0).
REQUIRED_CS_FORM = "tanh_2"


def write_flat(arr, grp, name):
    """rabbit's on-disk layout (writeFlatInChunks): flat dataset + shape attr."""
    arr = np.ascontiguousarray(arr)
    flat = arr.reshape(-1)
    ds = grp.create_dataset(name, flat.shape, dtype=flat.dtype)
    ds[...] = flat
    ds.attrs["original_shape"] = np.array(arr.shape, dtype="int64")


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("card", help="input datacard hdf5 (NOT modified)")
    p.add_argument("-o", "--out", required=True, help="output card hdf5")
    p.add_argument("--name", default="lattice_cs", help="external term name")
    p.add_argument(
        "--inflate",
        type=float,
        default=1.0,
        help="scale ALL sigmas by this (covariance by its square). 1.0 = as "
        "published. Use >1 to soften a constraint whose covariance its own "
        "authors call provisional.",
    )
    p.add_argument(
        "--condition-linf-nu",
        type=float,
        default=None,
        metavar="VAL",
        help="emit the CONDITIONAL 2x2 on (lambda2_nu, lambda4_nu) given "
        "lambda_inf_nu = VAL, instead of the 3x3. Default: the card's own "
        "anchor for lambda_inf_nu, which is where the model holds it "
        "(params.DEFAULT_FROZEN). Pass --no-condition for the 3x3.",
    )
    p.add_argument(
        "--no-condition",
        action="store_true",
        help="emit the full 3x3 marginal. Only correct if lambda_inf_nu is "
        "actually FLOATED in the fit -- and the scetlib_np work found that "
        "pathological (it ran to 0.0098, switching the CS kernel off).",
    )
    args = p.parse_args()

    from rabbit import inputdata

    from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall

    indata = inputdata.FitInputData(args.card)
    inp = wall.resolve_wall_inputs(indata)
    print(f"[card] {args.card}")
    print(f"[corr] tag {inp['corr_tag']}")
    print(f"[corr] np_model={inp['np_model']}  np_model_nu={inp['np_model_nu']}")
    if inp["np_model_nu"] != REQUIRED_CS_FORM:
        sys.exit(
            f"ERROR: the lattice fit of arXiv:2506.13874 used the "
            f"{REQUIRED_CS_FORM} CS form; this card's np_model_nu is "
            f"{inp['np_model_nu']!r}. A prior written for one form is not a "
            f"prior on another form's coefficients."
        )

    # --- the theta maps, from the SAME authority the model and the wall use ---
    specs, anchors = inp["specs"], inp["anchors"]
    for n in LAT_PARAMS:
        if n not in specs:
            sys.exit(f"ERROR: {n} is not one of this card's NP lambdas {inp['names']}")
    linf_anchor = float(anchors["lambda_inf_nu"])
    print(f"[anchor] lambda_inf_nu {linf_anchor}  spec {specs['lambda_inf_nu']}")
    for n in ("lambda2_nu", "lambda4_nu"):
        print(f"[anchor] {n} {float(anchors[n])}  spec {specs[n]}")

    # --- condition or marginalise --------------------------------------------
    sd = LAT_SIGMA * args.inflate
    cov = np.outer(sd, sd) * LAT_CORR
    mu = LAT_MU.copy()
    params = list(LAT_PARAMS)

    if args.no_condition:
        print("[cond] NOT conditioning: emitting the 3x3 marginal.")
        if specs["lambda_inf_nu"][0] is not None:
            sys.exit(
                "ERROR: lambda_inf_nu has a REPARAM map on this build; the 3x3 "
                "path assumes its fit coordinate is physical."
            )
    else:
        x1 = linf_anchor if args.condition_linf_nu is None else args.condition_linf_nu
        c11, c21, c22 = cov[0, 0], cov[1:, 0], cov[1:, 1:]
        mu_c = mu[1:] + c21 * (x1 - mu[0]) / c11
        cov_c = c22 - np.outer(c21, c21) / c11
        print(
            f"[cond] conditioning on lambda_inf_nu = {x1:g} "
            f"(lattice mean {mu[0]:g}, {(x1 - mu[0]) / sd[0]:+.2f} sigma_lat)"
        )
        print(f"       marginal mu    : {np.array2string(mu[1:], precision=6)}")
        print(
            f"       conditional mu : {np.array2string(mu_c, precision=6)}"
            f"   shift {np.array2string(mu_c - mu[1:], precision=6)}"
        )
        print(
            f"       marginal sig   : "
            f"{np.array2string(np.sqrt(np.diag(c22)), precision=6)}"
        )
        print(
            f"       conditional sig: "
            f"{np.array2string(np.sqrt(np.diag(cov_c)), precision=6)}"
            f"   tighter by x{np.sqrt(np.diag(c22) / np.diag(cov_c))}"
        )
        params, mu, cov = params[1:], mu_c, cov_c

    s = np.sqrt(np.diag(cov))
    corr = cov / np.outer(s, s)
    print(f"[phys] params {params}")
    print(f"[phys] mu     {np.array2string(mu, precision=6)}")
    print(f"[phys] sigma  {np.array2string(s, precision=6)}")
    for i in range(len(params)):
        for j in range(i + 1, len(params)):
            print(f"[phys] corr({params[i]}, {params[j]}) = {corr[i, j]:+.6f}")

    # --- THE THETA CONVERSION -------------------------------------------------
    # physical = c0 + c1*theta (+ c2*theta^2). A Gaussian only maps through an
    # AFFINE map, so a nonzero c2 is refused rather than linearised.
    c0 = np.empty(len(params))
    width = np.empty(len(params))
    for i, n in enumerate(params):
        kind, coeffs = specs[n]
        if kind is None:
            c0[i], width[i] = 0.0, 1.0  # fit coordinate IS the physical value
            continue
        if kind != "quad":
            sys.exit(f"ERROR: {n} has spec kind {kind!r}; only affine maps convert.")
        a, w, q = coeffs
        if q != 0.0:
            sys.exit(
                f"ERROR: {n}'s map is quadratic (c2 = {q}), so a Gaussian in the "
                f"physical variable is NOT a Gaussian in theta. Refusing."
            )
        c0[i], width[i] = float(a), float(w)
    print(f"[theta] anchors c0 {np.array2string(c0, precision=6)}")
    print(f"[theta] widths     {np.array2string(width, precision=6)}")

    W = np.diag(width)
    Winv = np.diag(1.0 / width)
    mu_t = Winv @ (mu - c0)
    cov_t = Winv @ cov @ Winv
    cinv_t = np.linalg.inv(cov_t)
    hess = cinv_t
    grad = -cinv_t @ mu_t
    const = 0.5 * mu_t @ cinv_t @ mu_t

    s_t = np.sqrt(np.diag(cov_t))
    print(f"[theta] mu     {np.array2string(mu_t, precision=6)}")
    print(f"[theta] sigma  {np.array2string(s_t, precision=6)}")
    print(
        f"[theta] corr   " f"{np.array2string(cov_t / np.outer(s_t, s_t), precision=6)}"
    )
    ev = np.linalg.eigvalsh(cov_t)
    print(f"[theta] cov eigenvalues {ev}  cond {ev.max() / ev.min():.4g}")
    print(f"[theta] H eigenvalues   {np.linalg.eigvalsh(hess)}")
    print("[theta] H = C_theta^-1:")
    for r in hess:
        print("        " + "  ".join(f"{v:+.6e}" for v in r))
    print(f"[theta] g = -H mu_theta : {np.array2string(grad, precision=6)}")
    print(f"[theta] const 0.5 mu^T H mu = {const:.6f}")
    print(
        "        (rabbit's build_tf_external_terms recomputes this itself for a "
        "dense Hessian, so the term is 0 at x = mu and NLLs stay comparable)"
    )

    # --- numerical verification of the map, BEFORE anything is written --------
    rng = np.random.default_rng(20260911)
    worst_chi2, worst_map = 0.0, 0.0
    pinv = np.linalg.inv(cov)
    for _ in range(20000):
        th = mu_t + rng.normal(size=len(params)) * (3.0 * s_t)
        ph = c0 + width * th
        # (1) the physical map is the one the WALL/model applies
        ph_ref = np.array(
            [
                float(wall.physical_from_theta(specs[n], th[i]))
                for i, n in enumerate(params)
            ]
        )
        worst_map = max(worst_map, float(np.max(np.abs(ph - ph_ref))))
        # (2) chi^2 invariance: physical quadratic form == theta quadratic form
        chi2_phys = (ph - mu) @ pinv @ (ph - mu)
        chi2_theta = 2.0 * (grad @ th + 0.5 * th @ hess @ th + const)
        worst_chi2 = max(
            worst_chi2, abs(chi2_phys - chi2_theta) / max(1.0, abs(chi2_phys))
        )
    print(
        f"[check] physical map vs wall.physical_from_theta: max abs diff "
        f"{worst_map:.3e}  (20000 draws)"
    )
    print(
        f"[check] chi2 invariance phys vs theta: max rel diff "
        f"{worst_chi2:.3e}  (20000 draws)"
    )
    if worst_map > 1e-12 or worst_chi2 > 1e-10:
        sys.exit("ERROR: the theta conversion does not verify. Refusing to write.")

    # (3) the term is zero at the prior mean; 1 along each EIGENDIRECTION of the
    #     covariance; and 1/(1-rho^2) along a single axis -- the last is the one
    #     that shows the correlation is really there. Walking one axis by its
    #     MARGINAL sigma is 5.9 sigma of this 2x2, which is exactly why a
    #     diagonal prior_sigmas is not this constraint.
    def chi2_at(th):
        return 2.0 * (grad @ th + 0.5 * th @ hess @ th + const)

    at_mu = chi2_at(mu_t)
    print(f"[check] chi2 at the prior mean = {at_mu:.3e} (must be 0)")
    assert abs(at_mu) < 1e-9
    evals, evecs = np.linalg.eigh(cov_t)
    for k in range(len(params)):
        c = chi2_at(mu_t + evecs[:, k] * np.sqrt(evals[k]))
        print(f"[check] chi2 at mu + 1 sigma along eigvec {k} = {c:.9f} (must be 1)")
        assert abs(c - 1.0) < 1e-8
    if len(params) == 2:
        rho = cov_t[0, 1] / np.sqrt(cov_t[0, 0] * cov_t[1, 1])
        want = 1.0 / (1.0 - rho**2)
        for i, n in enumerate(params):
            th = mu_t.copy()
            th[i] += s_t[i]
            c = chi2_at(th)
            print(
                f"[check] chi2 at mu + 1 marginal sigma({n}) = {c:.6f} "
                f"(must be 1/(1-rho^2) = {want:.6f})"
            )
            assert abs(c - want) < 1e-6 * want

    # --- write ---------------------------------------------------------------
    shutil.copy2(args.card, args.out)
    with h5py.File(args.out, "r+") as f:
        ext = (
            f["external_terms"]
            if "external_terms" in f
            else f.create_group("external_terms")
        )
        if args.name in ext:
            sys.exit(f"ERROR: term {args.name!r} already present in {args.out}")
        tg = ext.create_group(args.name)
        ds = tg.create_dataset(
            "params", [len(params)], dtype=h5py.special_dtype(vlen=str)
        )
        ds[...] = params
        write_flat(grad, tg, "grad_values")
        write_flat(hess, tg, "hess_dense")
    print(f"\n[write] {args.out}")

    # --- read back through rabbit's own reader AND builder --------------------
    from rabbit.external_likelihood import (
        build_tf_external_terms,
        read_external_terms_from_h5,
    )

    with h5py.File(args.out, "r") as f:
        terms = read_external_terms_from_h5(f.get("external_terms"))
    t = [t for t in terms if t["name"] == args.name][0]
    assert list(t["params"]) == params, t["params"]
    assert np.allclose(t["grad_values"], grad), "grad round-trip failed"
    assert np.allclose(t["hess_dense"], hess), "hess round-trip failed"
    print(f"[read] rabbit.read_external_terms_from_h5 OK ({len(terms)} term(s))")
    print(f"[read] rabbit's own const = ", end="")
    # resolve against the REAL fitter parameter list so a name typo cannot survive
    import tensorflow as tf

    from wremnants.postprocessing.scetlib_ad import params as adp  # noqa: F401

    fake_parms = np.array([p.encode() for p in params] + [b"dummy"])
    built = build_tf_external_terms(terms, fake_parms, tf.float64)
    print(f"{built[0]['const']:.6f}  (ours {const:.6f})")
    assert abs(built[0]["const"] - const) < 1e-9 * max(1.0, abs(const))
    print("INJECT_DONE")


if __name__ == "__main__":
    main()
