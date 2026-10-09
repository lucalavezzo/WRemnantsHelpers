#!/usr/bin/env python3
"""T8 step 2: the Z-data pull on lambda4_nu at NOMSTIFF, on the 2D-lattice card (ONE gated cache load).

Fitter built from NOMSTIFF's OWN meta_info command (tau 8, NPDampingWall margin=0), changed only by common.to_2d_card
(2D card, lambda4_nu in fit_params, prior_sigmas lambda2_nu=nan,lambda4_nu=nan), minus -o/--snapshot*/--externalPostfit,
built exactly as rabbit_fit.main() builds it (cf. 261005-cold-min-restart/scripts/term_eval.py).

At NOMSTIFF's vector (lambda4_nu = 0 = theta 0, its default; loaded by name):
  gate: NLL_2D(NOM) == NOMSTIFF.nllvalreduced - (1D term at NOM) + (2D term at NOM)
  grad: dNLL/dtheta(lambda4_nu) split into the lattice term (analytic g + H theta) and the rest (data + BB + wall(=0))
  HVP : the Hessian column along lambda4_nu
  Newton prediction (face held as in NOMSTIFF's cov): H_new = inv(C_NOM) with the lambda2_nu external curvature swapped
        1D -> 2D, bordered by the HVP column. Predicts lambda4_nu, lambda2_nu, dalphaS/sigma_NOM, sigma ratio, dNLL,
        for (i) lambda4_nu floated (with lambda4_nu >= 0) and (ii) lambda4_nu held 0 on the 2D card.
Only differences / sigma units for alphaS. Writes ../l4nu_pull.json; the HVP column goes to OUT (ceph).
"""
import json
import os
import sys
import time

os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=true")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C  # noqa: E402

sys.path.insert(0, f"{C.RT}/bin")
import h5py  # noqa: E402
import numpy as np  # noqa: E402
import tensorflow as tf  # noqa: E402

import rabbit  # noqa: E402
import rabbit_fit  # noqa: E402
from rabbit import fitter as rfitter  # noqa: E402
from rabbit import inputdata, io_tools  # noqa: E402
from rabbit.mappings import helpers as mh  # noqa: E402
from rabbit.param_models import helpers as ph  # noqa: E402
from rabbit.regularization import helpers as rh  # noqa: E402
from wums import logging as wlogging  # noqa: E402

DROP = {"--snapshotFile", "--snapshotInterval", "-o", "--outpath", "--externalPostfit"}


def ext_term(card):
    with h5py.File(card, "r") as f:
        t = f["external_terms/lattice_cs"]
        names = [
            n.decode() if isinstance(n, bytes) else str(n) for n in t["params"][...]
        ]
        g = t["grad_values"][...].reshape(t["grad_values"].attrs["original_shape"])
        H = t["hess_dense"][...].reshape(t["hess_dense"].attrs["original_shape"])
    mu = -np.linalg.solve(H, g)
    return names, g, H, 0.5 * mu @ H @ mu


def nll_ext(term, vals):
    _, g, H, c = term
    v = np.asarray(vals, float)
    return float(g @ v + 0.5 * v @ H @ v + c)


def main():
    print("[t8] rabbit from", rabbit.__file__, flush=True)
    toks = C.nomstiff_tokens()
    new, changes = C.to_2d_card(toks)
    for c in changes:
        print("[t8] change:", c, flush=True)
    argv, i = [], 1
    while i < len(new):
        if new[i] in DROP:
            i += 2
            continue
        argv.append(new[i])
        i += 1
    argv += ["-o", "/tmp"]
    args = rabbit_fit.make_parser().parse_args(argv)
    assert args.regularizationStrength == 8.0
    wlogging.setup_logger("t8", args.verbose, args.noColorLogger)

    frN = io_tools.get_fitresult(C.NOMSTIFF, None)
    nllN = float(frN["nllvalreduced"])
    hN = frN["parms"].get()
    namesN = [n.decode() if isinstance(n, bytes) else str(n) for n in hN.axes[0]]
    xN = np.asarray(hN.values(), float)
    covN = np.asarray(frN["cov"].get().values(), float)

    t0 = time.time()
    indata = inputdata.FitInputData(args.filename, args.pseudoData, host_memory=False)
    param_model = ph.load_models(args.paramModel, indata, **vars(args))
    print(f"[t8] cache loaded + model built in {time.time()-t0:.0f} s", flush=True)
    f = rfitter.make_fitter(
        indata,
        param_model,
        args,
        do_blinding=True,
        globalImpactsFromJVP=not args.globalImpactsDisableJVP,
    )
    f.tau.assign(args.regularizationStrength)
    f.regularizers = [
        rh.load_regularizer(
            m[0], mh.load_mapping(m[1], indata, *m[2:]), dtype=indata.dtype
        )
        for m in args.regularization
    ]
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)
    f.defaultassign()
    f.set_nobs(f.indata.data_obs)
    f.set_blinding_offsets(blind=True)

    names = list(f.parms.astype(str))
    print(
        f"[t8] fitter has {len(names)} parameters; NOMSTIFF {len(namesN)}; "
        f"extra {sorted(set(names) - set(namesN))}; missing {sorted(set(namesN) - set(names))}",
        flush=True,
    )
    assert set(names) - set(namesN) == {"lambda4_nu"} and not set(namesN) - set(names)
    i4, i2, ia = (
        names.index("lambda4_nu"),
        names.index("lambda2_nu"),
        names.index("alphaS"),
    )
    x0_default_l4 = float(f.x.numpy()[i4])
    f.load_fitresult(C.NOMSTIFF, None, profile=True)
    x = f.x.numpy()
    assert x[i4] == 0.0 and x0_default_l4 == 0.0, (x[i4], x0_default_l4)
    idxN = np.array([names.index(n) for n in namesN])
    assert np.array_equal(x[idxN], xN)

    t1D, t2D = ext_term(C.CARD_1D), ext_term(C.CARD_2D)
    assert t1D[0] == ["lambda2_nu"] and t2D[0] == ["lambda2_nu", "lambda4_nu"]
    e1 = nll_ext(t1D, [x[i2]])
    e2 = nll_ext(t2D, [x[i2], x[i4]])
    nll = float(f.reduced_nll().numpy())
    comps = tf.function(
        lambda: f._compute_nll_components(profile=True, full_nll=False)[:4]
    )
    ln, lc, lb, lp = [float(v) if v is not None else 0.0 for v in comps()]
    lext = float(f._compute_external_nll().numpy())
    expect = nllN - e1 + e2
    print(
        f"[gate] NLL_2D(NOM) - (NOMSTIFF - ext1D + ext2D) = {nll-expect:+.3e}   "
        f"(ext1D {e1:.6f}, ext2D {e2:.6f}, rabbit ext {lext:.6f}, wall pen {lp:.3e})",
        flush=True,
    )

    val, g = f.loss_val_grad()
    g = g.numpy()
    _, g2, H2, _ = t2D
    gext = g2 + H2 @ np.array([x[i2], x[i4]])
    g4, g4ext = float(g[i4]), float(gext[1])
    g4rest = g4 - g4ext
    print(
        f"[grad] dNLL/dtheta(lambda4_nu) total {g4:+.6e} = lattice {g4ext:+.6e} + Z data/BB/wall {g4rest:+.6e}",
        flush=True,
    )
    print(
        f"[grad]   per unit physical lambda4_nu (theta width 0.5): total {g4/0.5:+.4e}, lattice {g4ext/0.5:+.4e}, data {g4rest/0.5:+.4e}",
        flush=True,
    )
    print(
        f"[grad] dNLL/dtheta(lambda2_nu) total {g[i2]:+.6e} (lattice 2D part {gext[0]:+.6e}); |grad| over the NOMSTIFF params "
        f"except lambda2_nu: max {np.max(np.abs(np.delete(g, [i2, i4]))):.3e}",
        flush=True,
    )

    e = np.zeros(len(names))
    e[i4] = 1.0
    t = time.time()
    _, _, hcol = f.loss_val_grad_hessp(tf.constant(e, dtype=f.x.dtype))
    hcol = hcol.numpy()
    print(
        f"[hvp] column along lambda4_nu in {time.time()-t:.0f} s: H44 {hcol[i4]:.6e} (lattice part {H2[1,1]:.6e}, data {hcol[i4]-H2[1,1]:.6e}); "
        f"H(l4,l2) {hcol[i2]:.6e} (lattice {H2[0,1]:.6e})",
        flush=True,
    )
    os.makedirs(C.OUT, exist_ok=True)
    np.savez(
        f"{C.OUT}/l4nu_hvp_column_at_NOMSTIFF.npz",
        names=np.array(names),
        hcol=hcol,
        grad=g,
    )

    # ---- Newton prediction (theta units)
    from wremnants.postprocessing.scetlib_ad import params as P

    WID = {}
    for n in ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]:
        rp = P.reparam(n)
        WID[n] = rp[1][0] if (rp is not None and rp[0] == "unit") else 1.0
    print(f"[newton] REPARAM widths {WID}", flush=True)
    assert WID["lambda2_nu"] == 0.1 and WID["lambda4_nu"] == 0.5
    HN = np.linalg.inv(
        covN
    )  # NOMSTIFF's Hessian (1D lattice term + engaged stiff spring)
    jN2 = namesN.index("lambda2_nu")
    S = HN.copy()
    S[jN2, jN2] += (
        -t1D[2][0, 0] + H2[0, 0]
    )  # swap the lambda2_nu external curvature 1D -> 2D
    gS = g[idxN]  # 2D-card gradient on the old params
    b = hcol[idxN]
    c44 = hcol[i4]
    Hfull = np.block([[S, b[:, None]], [b[None, :], np.array([[c44]])]])
    gfull = np.concatenate([gS, [g4]])
    d_float = -np.linalg.solve(Hfull, gfull)
    d_hold = -np.linalg.solve(S, gS)
    Cf = np.linalg.inv(Hfull)
    Ch = np.linalg.inv(S)
    ja = namesN.index("alphaS")
    sN = np.sqrt(covN[ja, ja])
    res = {}
    for lab, d, Cx, nl4 in [
        ("float", d_float, Cf, d_float[-1]),
        ("hold0_2Dcard", d_hold, Ch, 0.0),
    ]:
        dN = d[: len(namesN)]
        res[lab] = dict(
            dtheta_l4=float(nl4),
            lambda4_nu=0.0 + 0.5 * float(nl4),
            lambda2_nu=float(0.15 + 0.1 * (xN[jN2] + dN[jN2])),
            dlambda2_nu=float(0.1 * dN[jN2]),
            dalphaS_over_sigNOM=float(dN[ja] / sN),
            sigma_ratio=float(np.sqrt(Cx[ja, ja]) / sN),
            dNLL_pred=float(0.5 * (gfull[: len(d)] if lab == "float" else gS) @ d),
            tmd_dphys={
                n: float(dN[namesN.index(n)] * WID[n])
                for n in ["lambda2", "lambda4", "delta_lambda2"]
            },
        )
        print(f"[newton {lab}] {res[lab]}", flush=True)
    if d_float[-1] < 0:
        print(
            "[newton] the floated step goes INTO the wall (lambda4_nu < 0): the constrained answer is hold0_2Dcard",
            flush=True,
        )
    # the TMD reparam widths are not all 0.1: record the theta steps too
    res["dtheta_tmd_float"] = {
        n: float(d_float[namesN.index(n)])
        for n in ["lambda2", "lambda4", "delta_lambda2"]
    }
    res["dtheta_tmd_hold"] = {
        n: float(d_hold[namesN.index(n)])
        for n in ["lambda2", "lambda4", "delta_lambda2"]
    }
    out = dict(
        changes=changes,
        gate=nll - expect,
        ext1D_NOM=e1,
        ext2D_NOM=e2,
        rabbit_ext=lext,
        wall_pen=lp,
        grad_l4_theta=dict(total=g4, lattice=g4ext, data=g4rest),
        grad_l2_theta=dict(total=float(g[i2]), lattice2D=float(gext[0])),
        H44=float(hcol[i4]),
        H44_lattice=float(H2[1, 1]),
        H42=float(hcol[i2]),
        H42_lattice=float(H2[0, 1]),
        rho_alphaS_l4_float=float(Cf[ja, -1] / np.sqrt(Cf[ja, ja] * Cf[-1, -1])),
        sigma_l4_phys_float=float(0.5 * np.sqrt(Cf[-1, -1])),
        newton=res,
    )
    json.dump(out, open(f"{C.TASK}/l4nu_pull.json", "w"), indent=1)
    print("[t8] wrote l4nu_pull.json", flush=True)


if __name__ == "__main__":
    main()
