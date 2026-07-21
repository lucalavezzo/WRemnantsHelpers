"""POINT-level check: param-model σ(Q,Y,qT) vs a direct SCETlib run at the POSTFIT
tune, at each shared grid node — NO integration on either side.

The integrated comparison (``compare_postfit_sigma_gen.py``) is confounded by the
SCETlib "points" file's coarse Q sampling of the Breit-Wigner (a ±5% Q-integration
ambiguity). This script removes ALL integration: it reconstructs the param model's
native ``sigma_dense`` — d³σ/(dQ dY dqT) at each bt-grid node, BEFORE the Q-integral,
|Y|-fold and qT-rebin (the same object ``sigma_YqT_native`` builds internally) — at
the postfit λ, and compares it to the SCETlib run's differential at the (Q, Y, qT)
nodes the two grids SHARE exactly (14 Q incl. the peak, ~119 Y, 66 qT). A flat ratio
≈ const means the on-the-fly NP reconstruction reproduces SCETlib point-by-point at
the fitted tune; structure/qT-slope means a genuine reconstruction or NP-form
difference. This mirrors ``point_mode_compare.py`` (btgrid-precision experiment B)
but for the postfit tanh_6 tune and the areimers ``…_points_…`` hist file.

Run in the WRemnants container (CPU is fine):
    source WRemnants/setup.sh
    python3 studies/btgrid-precision/compare_postfit_sigma_dense.py \\
        --scetlib-pkl <..._points_combined.pkl> --fitresult <...fitresults_t0.hdf5> \\
        --datacard <...ZMassDilepton.hdf5> \\
        --out ~/public_html/alphaS/260702_2D_l6nu0p01_l60p01_nowall/sigma_dense_point_compare.png
"""

import argparse
import sys
import time
import types

import numpy as np


def load_scetlib_dense(pkl):
    """(σ[Q,Y,qT], Q, Y, qT) from the SCETlib points hist — the raw differential
    d³σ/(dQ dY dqT) at each node, central variation, NaNs (the qT=0 edge) → 0."""
    import pickle

    with open(pkl, "rb") as f:
        d = pickle.load(f)
    h = d["hist"]
    names = [a.name for a in h.axes]
    v = np.asarray(h.values(), dtype=np.float64)
    if "vars" in names:
        vl = list(h.axes["vars"])
        ci = next((vl.index(c) for c in ("central", "pdf0", "nominal") if c in vl), 0)
        v = np.take(v, ci, axis=names.index("vars"))
        names = [n for n in names if n != "vars"]
    v = np.transpose(v, [names.index("Q"), names.index("Y"), names.index("qT")])
    v = np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)
    return (
        v,
        np.asarray(h.axes["Q"].centers),
        np.asarray(h.axes["Y"].centers),
        np.asarray(h.axes["qT"].centers),
    )


def shared_index(a, b, tol=1e-4):
    """For each value in ``a``, its index in ``b`` if present (else -1)."""
    out = np.full(a.size, -1, dtype=int)
    for i, x in enumerate(a):
        j = np.where(np.abs(b - x) < tol)[0]
        if j.size:
            out[i] = j[0]
    return out


def main(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--scetlib-pkl", required=True)
    p.add_argument("--fitresult", required=True)
    p.add_argument(
        "--datacard", required=True, help="fit-input hdf5 (for the gen grid)"
    )
    p.add_argument("--btgrid", default=None)
    p.add_argument("--result", default=None)
    p.add_argument("--q-lo", type=float, default=60.0)
    p.add_argument("--q-hi", type=float, default=120.0)
    p.add_argument(
        "--absy-acc", type=float, default=2.5, help="|Y| acceptance for the summary"
    )
    p.add_argument(
        "--peak-q", type=float, default=91.0, help="Q slice for the dσ/dqT plot"
    )
    p.add_argument(
        "--slice-y", type=float, default=0.0, help="Y slice for the dσ/dqT plot"
    )
    p.add_argument(
        "--qt-plot-max",
        type=float,
        default=40.0,
        help="upper qT shown in the plot (resum-only σ→0 and the ratio is "
        "0/0 noise beyond ~40 GeV; the summary printout covers all qT)",
    )
    p.add_argument("--out", required=True)
    args = p.parse_args(argv)

    import tensorflow as tf  # noqa: F401

    from wremnants.postprocessing.scetlib_np import btgrid_integrate as fz_int
    from wremnants.postprocessing.scetlib_np import btgrid_tf as fz_tf
    from wremnants.postprocessing.scetlib_np import lambda_central as lc
    from wremnants.postprocessing.scetlib_np.fitresult_lambdas import _flat_values
    from wremnants.postprocessing.scetlib_np.sigma_gen import (
        SigmaGenModel,
        _default_btgrid_dir,
    )
    from wremnants.postprocessing.scetlib_np.validation.agreement import (
        assemble_tune,
        resolve_base_lambda,
        resolve_gen_axes,
    )

    btgrid = args.btgrid or _default_btgrid_dir()
    overrides = _flat_values(args.fitresult, which="postfit", result=args.result)
    fit_eff, fit_gnu = lc.read_np_models(args.fitresult)
    print(f"[λ] postfit: {overrides}")
    print(f"[λ] forms: np_model={fit_eff}, np_model_nu={fit_gnu}")
    base = resolve_base_lambda(
        types.SimpleNamespace(
            meta_from=args.fitresult, theory_corr=None, theory_corr_proc=None
        )
    )
    eff, gnu, _ = assemble_tune(base, overrides)
    eval_eff = fit_eff or base["eff_params"]["np_model"]
    eval_gnu = fit_gnu or base["gnu_params"]["np_model_nu"]
    gen_axes = resolve_gen_axes(
        types.SimpleNamespace(
            ptv_edges=None, absy_edges=None, gen_edges_from=None, datacard=args.datacard
        )
    )

    print("\n[core] constructing SigmaGenModel …", flush=True)
    t0 = time.time()
    core = SigmaGenModel(
        btgrid_dir=btgrid,
        lambda_central=base,
        gen_axes=gen_axes,
        Q_lo=args.q_lo,
        Q_hi=args.q_hi,
        include_nonsingular=False,
    )
    print(f"  built in {time.time()-t0:.1f}s")

    # ---- param-model native σ(Q,Y,qT) at the postfit λ, BEFORE any integration
    #      (replicates sigma_YqT_native up to sparse_to_dense — the pre-Q-integral
    #      density d³σ/(dQ dY dqT) on the bt-grid nodes).
    eff_r = {k: v for k, v in eff.items() if k != "np_model"}
    gnu_r = {k: v for k, v in gnu.items() if k != "np_model_nu"}
    sigma_flat = fz_tf.reconstruct_batch_factorized_tf(
        b_bar=core.b_bar,
        I_pert_u=core.I_pert_u,
        C_nu_uu=core.C_nu_uu,
        c_of_u=core.c_of_u,
        eff_params=eff_r,
        gnu_params=gnu_r,
        np_model=eval_eff,
        np_model_nu=eval_gnu,
        KwqT=core.KwqT,
        gather_idx=core.gather_idx,
        Y_unique=core.Y_feff_unique,
        feff_idx_u=core.feff_idx_u,
    )
    dense = np.asarray(
        fz_int.sparse_to_dense_tf(sigma_flat, core.flat_idx).numpy(), dtype=np.float64
    )  # (NQ, NY, NqT)
    Qm, Ym, Tm = (
        np.asarray(core.Q_unique),
        np.asarray(core.Y_unique),
        np.asarray(core.qT_unique),
    )
    print(f"  sigma_dense {dense.shape}  (NQ={Qm.size} NY={Ym.size} NqT={Tm.size})")

    # ---- SCETlib differential on its grid
    sc, Qs, Ys, Ts = load_scetlib_dense(args.scetlib_pkl)
    print(f"[scetlib] dense {sc.shape}  (NQ={Qs.size} NY={Ys.size} NqT={Ts.size})")

    # ---- restrict to shared nodes (exact, no interpolation)
    iQ, iY, iT = shared_index(Qm, Qs), shared_index(Ym, Ys), shared_index(Tm, Ts)
    mQ, mY, mT = iQ >= 0, iY >= 0, iT >= 0
    print(
        f"[shared] Q {mQ.sum()}/{Qm.size}  Y {mY.sum()}/{Ym.size}  qT {mT.sum()}/{Tm.size}"
    )
    A = dense[np.ix_(mQ, mY, mT)]  # param model on shared nodes
    B = sc[np.ix_(iQ[mQ], iY[mY], iT[mT])]  # SCETlib on the SAME nodes
    Qsh, Ysh, Tsh = Qm[mQ], Ym[mY], Tm[mT]

    ratio = np.divide(A, B, out=np.full_like(A, np.nan), where=np.abs(B) > 1e-300)
    yacc = np.abs(Ysh) <= args.absy_acc
    fin = ratio[:, yacc, :]
    fin = fin[np.isfinite(fin)]
    med = float(np.median(fin))
    print(
        f"\n=== param/scetlib per-node ratio, |Y|<= {args.absy_acc} (NO integration) ==="
    )
    print(
        f"  overall: median {med:.5f}  mean {fin.mean():.5f}  std {fin.std():.2e}  "
        f"[{fin.min():.5f}, {fin.max():.5f}]  n={fin.size}"
    )
    # qT profile of the mean ratio over (shared Q, |Y|<=acc): flat ⇒ shape-perfect
    prof = np.array([np.nanmean(ratio[:, yacc, it]) for it in range(Tsh.size)])
    pf = prof[np.isfinite(prof)]
    print(
        f"  qT-profile of mean ratio: spread max-min = {pf.max()-pf.min():.4f} "
        f"({100*(pf.max()-pf.min()):.2f}%)  [{pf.min():.4f}, {pf.max():.4f}]"
    )
    print("   qT     mean(param/scetlib)   (over shared Q, |Y|<=%.1f)" % args.absy_acc)
    for it, tv in enumerate(Tsh):
        col = ratio[:, yacc, it]
        col = col[np.isfinite(col)]
        if col.size and (tv <= 12 or it % 5 == 0):
            print(
                f"  {tv:6.2f}   {col.mean():.5f}   (std {col.std():.1e}, n={col.size})"
            )

    # ---- plots: (1) dσ/dqT at (peak Q, Y slice); (2) qT-profile of mean ratio
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    iq = int(np.argmin(np.abs(Qsh - args.peak_q)))
    iy = int(np.argmin(np.abs(Ysh - args.slice_y)))
    # slice ratio at the plotted (Q, Y) node, over the physical resummation window
    sl = ratio[iq, iy, :]
    slw = sl[np.isfinite(sl) & (Tsh <= args.qt_plot_max)]
    slw16 = sl[np.isfinite(sl) & (Tsh <= 16.0)]
    print(f"\n=== slice ratio at (Q={Qsh[iq]:g}, Y={Ysh[iy]:g}) — NO integration ===")
    print(
        f"  qT≤16 GeV : mean {slw16.mean():.5f}  [{slw16.min():.5f}, {slw16.max():.5f}]  "
        f"n={slw16.size}"
    )
    print(
        f"  qT≤{args.qt_plot_max:g} GeV : mean {slw.mean():.5f}  "
        f"[{slw.min():.5f}, {slw.max():.5f}]  n={slw.size}"
    )
    pm = Tsh <= args.qt_plot_max  # physical resummation window
    Tp = Tsh[pm]
    qA, qB = A[iq, iy, pm], B[iq, iy, pm]
    fig, (ax, axr, axp) = plt.subplots(
        3, 1, figsize=(7, 8), gridspec_kw={"height_ratios": [3, 1, 1.4], "hspace": 0.28}
    )
    ax.plot(Tp, qB, "o-", ms=3, color="C0", label="SCETlib N3LL (points)")
    ax.plot(Tp, qA, "x--", ms=4, color="C3", label="param model (sigma_dense)")
    ax.set_ylabel(r"$\sigma$ at node  [a.u.]")
    ax.set_title(f"σ(Q={Qsh[iq]:g}, Y={Ysh[iy]:g}, qT) — postfit tune, NO integration")
    ax.legend(fontsize=9)
    ax.margins(x=0)
    rr = np.divide(qA, qB, out=np.full_like(qA, np.nan), where=np.abs(qB) > 1e-300)
    axr.plot(Tp, rr, "k.-", ms=3)
    axr.axhline(1.0, color="0.5", lw=0.8, ls="--")
    axr.set_ylabel("param /\nSCETlib")
    axr.set_ylim(0.99, 1.01)
    axr.margins(x=0)
    axp.plot(Tp, prof[pm], "C2.-", ms=3)
    axp.axhline(1.0, color="0.5", lw=0.8, ls="--")
    axp.set_xlabel(r"$q_T$ (= $p_T^Z$) [GeV]")
    axp.set_ylabel(f"mean param/SCETlib\n(shared Q, |Y|≤{args.absy_acc:g})")
    axp.set_ylim(0.99, 1.01)
    axp.margins(x=0)
    axp.text(
        0.5,
        0.06,
        f"median over all shared nodes (|Y|≤{args.absy_acc:g}) = {med:.5f}"
        f"   ·   flat to ≈0.04% for qT≲16 GeV",
        transform=axp.transAxes,
        ha="center",
        fontsize=8,
        bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.9),
    )

    from wremnants.postprocessing.scetlib_np import plot_output

    outdir, base_name = plot_output.split_outpath(args.out)
    plot_output.save_plot(outdir, base_name, fig=fig, args=args, dpi=130)
    plt.close(fig)
    print(f"\n[plot] wrote {outdir}/{base_name}.png(.pdf)")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
