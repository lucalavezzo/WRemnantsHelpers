#!/usr/bin/env python3
r"""How much of the reco-level residual is the GEN GRID, and what would a finer
one buy?

``validate_variations_reco.py`` split each direction's reco residual into

    r_mod / r_ref = (r_mod / r_A) x (r_A / r_B) x (r_B / r_ref)
                     \__ CALC __/   \__ WGT __/   \__ GRAIN __/

and found that, once the known qT [0,1] nonsingular-cutoff convention is
aligned, GRAIN -- the pure gen-binning granularity term -- is the LARGER of the
two in 30 of 39 directions. GRAIN is the one term that a finer gen grid removes
and that the discrete templates never pay. This script measures how it scales
with the gen grid.

THE CONSTRAINT THAT SHAPES THE WHOLE MEASUREMENT
------------------------------------------------
The gen grid is not ours to choose at analysis time. R = R_raw/N_gen comes out
of the histmaker's ``nominal_prefsr_yieldsUnfolding``, whose ptVGen edges are
``rebin_pt(reco ptll edges)`` = one gen bin per TWO reco bins
(``wremnants/production/unfolding_tools.py``), and whose absYVGen edges are the
positive half of the reco yll edges. So the card's 21 x 10 gen grid is the
FINEST R that exists on disk: refining it needs a histmaker rerun, not a cache
rebuild. A cache on a finer gen grid, on its own, buys exactly nothing --
folding sigma_gen(fine) through a P(b|g) that only knows the coarse bins is
algebraically identical to folding sigma_gen(coarse).

So the trend is measured by COARSENING, which is exact and free: merging gen
bins is a linear map M, and every object the split needs transforms under it
in closed form,

    R_raw_c = R_raw M^T      N_gen_c = M N_gen      sigma_gen_c = M sigma_gen
    P_c     = R_raw_c / N_gen_c

with the model's own sigma_gen evaluated ONCE per direction, on the shipped
cache, and re-folded at every resolution. Every resolution therefore shares one
build and one set of SCETlib calls, so the ~3e-3 cache-rebuild reproducibility
floor (knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md) does not
enter the comparison at all: it is the same numbers folded differently.

The finest point of the scan is the shipped grid; finer than that is an
extrapolation of the fitted power law, and is labelled as such everywhere.

WHAT IS COMPUTED, PER RESOLUTION AND PER DIRECTION
--------------------------------------------------
  r_mod = [P_c (M sigma_gen(p_v))] / [P_c (M sigma_gen(anchor))]
  r_A   = [P_c (rho_c . M sigma_gen(anchor))] / [P_c (M sigma_gen(anchor))]
  r_B   = [P_c (rho_c . N_gen_c)] / [P_c N_gen_c]  ==  [R_raw_c rho_c] / [R_raw 1]
  r_ref = the histmaker's own per-event reweighted reco variation

with rho_c the correction file's response BIN-AVERAGED on the coarse grid
(numerator and denominator merged separately, then divided -- never a mean of
ratios). GRAIN = r_B/r_ref is free of the model and of the qT [0,1] convention:
it contains no SCETlib number at all.

A LINEARISED FISHER PROXY FOR THE FIT
-------------------------------------
A closure number nobody can see in the fit is worth little, so each resolution
also gets an Asimov Fisher matrix built from the SAME reco responses,

    F = A^T diag(n) A + Prior,     n(b) = the histmaker's expected yield,

A's columns being d ln N / d theta for alpha_s (per unit alpha_s) and for each
basis nuisance (per unit theta, unit Gaussian prior). That gives
sigma(alpha_s)(resolution) and, projecting a residual d(b) onto the same basis,
the alpha_s BIAS that residual would cause. It is a proxy -- the real card
floats 3731 nuisances -- and is only ever compared to itself across
resolutions.

Usage (in the container, see incontainer.sh):

    ./grain_vs_grid.py --datacard <card.hdf5> --histmaker <hm.hdf5> \
        --cache <cache.npz> --conf <cache.conf> --npz <out.npz>
    ./grain_vs_grid.py --from-npz <out.npz> -o <plotdir> --csv <out.csv>
"""

import argparse
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
for _p in (_WREM, os.path.join(_WREM, "scripts", "rabbit", "scetlib_ad"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CORR_MAIN = (
    "nominal_ptll_yll_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_"
    "CT18Z_N3p0LL_N2LO_Corr"
)
CORR_AS = CORR_MAIN.replace("_N2LO_Corr", "_N2LO_pdfas_Corr")
SIGNAL_SAMPLE = "Zmumu_2016PostVFP"

# The nuisance basis the alpha_s projection profiles over. Same list as
# lowqt_nonsingular_attribution.py so the numbers stay comparable.
BASIS = ["kappaFO2.-kappaf0.5", "kappaFO0.5-kappaf2.", "mufup", "mufdown",
         "lambda21.0", "lambda41.0", "delta_lambda20.02", "lambda2_nu0.25",
         "gamma_cusp1.", "gamma_mu_q1.", "gamma_nu1.", "s1.", "h_qqV1.",
         "b_qqV0.5", "b_qqbarV0.5", "b_qqS0.5", "b_qg0.5"]
AS_UP = "pdfCT18ZNNLO_as_0120"
AS_STEP = 0.002


# =========================================================== compute stage ==
def compute(args):
    """Everything that needs SCETlib or the 7.5 GB histmaker, once, to an npz."""
    import validate_variations as VV
    from rabbit.inputdata import FitInputData

    from wremnants.postprocessing.scetlib_ad.param_model import SCETlibADParamModel
    from wremnants.postprocessing.scetlib_ad.response import R_info_from_auxiliary

    indata = FitInputData(args.datacard)
    model = SCETlibADParamModel(
        indata, cache=args.cache, conf=args.conf, gen_level=0,
        threads=args.threads, fit_params="lambda2", poi_params="lambda2",
        jitCompile="off",
    )
    reco_axes = model._fit_axes(indata)
    P = np.asarray(model.R.numpy(), dtype=np.float64)             # (n_reco, n_gen)
    sg0 = np.asarray(model.sigma_gen_central_flat.numpy(), float)  # (n_gen,)
    core, names = model.core, list(model.core.param_names)
    anchor = np.asarray(core.anchor, float)

    (qt_name, Te), (y_name, Ye) = model.gen_axes
    if not (qt_name.startswith("ptV") and y_name.startswith("absY")):
        raise SystemExit(f"expected (ptVGen, absYVGen), got ({qt_name}, {y_name})")
    nT, nY = Te.size - 1, Ye.size - 1
    reco_shape = model.reco_shape
    print(f"gen grid : {nT} x {nY} = {sg0.size};  reco {reco_shape}", flush=True)

    N_gen = np.asarray(R_info_from_auxiliary(indata)["N_gen"], float).reshape(-1)
    # R_raw is what the histmaker filled; P is R_raw/N_gen with empty columns
    # left at zero, so multiplying back is exact wherever N_gen > 0 and 0 where
    # it is not (R_raw is 0 there too).
    R_raw = P * N_gen[np.newaxis, :]

    # ---- the histmaker's own reco variations (the per-event reference) -----
    import validate_variations_reco as VVR
    per_file = {}
    for hname in args.corr:
        h = VVR.load_hist(args.histmaker, args.sample, hname)
        vals, labels = VVR.reco_var_tensor(h, reco_axes)
        per_file[hname] = (vals, labels, VV.central_label(labels))
        print(f"reference: {hname} ({len(labels)} vars)", flush=True)

    # ---- the correction file on its NATIVE gen grid ------------------------
    corr_native = {}
    for pkl in VVR._corr_pickles():
        h = VV.load_corr(pkl)
        ax = {a.name: a for a in h.axes}
        labels = [str(x) for x in ax["vars"]]
        vals = np.asarray(h.values(flow=False))
        dims = [a.name for a in h.axes]
        vals = np.squeeze(vals, axis=(dims.index("Q"), dims.index("charge")))
        order = [d for d in dims if d not in ("Q", "charge")]
        vals = np.moveaxis(
            vals,
            [order.index("absY"), order.index("qT"), order.index("vars")],
            [0, 1, 2],
        )
        corr_native[pkl] = (labels, VV.central_label(labels), vals,
                            np.asarray(ax["absY"].edges, float),
                            np.asarray(ax["qT"].edges, float))
        print(f"gen reference: {os.path.basename(pkl)} "
              f"{vals.shape} absY x qT x vars", flush=True)

    def native_for(label):
        for _p, (labels, cen, vals, Yn, Tn) in corr_native.items():
            if label in labels:
                return (vals[:, :, labels.index(label)], vals[:, :, labels.index(cen)],
                        Yn, Tn)
        return (None, None, None, None)

    # ---- walk the directions ----------------------------------------------
    out_labels, out_sgv, out_num, out_den = [], [], [], []
    out_ref, ref_cen_store = [], {}
    Yn_ref = Tn_ref = None
    for hname in args.corr:
        vals, labels, cen = per_file[hname]
        ref_cen = vals[..., labels.index(cen)]
        ref_cen_store[hname] = ref_cen
        for L in labels:
            if L == cen:
                continue
            ov = VV.variation_for(L)
            if ov is None:
                continue
            p = anchor.copy()
            skip = False
            for k, v in ov.items():
                if k not in names:
                    skip = True
                    break
                p[names.index(k)] = v
            if skip:
                print(f"  {L}: cache lacks {list(ov)}, skipped")
                continue
            num, den, Yn, Tn = native_for(L)
            if num is None:
                print(f"  {L}: no gen reference, skipped")
                continue
            if Yn_ref is None:
                Yn_ref, Tn_ref = Yn, Tn
            elif not (np.allclose(Yn, Yn_ref) and np.allclose(Tn, Tn_ref)):
                raise SystemExit("correction files disagree on the native gen grid")
            sgv = model._fold(np.asarray(core.values_and_jacobian(p)[0], float))
            out_labels.append(L)
            out_sgv.append(sgv)
            out_num.append(num)
            out_den.append(den)
            out_ref.append(vals[..., labels.index(L)].reshape(-1))
            print(f"  {L:<34} done", flush=True)

    # the plain nominal, for the identity check quoted in the README
    hn = VVR.load_hist(args.histmaker, "Zmumu_2016PostVFP", "nominal")
    nom_names = [a.name for a in hn.axes]
    nv = np.asarray(hn.values(flow=False), float)
    keep_idx = [nom_names.index(n) for n, _ in reco_axes]
    drop = tuple(i for i in range(nv.ndim) if i not in keep_idx)
    if drop:
        nv = nv.sum(axis=drop)
    rem = [n for n in nom_names if nom_names.index(n) in keep_idx]
    nv = np.transpose(nv, [rem.index(n) for n, _ in reco_axes])
    nv = nv[: reco_shape[0], : reco_shape[1]]

    np.savez_compressed(
        args.npz,
        labels=np.array(out_labels),
        sgv=np.array(out_sgv),                    # (K, n_gen)
        sg0=sg0,
        corr_num=np.array(out_num),               # (K, nYnat, nTnat)
        corr_den=np.array(out_den),
        ref_var=np.array(out_ref),                # (K, n_reco)
        ref_cen=np.concatenate(
            [ref_cen_store[h].reshape(1, -1) for h in args.corr], axis=0),
        ref_cen_files=np.array(list(args.corr)),
        ref_cen_of=np.array([
            [i for i, h in enumerate(args.corr)
             if L in per_file[h][1]][0] for L in out_labels]),
        R_raw=R_raw, N_gen=N_gen, nominal=nv.reshape(-1),
        Te=Te, Ye=Ye, Tn=Tn_ref, Yn=Yn_ref,
        reco_edges_0=np.asarray(reco_axes[0][1], float),
        reco_edges_1=np.asarray(reco_axes[1][1], float),
        reco_shape=np.array(reco_shape),
        cache=np.array(os.path.abspath(args.cache)),
        datacard=np.array(os.path.abspath(args.datacard)),
        histmaker=np.array(os.path.abspath(args.histmaker)),
    )
    print(f"\nwrote {args.npz}  ({len(out_labels)} directions)")


# =========================================================== analyse stage ==
def merge_matrix(fine, coarse, name, tol=1e-9):
    """(n_coarse, n_fine) 0/1 matrix summing fine bins into coarse ones."""
    fine, coarse = np.asarray(fine, float), np.asarray(coarse, float)
    M = np.zeros((coarse.size - 1, fine.size - 1))
    for k in range(coarse.size - 1):
        lo, hi = coarse[k], coarse[k + 1]
        idx = [i for i in range(fine.size - 1)
               if fine[i] >= lo - tol and fine[i + 1] <= hi + tol]
        if not idx or abs(fine[idx[0]] - lo) > tol or abs(fine[idx[-1] + 1] - hi) > tol:
            raise SystemExit(f"{name}: [{lo}, {hi}] is not a union of fine bins")
        M[k, idx] = 1.0
    return M


def coarse_qt_edges(Te, k, n_inrange):
    """Merge the first ``n_inrange`` qT bins in blocks of k; keep the trailing
    overflow bin ([44, 100], the histmaker's ptVGen overflow) untouched -- it is
    a RANGE artefact, not a granularity one, and merging it would mix the two."""
    if n_inrange % k:
        raise SystemExit(f"qT: {n_inrange} in-range bins not divisible by {k}")
    idx = list(range(0, n_inrange, k)) + list(range(n_inrange, Te.size))
    return Te[idx]


def coarse_y_edges(Ye, m):
    n = Ye.size - 1
    if n % m:
        raise SystemExit(f"|Y|: {n} bins not divisible by {m}")
    return Ye[list(range(0, n, m)) + [n]]


def summarize(dev, w, mask):
    d = np.asarray(dev, float)
    good = np.isfinite(d) & mask
    if not good.any():
        return np.nan, np.nan
    return float(d[good].max()), float(np.average(d[good], weights=np.asarray(w)[good]))


class Grid:
    """One coarsening of the card's gen grid, with everything it implies."""

    def __init__(self, z, k, m):
        Te, Ye = z["Te"], z["Ye"]
        self.k, self.m = k, m
        n_over = 1                      # the trailing [44, 100] overflow bin
        self.Tc = coarse_qt_edges(Te, k, Te.size - 1 - n_over)
        self.Yc = coarse_y_edges(Ye, m)
        self.nTc, self.nYc = self.Tc.size - 1, self.Yc.size - 1
        MQ = merge_matrix(Te, self.Tc, "qT")
        MY = merge_matrix(Ye, self.Yc, "absY")
        self.M = np.kron(MQ, MY)                       # gen flattened qT-major
        self.MQn = merge_matrix(z["Tn"], self.Tc, "qT native")
        self.MYn = merge_matrix(z["Yn"], self.Yc, "absY native")
        self.N_c = self.M @ z["N_gen"]
        self.R_raw_c = z["R_raw"] @ self.M.T
        safe = np.where(self.N_c > 0, self.N_c, 1.0)
        self.P_c = self.R_raw_c / safe[np.newaxis, :]
        self.den_reco = self.R_raw_c.sum(axis=1)       # == R_raw @ 1, k-independent
        self.sg0_c = self.M @ z["sg0"]
        self.sr0 = self.P_c @ self.sg0_c

    @property
    def nbins(self):
        return self.nTc * self.nYc

    def rho(self, num, den):
        """Bin-averaged correction response on this grid, flattened qT-major."""
        n = self.MYn @ num @ self.MQn.T
        d = self.MYn @ den @ self.MQn.T
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.where(d != 0, n / d, np.nan)
        return r.T.reshape(-1)

    def fold(self, sg):
        return (self.P_c @ (self.M @ sg)) / self.sr0

    def r_A(self, rho):
        return (self.P_c @ (rho * self.sg0_c)) / self.sr0

    def r_B(self, rho):
        return (self.R_raw_c @ rho) / self.den_reco


def fisher(A, n, i_as):
    """(sigma_as, solve(d)) for the Asimov Fisher matrix of a response set.

    A holds d ln N / d theta per column; column ``i_as`` is alpha_s per unit
    alpha_s and carries no prior, every other column is a unit-Gaussian
    nuisance. ``solve(d)`` returns the alpha_s shift a residual d(b) buys.
    """
    F = A.T @ (n[:, None] * A)
    P = np.eye(A.shape[1])
    P[i_as, i_as] = 0.0
    Finv = np.linalg.inv(F + P)
    sig = float(np.sqrt(Finv[i_as, i_as]))

    def solve(d):
        rhs = A.T @ (n * np.nan_to_num(d))
        return float((Finv @ rhs)[i_as])

    return sig, solve


def analyse(z, ks, ms, align_bin0=True, out=print):
    labels = [str(x) for x in z["labels"]]
    reco_shape = tuple(int(v) for v in z["reco_shape"])
    ref_cen_all = z["ref_cen"]
    ref_of = z["ref_cen_of"]
    Te, Ye = z["Te"], z["Ye"]
    nT, nY = Te.size - 1, Ye.size - 1
    n_ptll = reco_shape[0]
    top_bin = np.ones(reco_shape, bool)
    top_bin[-1, :] = False                      # the gen-overflow-fed reco bin
    top_bin = top_bin.reshape(-1)

    # The qT[0,1] alignment is applied ONCE, on the card's fine grid, before any
    # merging, so it means the same thing at every resolution.
    fine_rho = {}
    G1 = Grid(z, 1, 1)
    for i, L in enumerate(labels):
        fine_rho[L] = G1.rho(z["corr_num"][i], z["corr_den"][i])

    rows = []
    for k in ks:
        for m in ms:
            G = Grid(z, k, m)
            r_mod, r_A, r_B, r_ref, wts = {}, {}, {}, {}, {}
            for i, L in enumerate(labels):
                sgv = z["sgv"][i]
                if align_bin0:
                    sgv = sgv.copy()
                    sgv.reshape(nT, nY)[0, :] = (
                        fine_rho[L].reshape(nT, nY)[0, :]
                        * z["sg0"].reshape(nT, nY)[0, :])
                rho = np.where(np.isfinite(G.rho(z["corr_num"][i], z["corr_den"][i])),
                               G.rho(z["corr_num"][i], z["corr_den"][i]), 1.0)
                cen = ref_cen_all[ref_of[i]]
                with np.errstate(divide="ignore", invalid="ignore"):
                    rr = np.where(cen > 0, z["ref_var"][i] / cen, np.nan)
                r_mod[L], r_A[L], r_B[L], r_ref[L], wts[L] = (
                    G.fold(sgv), G.r_A(rho), G.r_B(rho), rr, cen)

            # ---- the Fisher proxy on THIS grid ----
            basis = [L for L in BASIS if L in labels]
            n_evt = ref_cen_all[0]
            cols = [(r_mod[AS_UP] - 1.0) / AS_STEP] + [r_mod[L] - 1.0 for L in basis]
            A = np.stack(cols, axis=1)
            sig_as, _ = fisher(A, n_evt, 0)

            for i, L in enumerate(labels):
                cen = wts[L]
                good = np.isfinite(r_ref[L]) & (r_ref[L] != 0) & (cen > 0)
                res = dict(k=k, m=m, nT=G.nTc, nY=G.nYc, ngen=G.nbins,
                           direction=L, sigma_as=sig_as)
                for tag, ratio in (("total", r_mod[L] / r_ref[L]),
                                   ("calc", r_mod[L] / r_A[L]),
                                   ("wgt", r_A[L] / r_B[L]),
                                   ("grain", r_B[L] / r_ref[L])):
                    mx, wm = summarize(np.abs(ratio - 1.0), cen, good)
                    res[f"{tag}_max"], res[f"{tag}_wmean"] = mx, wm
                    mx2, wm2 = summarize(np.abs(ratio - 1.0), cen, good & top_bin)
                    res[f"{tag}_max_notop"], res[f"{tag}_wmean_notop"] = mx2, wm2
                _, resp = summarize(np.abs(r_ref[L] - 1.0), cen, good)
                res["response_wmean"] = resp

                # alpha_s equivalent of this direction's residual, profiling the
                # OTHER basis nuisances (never the direction itself).
                keep = [b for b in basis if b != L]
                cols = ([(r_mod[AS_UP] - 1.0) / AS_STEP]
                        + [r_mod[b] - 1.0 for b in keep])
                Ai = np.stack(cols, axis=1)
                _, solve = fisher(Ai, n_evt, 0)
                res["eq_as_total"] = solve(
                    np.where(good, r_mod[L] / r_ref[L] - 1.0, 0.0))
                res["eq_as_grain"] = solve(
                    np.where(good, r_B[L] / r_ref[L] - 1.0, 0.0))
                res["eq_as_calc"] = solve(
                    np.where(good, r_mod[L] / r_A[L] - 1.0, 0.0))
                rows.append(res)
            out(f"grid k={k} m={m}: {G.nTc} x {G.nYc} = {G.nbins} gen bins, "
                f"sigma(as)_Fisher = {sig_as:.4e}", flush=True)
    return rows


def _fit_power(x, y):
    """y = C x^p by least squares in logs; returns (C, p)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
    if ok.sum() < 2:
        return np.nan, np.nan
    p, lc = np.polyfit(np.log(x[ok]), np.log(y[ok]), 1)
    return float(np.exp(lc)), float(p)


# ------------------------------------------------------------------ main ---
def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datacard")
    ap.add_argument("--histmaker")
    ap.add_argument("--cache")
    ap.add_argument("--conf")
    ap.add_argument("--corr", nargs="+", default=[CORR_MAIN, CORR_AS])
    ap.add_argument("--sample", default=SIGNAL_SAMPLE)
    ap.add_argument("--threads", type=int, default=48)
    ap.add_argument("--npz", required=True)
    ap.add_argument("--from-npz", action="store_true")
    ap.add_argument("--csv")
    ap.add_argument("--no-align-bin0", action="store_true")
    ap.add_argument("--kk", type=int, nargs="+", default=[1, 2, 4, 5, 10, 20])
    ap.add_argument("--mm", type=int, nargs="+", default=[1, 2, 5, 10])
    args = ap.parse_args()

    if not args.from_npz:
        compute(args)
        return

    z = np.load(args.npz, allow_pickle=False)
    rows = analyse(z, args.kk, args.mm, align_bin0=not args.no_align_bin0)
    if args.csv:
        import csv
        with open(args.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"table -> {args.csv}")


if __name__ == "__main__":
    main()
