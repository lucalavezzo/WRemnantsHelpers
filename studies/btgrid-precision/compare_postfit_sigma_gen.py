"""Compare the param-model resum-only σ_gen at the POSTFIT λ against a direct
SCETlib point-grid run at the SAME postfit λ.

This extends the btgrid-precision triangulation (previously done at λ_central via
export_spectrum + plot_precision_compare) to the *postfit* tune — the physically
awkward point with λ2 < 0, λ4 < 0, δλ2 < 0 that the real-data fit lands on. It
answers: does the on-the-fly bt-grid reconstruction still reproduce a direct
SCETlib run once we sit at the fitted NP tune?

  * Param-model side  = ``SigmaGenModel`` (the datacard-free core that
    ``sigma_gen_at_lambda`` uses), built with ``include_nonsingular=False``
    (resum-only, to match SCETlib ``calculation_piece = sing``) and EVALUATED at
    the postfit λ read from ``--fitresult`` with the fit's tanh_6 numerator forms.
  * SCETlib side       = a direct N3LL point-grid run pickle
    (``{hist, config, meta_data}``), read with ``input_tools.read_scetlib_hist``,
    |Y|-folded, Q-summed, restricted to |Y| ≤ the model's absYVGen max, and
    rebinned qT → ptVGen by CENTER MEMBERSHIP (the point grid is fine — 0.1 GeV in
    qT — and its edges are NOT a subset of the gen edges, so the exact-Simpson
    ``_merge_matrix`` path used for the correction-input pkl does not apply here).

The overlay + ratio + differential-difference figure is produced by
``sigma_gen_at_lambda.make_projection_plot`` (the same 3-panel plotter), summed
over absYVGen (the ptZ = ptVGen projection).

Run in the WRemnants container (binds /work,/ceph,/home; CPU is fine):

    source WRemnants/setup.sh
    python3 studies/btgrid-precision/compare_postfit_sigma_gen.py \\
        --scetlib-pkl <..._points_combined.pkl> \\
        --fitresult   <..._nowall/fitresults_t0.hdf5> \\
        --datacard    <..._realdata/ZMassDilepton.hdf5> \\
        --out ~/public_html/alphaS/260702_2D_l6nu0p01_l60p01_nowall/sigma_gen_parammodel_vs_scetlib.png
"""

import argparse
import sys
import time
import types

import numpy as np


def scetlib_ptv_projection(pkl, ptv_edges, absy_max, q_lo, q_hi, charge=0, tol=1e-6):
    """Read the SCETlib POINT-grid pkl and project onto the model's ptVGen edges.

    This "points" run stores the DIFFERENTIAL cross section d³σ/(dQ dY dqT) sampled
    on a fine grid (unlike the coarse "spectrum" correction-input pkl, which stores
    already-bin-integrated σ that ``_merge_matrix`` can plain-sum). So here we
    integrate: weight each sample by its (clipped) bin widths ΔQ·ΔY·ΔqT, with Q
    clipped to [q_lo, q_hi] and |Y| clipped to ≤ ``absy_max`` so the integration
    window matches the model's exactly (the point Q grid spans 59..121 and Y is
    0.1-spaced, neither aligned to the [60,120]/|Y|≤2.5 edges). qT (physical, ≥0)
    stays fine and is folded into ptVGen by center membership (0.1-GeV source bins
    ≪ the ptVGen bins, so boundary error is negligible). The grid is Y-symmetric to
    machine precision, so summing the signed-Y bins over |Y|≤absy_max = the |Y|-fold.

    Returns (σ per ptVGen bin summed over |Y|≤absy_max and Q∈[q_lo,q_hi],
    σ dropped above the top ptVGen edge, effective |Y| max used).
    """
    import pickle

    with open(pkl, "rb") as f:
        d = pickle.load(f)
    h = d["hist"]
    names = [a.name for a in h.axes]
    v = np.asarray(h.values(), dtype=np.float64)

    if "vars" in names:
        vlabels = list(h.axes["vars"])
        ci = next(
            (vlabels.index(c) for c in ("central", "pdf0", "nominal") if c in vlabels),
            0,
        )
        v = np.take(v, ci, axis=names.index("vars"))
        names = [n for n in names if n != "vars"]
    order = [names.index("Q"), names.index("Y"), names.index("qT")]
    v = np.nan_to_num(np.transpose(v, order), nan=0.0, posinf=0.0, neginf=0.0)

    Qe = np.asarray(h.axes["Q"].edges, dtype=np.float64)
    Ye = np.asarray(h.axes["Y"].edges, dtype=np.float64)
    Te = np.asarray(h.axes["qT"].edges, dtype=np.float64)
    # clipped widths → the integration window matches the model's exactly
    wQ = np.clip(np.minimum(Qe[1:], q_hi) - np.maximum(Qe[:-1], q_lo), 0.0, None)
    wY = np.clip(
        np.minimum(Ye[1:], absy_max) - np.maximum(Ye[:-1], -absy_max), 0.0, None
    )
    wT = np.clip(np.minimum(Te[1:], np.inf) - np.maximum(Te[:-1], 0.0), 0.0, None)

    sig_qt = wT * np.einsum("q,y,qyt->t", wQ, wY, v)  # bin-integrated σ per qT bin
    qt_centers = 0.5 * (Te[:-1] + Te[1:])
    absy_used = min(absy_max, float(Ye[-1]))

    ptv_edges = np.asarray(ptv_edges, dtype=np.float64)
    nb = ptv_edges.size - 1
    idx = np.searchsorted(ptv_edges, qt_centers, side="right") - 1
    inrange = (idx >= 0) & (qt_centers <= ptv_edges[-1] + tol)
    idx = np.clip(idx, 0, nb - 1)
    out = np.zeros(nb, dtype=np.float64)
    np.add.at(out, idx[inrange], sig_qt[inrange])
    dropped = float(sig_qt[~inrange].sum())
    return out, dropped, absy_used


def main(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--scetlib-pkl", required=True, help="SCETlib point-grid run pkl")
    p.add_argument(
        "--fitresult", required=True, help="rabbit fitresults hdf5 (postfit λ + forms)"
    )
    p.add_argument(
        "--datacard",
        default=None,
        help="fit-input hdf5 for the gen grid (ptVGen/absYVGen)",
    )
    p.add_argument(
        "--btgrid",
        default=None,
        help="bt-grid dir (default: the packaged b0_nu=1 grid)",
    )
    p.add_argument("--result", default=None, help="fitresult group suffix")
    p.add_argument("--charge", type=int, default=0, help="0 = Z")
    p.add_argument("--q-lo", type=float, default=60.0)
    p.add_argument("--q-hi", type=float, default=120.0)
    p.add_argument("--ptv-edges", default=None, help="override ptVGen edges 'a,b,...'")
    p.add_argument(
        "--absy-edges", default=None, help="override absYVGen edges 'a,b,...'"
    )
    p.add_argument(
        "--normalize",
        action="store_true",
        help="scale the SCETlib curve to the model σ_gen integral "
        "(SHAPE-only comparison — robust to the points file's coarse "
        "Q sampling of the Breit-Wigner, which makes the absolute "
        "normalization ambiguous at the ~5%% level)",
    )
    p.add_argument("--out", required=True, help="output plot path (.png)")
    args = p.parse_args(argv)

    from wremnants.postprocessing.scetlib_np import lambda_central as lc
    from wremnants.postprocessing.scetlib_np.fitresult_lambdas import _flat_values
    from wremnants.postprocessing.scetlib_np.sigma_gen import (
        SigmaGenModel,
        _default_btgrid_dir,
    )
    from wremnants.postprocessing.scetlib_np.sigma_gen_at_lambda import (
        make_projection_plot,
    )
    from wremnants.postprocessing.scetlib_np.validation.agreement import (
        assemble_tune,
        resolve_base_lambda,
        resolve_gen_axes,
    )

    btgrid = args.btgrid or _default_btgrid_dir()

    # ---- postfit tune from the fitresults: base (card λ_central) + postfit λ
    # overrides, evaluated with the fit's numerator forms (tanh_6 here).
    overrides = _flat_values(args.fitresult, which="postfit", result=args.result)
    fit_eff_form, fit_gnu_form = lc.read_np_models(args.fitresult)
    print(f"[λ] postfit from {args.fitresult}:\n    {overrides}")
    print(f"[λ] fit forms: np_model={fit_eff_form}, np_model_nu={fit_gnu_form}")

    base_args = types.SimpleNamespace(
        meta_from=args.fitresult, theory_corr=None, theory_corr_proc=None
    )
    base = resolve_base_lambda(base_args)
    eff, gnu, explicit = assemble_tune(base, overrides)
    eval_eff = fit_eff_form or base["eff_params"]["np_model"]
    eval_gnu = fit_gnu_form or base["gnu_params"]["np_model_nu"]
    eff["np_model"], gnu["np_model_nu"] = eval_eff, eval_gnu

    gen_args = types.SimpleNamespace(
        ptv_edges=args.ptv_edges,
        absy_edges=args.absy_edges,
        gen_edges_from=None,
        datacard=args.datacard,
    )
    gen_axes = resolve_gen_axes(gen_args)
    absy_max = float(np.asarray(gen_axes[1][1])[-1])
    ptv_edges = np.asarray(gen_axes[0][1], dtype=np.float64)

    print(
        "\n[core] constructing SigmaGenModel (resum-only) at the base tune …",
        flush=True,
    )
    t0 = time.time()
    core = SigmaGenModel(
        btgrid_dir=btgrid,
        lambda_central=base,
        gen_axes=gen_axes,
        Q_lo=args.q_lo,
        Q_hi=args.q_hi,
        include_nonsingular=False,
    )
    print(f"  constructed in {time.time()-t0:.1f}s; gen grid {core.gen_shape}")

    print(f"\n[λ] evaluating resum-only σ_gen at the postfit tune:")
    print(f"  F_eff  : {eff}")
    print(f"  γ_ν^NP : {gnu}")
    t0 = time.time()
    sigma_gen = np.asarray(
        core.sigma_gen(eff, gnu, np_model=eval_eff, np_model_nu=eval_gnu).numpy(),
        dtype=np.float64,
    )
    print(
        f"  σ_gen computed in {time.time()-t0:.1f}s; shape {sigma_gen.shape}; "
        f"Σ = {sigma_gen.sum():.6g}"
    )

    # ---- SCETlib direct run projected onto the same ptVGen edges
    print(f"\n[scetlib] reading {args.scetlib_pkl}")
    s_corr, dropped, absy_used = scetlib_ptv_projection(
        args.scetlib_pkl, ptv_edges, absy_max, args.q_lo, args.q_hi, charge=args.charge
    )
    print(
        f"  projected onto {ptv_edges.size-1} ptVGen bins; summed |Y| ≤ {absy_used:g} "
        f"(target {absy_max:g}); dropped σ above the top ptVGen edge = {dropped:.4g}"
    )

    # ptZ projection of the model (sum over absYVGen), for the ratio printout.
    s_model = sigma_gen.sum(axis=1)
    norm = float(s_model.sum() / s_corr.sum())
    print(f"\n  Σ model / Σ scetlib(points, Q-integrated) = {norm:.5f}")
    label = "SCETlib N3LL resum (points, postfit λ)"
    if args.normalize:
        s_corr = s_corr * norm
        label += f", ×{norm:.4f} (shape-normalized)"
        print(f"  [shape mode] SCETlib scaled to the model integral (×{norm:.5f})")
    with np.printoptions(precision=4, suppress=True, linewidth=140):
        ratio = np.divide(s_model, s_corr, out=np.ones_like(s_model), where=s_corr != 0)
        print(
            f"  per-ptVGen model/scetlib: min {ratio.min():.4f} max {ratio.max():.4f} "
            f"(mean-abs dev from 1: {np.mean(np.abs(ratio-1)):.4f})"
        )
        print(f"  ratio: {ratio}")
        print(f"  model    σ(ptVGen): {s_model}")
        print(f"  scetlib  σ(ptVGen): {s_corr}")

    make_projection_plot(
        sigma_gen,
        core.gen_axes,
        "ptVGen",
        args.out,
        eff,
        gnu,
        s_corr=s_corr,
        corr_label=label,
        args=args,
    )
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
