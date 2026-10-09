#!/usr/bin/env python3
"""Inject OUR ASWZ lattice CS-kernel constraint into a scetlib_ad datacard as a
rabbit EXTERNAL LIKELIHOOD TERM in the model's THETA coordinate.

Adapted from
``studies/scetlib-ad-param-model/260911-lattice-constraints/scripts/inject_lattice_cs_prior_theta.py``
(read its docstring for the mechanism and the reasons it is not ``prior_sigmas``
and not a ``Regularizer``). Three things change, everything else is kept:

1. THE CONSTRAINT. Not the Tackmann/Cridge 3x3 (AN eq. nplunc) but our own fit
   of the SCETlib tanh_2 CS kernel to the ASWZ (arXiv:2402.06725) per-ensemble
   lattice data, ``studies/lattice-cs-kernel/260923-scetlib-kernel-fit``:
   tanh_2, lambda_inf_nu = 2 FIXED, the lattice-spacing term k1*a/b_T PROFILED,
   n_f = 5 perturbative kernel. Read from that task's ``fit_results.json``
   (entry ``tanh2 | linf=2 | k1``), not retyped. The 2x2 (lambda2_nu,
   lambda4_nu) block of its 3x3 (l2, l4, k1) covariance is the covariance
   MARGINALISED over k1 -- for a Gaussian the marginal is the sub-block.

2. NO CONDITIONING. That fit already holds lambda_inf_nu at 2, the value every
   AD fit freezes it at (``params.DEFAULT_FROZEN``, anchor from the card's
   correction). The script REFUSES a card whose lambda_inf_nu anchor is not 2.

3. A SYSTEMATIC COVARIANCE from that task's variant fits (all at linf=2):
     n_f scheme        nf4 scheme  |  nf5 matched at mu=1      -> ONE shift, the larger
     k-form            k2 only     |  k1+k2                    -> ONE shift, the larger
     b_T window        drop b_T < 0.2 fm                        -> one shift
   "Larger" = larger chi^2 of the shift under the STAT covariance (so it is
   judged in the metric the constraint actually uses). The two n_f variants are
   alternative treatments of the SAME question (which flavour scheme the
   lattice's n_f=4 kernel should be compared in), and their shifts agree to 3 %
   -- adding both would double-count one effect. Same logic for the k-form:
   k2-only and k1+k2 are alternatives to the nominal k1, not independent
   effects. C_syst = sum_i d_i d_i^T over the three chosen shifts, treated as
   independent and fully correlated between lambda2_nu and lambda4_nu within
   each shift (which is what d d^T says). ``--syst none`` gives stat-only.

The theta conversion, checks and write/round-trip are unchanged from 260911:

    physical = anchor + width * theta   (params.REPARAM width, card anchor)
    mu_theta = W^-1 (mu - anchor)       C_theta = W^-1 C W^-1
    H_theta  = W C^-1 W                 g_theta = -H_theta mu_theta

and a non-affine (quadratic) map is refused.

``--l4zero`` (added 2026-09-23 late, Luca-approved design): a 1D constraint on
lambda2_nu ONLY, for fits that FREEZE lambda4_nu at its anchor (0). Numbers are
the DIRECT lattice refit at lambda4_nu = 0 (lambda_inf_nu = 2, k1 profiled) from
``260923-scetlib-kernel-fit/fit_l4zero.json`` key ``lambda2_nu`` (central, stat,
tot = stat (+) syst, syst from the same three-group sum of d d^T), NOT the
Gaussian conditional of the 2D fit (0.108, biased low -- see that task's LOGBOOK
section 6). The script refuses unless the card's lambda4_nu anchor is 0, since
the constraint is only valid on that slice.
"""
import argparse
import json
import shutil
import sys

import h5py
import numpy as np

KFIT = (
    "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/"
    "260923-scetlib-kernel-fit/fit_results.json"
)
KFIT_L4Z = (
    "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/"
    "260923-scetlib-kernel-fit/fit_l4zero.json"
)
NOMINAL = "tanh2 | linf=2 | k1"
NOMINAL_L4Z = "L4=0 | linf=2 | k1 [nominal]"
# groups of alternative variants; one shift (the largest) is taken per group
SYST_GROUPS = {
    "n_f scheme": ["SYST nf4 scheme, linf=2", "SYST nf matched mu=1, linf=2"],
    "k-form": ["SYST k2, linf=2", "SYST k1+k2, linf=2"],
    "b_T window": ["SYST drop bT<0.2 fm, linf=2"],
}
PARAMS = ["lambda2_nu", "lambda4_nu"]
KEYS = ["l2", "l4"]
REQUIRED_CS_FORM = "tanh_2"
LINF_NU_FIT = 2.0


def write_flat(arr, grp, name):
    """rabbit's on-disk layout (writeFlatInChunks): flat dataset + shape attr."""
    arr = np.ascontiguousarray(arr)
    flat = arr.reshape(-1)
    ds = grp.create_dataset(name, flat.shape, dtype=flat.dtype)
    ds[...] = flat
    ds.attrs["original_shape"] = np.array(arr.shape, dtype="int64")


def build_constraint(kfit_path, syst):
    d = json.load(open(kfit_path))
    nom = d[NOMINAL]
    assert nom["fixed"]["linf"] == LINF_NU_FIT, nom["fixed"]
    assert nom["free"][:2] == KEYS, nom["free"]
    mu = np.array([nom["x"][k] for k in KEYS])
    cstat = np.array(nom["cov"])[:2, :2]
    print(f"[lat] source {kfit_path} :: {NOMINAL!r}")
    print(
        f"[lat] chi2 {nom['chi2']:.3f} / ndf {nom['ndf']}  fixed {nom['fixed']}"
        f"  (k1 profiled -> 2x2 block is the k1-marginal)"
    )
    print(f"[lat] mu        {mu}")
    s = np.sqrt(np.diag(cstat))
    print(f"[lat] sigma_stat {s}  rho {cstat[0, 1] / s[0] / s[1]:+.4f}")
    cinv = np.linalg.inv(cstat)
    csyst = np.zeros((2, 2))
    chosen = {}
    for grp, variants in SYST_GROUPS.items():
        best = None
        for v in variants:
            e = d[v]
            assert e["fixed"].get("linf") == LINF_NU_FIT, (v, e["fixed"])
            dv = np.array([e["x"][k] for k in KEYS]) - mu
            c2 = float(dv @ cinv @ dv)
            print(
                f"[syst] {grp:11s} {v:32s} d = ({dv[0]:+.5f}, {dv[1]:+.6f})"
                f"  chi2_stat(d) = {c2:.3f}"
            )
            if best is None or c2 > best[2]:
                best = (v, dv, c2)
        chosen[grp] = best
        csyst += np.outer(best[1], best[1])
    for grp, (v, dv, c2) in chosen.items():
        print(f"[syst] TAKEN for {grp!r}: {v}  (chi2_stat {c2:.3f})")
    ss = np.sqrt(np.diag(csyst))
    print(f"[syst] sigma_syst {ss}  rho {csyst[0, 1] / ss[0] / ss[1]:+.4f}")
    ctot = cstat + csyst
    st = np.sqrt(np.diag(ctot))
    print(f"[tot ] sigma_tot  {st}  rho {ctot[0, 1] / st[0] / st[1]:+.4f}")
    if syst == "none":
        print("[use ] STAT ONLY")
        return mu, cstat, dict(cstat=cstat, csyst=csyst, chosen=chosen)
    print("[use ] STAT + SYST (primary)")
    return mu, ctot, dict(cstat=cstat, csyst=csyst, chosen=chosen)


def build_constraint_l4zero(path, syst):
    d = json.load(open(path))
    nom = d["fits"][NOMINAL_L4Z]
    assert nom["fixed"]["linf"] == LINF_NU_FIT and nom["fixed"]["l4"] == 0.0, nom[
        "fixed"
    ]
    s = d["lambda2_nu"]
    assert (
        abs(s["central"] - nom["x"]["l2"]) < 1e-15
        and abs(s["stat"] - nom["err"]["l2"]) < 1e-15
    )
    print(f"[lat] source {path} :: {NOMINAL_L4Z!r} + summary 'lambda2_nu'")
    print(
        f"[lat] chi2 {nom['chi2']:.3f} / ndf {nom['ndf']}  fixed {nom['fixed']}  (k1 profiled)"
    )
    print(
        f"[lat] lambda2_nu = {s['central']:.6f}  stat {s['stat']:.6f}  syst {s['syst']:.6f}  tot {s['tot']:.6f}"
    )
    for grp, (v, dv) in s["chosen"].items():
        print(f"[syst] TAKEN for {grp!r}: {v}  d = {dv:+.6f}")
    assert abs(np.sqrt(s["stat"] ** 2 + s["syst"] ** 2) - s["tot"]) < 1e-12
    assert (
        abs(np.sqrt(sum(dv**2 for _, dv in s["chosen"].values())) - s["syst"]) < 1e-12
    )
    sig = s["stat"] if syst == "none" else s["tot"]
    print(
        f"[use ] {'STAT ONLY' if syst == 'none' else 'STAT + SYST (primary)'}: sigma {sig:.6f}"
    )
    return np.array([s["central"]]), np.array([[sig**2]])


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("card", help="input datacard hdf5 (NOT modified)")
    p.add_argument("-o", "--out", help="output card hdf5 (omit with --dry-run)")
    p.add_argument("--name", default="lattice_cs", help="external term name")
    p.add_argument("--syst", choices=["default", "none"], default="default")
    p.add_argument("--kfit", default=KFIT)
    p.add_argument("--dry-run", action="store_true", help="print, do not write")
    p.add_argument(
        "--l4zero",
        action="store_true",
        help="1D lambda2_nu constraint on the lambda4_nu = 0 slice",
    )
    args = p.parse_args()

    global PARAMS
    if args.l4zero:
        PARAMS = ["lambda2_nu"]
        mu, cov = build_constraint_l4zero(KFIT_L4Z, args.syst)
    else:
        mu, cov, _ = build_constraint(args.kfit, args.syst)
    npar = len(PARAMS)

    from rabbit import inputdata

    from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall

    indata = inputdata.FitInputData(args.card)
    inp = wall.resolve_wall_inputs(indata)
    print(f"[card] {args.card}")
    print(f"[corr] tag {inp['corr_tag']}")
    print(f"[corr] np_model={inp['np_model']}  np_model_nu={inp['np_model_nu']}")
    if inp["np_model_nu"] != REQUIRED_CS_FORM:
        sys.exit(f"ERROR: np_model_nu is {inp['np_model_nu']!r}, need tanh_2.")
    if getattr(indata, "external_terms", None):
        names = [t["name"] for t in indata.external_terms]
        sys.exit(f"ERROR: input card already carries external terms {names}.")
    specs, anchors = inp["specs"], inp["anchors"]
    for n in PARAMS + ["lambda_inf_nu", "lambda4_nu"]:
        if n not in specs:
            sys.exit(f"ERROR: {n} is not one of this card's NP lambdas {inp['names']}")
        print(f"[anchor] {n} = {anchors[n]}  spec {specs[n]}")
    if abs(float(anchors["lambda_inf_nu"]) - LINF_NU_FIT) > 1e-12:
        sys.exit(
            f"ERROR: card holds lambda_inf_nu at {anchors['lambda_inf_nu']}, the "
            f"lattice fit at {LINF_NU_FIT}. The constraint is conditional on it."
        )
    if args.l4zero and abs(float(anchors["lambda4_nu"])) > 0.0:
        sys.exit(
            f"ERROR: --l4zero needs the card's lambda4_nu anchor at 0, got {anchors['lambda4_nu']}."
        )

    s = np.sqrt(np.diag(cov))
    corr = cov / np.outer(s, s)
    print(f"[phys] params {PARAMS}")
    print(f"[phys] mu     {np.array2string(mu, precision=6)}")
    print(f"[phys] sigma  {np.array2string(s, precision=6)}")
    if npar == 2:
        print(f"[phys] corr   {corr[0, 1]:+.6f}")

    # --- THE THETA CONVERSION (affine only) ----------------------------------
    c0 = np.empty(npar)
    width = np.empty(npar)
    for i, n in enumerate(PARAMS):
        kind, coeffs = specs[n]
        if kind is None:
            c0[i], width[i] = 0.0, 1.0
            continue
        if kind != "quad":
            sys.exit(f"ERROR: {n} has spec kind {kind!r}; only affine maps convert.")
        a, w, q = coeffs
        if q != 0.0:
            sys.exit(f"ERROR: {n}'s map is quadratic (c2 = {q}). Refusing.")
        c0[i], width[i] = float(a), float(w)
    print(f"[theta] anchors c0 {c0}")
    print(f"[theta] widths     {width}")
    Winv = np.diag(1.0 / width)
    mu_t = Winv @ (mu - c0)
    cov_t = Winv @ cov @ Winv
    hess = np.linalg.inv(cov_t)
    grad = -hess @ mu_t
    const = 0.5 * mu_t @ hess @ mu_t
    s_t = np.sqrt(np.diag(cov_t))
    print(f"[theta] mu     {np.array2string(mu_t, precision=6)}")
    print(f"[theta] sigma  {np.array2string(s_t, precision=6)}")
    ev = np.linalg.eigvalsh(cov_t)
    print(f"[theta] cov eigenvalues {ev}  cond {ev.max() / ev.min():.4g}")
    print(f"[theta] H eigenvalues   {np.linalg.eigvalsh(hess)}")
    print("[theta] H = C_theta^-1:")
    for r in hess:
        print("        " + "  ".join(f"{v:+.9e}" for v in r))
    print(f"[theta] g = -H mu_theta : {np.array2string(grad, precision=9)}")
    print(f"[theta] const 0.5 mu^T H mu = {const:.9f}")

    # --- verification BEFORE anything is written -----------------------------
    rng = np.random.default_rng(20260923)
    worst_chi2, worst_map = 0.0, 0.0
    pinv = np.linalg.inv(cov)
    for _ in range(20000):
        th = mu_t + rng.normal(size=npar) * (3.0 * s_t)
        ph = c0 + width * th
        ph_ref = np.array(
            [
                float(wall.physical_from_theta(specs[n], th[i]))
                for i, n in enumerate(PARAMS)
            ]
        )
        worst_map = max(worst_map, float(np.max(np.abs(ph - ph_ref))))
        chi2_phys = (ph - mu) @ pinv @ (ph - mu)
        chi2_theta = 2.0 * (grad @ th + 0.5 * th @ hess @ th + const)
        worst_chi2 = max(
            worst_chi2, abs(chi2_phys - chi2_theta) / max(1.0, abs(chi2_phys))
        )
    print(
        f"[check] map vs wall.physical_from_theta: max abs diff {worst_map:.3e} (20000 draws)"
    )
    print(f"[check] chi2 invariance phys vs theta: max rel diff {worst_chi2:.3e}")
    if worst_map > 1e-12 or worst_chi2 > 1e-10:
        sys.exit("ERROR: the theta conversion does not verify. Refusing to write.")

    def chi2_at(th):
        return 2.0 * (grad @ th + 0.5 * th @ hess @ th + const)

    at_mu = chi2_at(mu_t)
    print(f"[check] chi2 at the prior mean = {at_mu:.3e} (must be 0)")
    assert abs(at_mu) < 1e-9
    evals, evecs = np.linalg.eigh(cov_t)
    for k in range(npar):
        c = chi2_at(mu_t + evecs[:, k] * np.sqrt(evals[k]))
        print(f"[check] chi2 at mu + 1 sigma along eigvec {k} = {c:.9f} (must be 1)")
        assert abs(c - 1.0) < 1e-8
    rho = cov_t[0, 1] / np.sqrt(cov_t[0, 0] * cov_t[1, 1]) if npar == 2 else 0.0
    want = 1.0 / (1.0 - rho**2)
    for i, n in enumerate(PARAMS):
        th = mu_t.copy()
        th[i] += s_t[i]
        c = chi2_at(th)
        print(
            f"[check] chi2 at mu + 1 marginal sigma({n}) = {c:.6f} (1/(1-rho^2) = {want:.6f})"
        )
        assert abs(c - want) < 1e-6 * want
    # the anchor (theta = 0) under this constraint, for reference
    print(
        f"[info ] chi2_lat at the card anchor (theta=0) = {chi2_at(np.zeros(npar)):.4f}"
    )

    if args.dry_run:
        print("DRY_RUN_DONE (nothing written)")
        return
    if not args.out:
        sys.exit("ERROR: -o required unless --dry-run")

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
        ds = tg.create_dataset("params", [npar], dtype=h5py.special_dtype(vlen=str))
        ds[...] = PARAMS
        write_flat(grad, tg, "grad_values")
        write_flat(hess, tg, "hess_dense")
    print(f"\n[write] {args.out}")

    from rabbit.external_likelihood import (
        build_tf_external_terms,
        read_external_terms_from_h5,
    )

    with h5py.File(args.out, "r") as f:
        terms = read_external_terms_from_h5(f.get("external_terms"))
    t = [t for t in terms if t["name"] == args.name][0]
    assert list(t["params"]) == PARAMS, t["params"]
    assert np.allclose(t["grad_values"], grad), "grad round-trip failed"
    assert np.allclose(t["hess_dense"], hess), "hess round-trip failed"
    print(f"[read] rabbit.read_external_terms_from_h5 OK ({len(terms)} term(s))")
    import tensorflow as tf

    fake_parms = np.array([p.encode() for p in PARAMS] + [b"dummy"])
    built = build_tf_external_terms(terms, fake_parms, tf.float64)
    print(f"[read] rabbit's own const = {built[0]['const']:.9f}  (ours {const:.9f})")
    assert abs(built[0]["const"] - const) < 1e-9 * max(1.0, abs(const))
    # and through the real reader of the whole card
    ind2 = inputdata.FitInputData(args.out)
    names2 = [t["name"] for t in ind2.external_terms]
    print(f"[read] FitInputData(out).external_terms = {names2}")
    assert names2 == [args.name]
    print("INJECT_DONE")


if __name__ == "__main__":
    main()
