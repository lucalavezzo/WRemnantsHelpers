#!/usr/bin/env python3
r"""GRAIN measured on a genuinely FINER gen grid, from a dedicated histmaker.

``grain_vs_grid.py`` can only COARSEN: the shipped card's 21 x 10 gen grid is the
finest response matrix that exists on disk, because the histmaker builds
``ptVGen`` as ``rebin_pt(reco ptll edges)`` -- one gen bin per two reco bins.
``finegen_histmaker.py`` reruns the histmaker with that map removed, giving
40 gen qT bins (the reco ptll edges themselves, with [44, 100] resolved instead
of being an overflow) and 20 gen |Y| bins (each shipped bin split at its
midpoint). This script reads that output and measures GRAIN on it.

GRAIN needs NO model and NO SCETlib cache:

    GRAIN(b) = [ sum_g R_raw(b, g) rho_bar(g) / sum_g R_raw(b, g) ] / r_ref(b)

with rho_bar the correction file's response bin-averaged on the gen grid
(numerator and denominator merged separately) and r_ref the histmaker's own
per-event reweighted reco variation. Both come out of the same events, so the
comparison across gen grids is internal to ONE histmaker run and one set of
weights: nothing here can be moved by a cache rebuild, by SCETlib, or by the
qT [0, 1] nonsingular-cutoff convention.

Because the fine run's own coarsening back to 21 x 10 reproduces the shipped
grid EXACTLY (the shipped edges are a sub-union of the fine ones by
construction), the run carries its own control: the (20 in-range + overflow) x 10
row of the output must reproduce the number measured on the production card.

Usage (in the container, see incontainer.sh):

    ./grain_finegrid.py --histmaker <finegen.hdf5> --card-npz <grain_inputs.npz> \
        --csv <out.csv> [-o <plotdir>]
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

from grain_vs_grid import BASIS, fisher, merge_matrix  # noqa: E402

CORR_MAIN = (
    "nominal_ptll_yll_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_"
    "CT18Z_N3p0LL_N2LO_Corr"
)
CORR_AS = CORR_MAIN.replace("_N2LO_Corr", "_N2LO_pdfas_Corr")
SAMPLE = "Zmumu_2016PostVFP"
JOINT = "nominal_prefsr_yieldsUnfolding"
GENTOT = "prefsr"


def _get(out, name):
    p = out[name]
    return p.get() if hasattr(p, "get") else p


def _with_overflow(h, axname):
    """values with ``axname``'s overflow kept as a trailing in-range bin."""
    full = h.values(flow=True)
    idx = []
    for ax in h.axes:
        uf = 1 if ax.traits.underflow else 0
        if ax.name == axname:
            idx.append(slice(uf, uf + ax.size + 1))
        else:
            idx.append(slice(uf, uf + ax.size))
    return full[tuple(idx)]


def load_fine(path, corr_names, reco_pt_hi=44.0):
    import h5py

    from wums import ioutils as wums_io

    with h5py.File(path, "r") as f:
        out = wums_io.pickle_load_h5py(f[SAMPLE])["output"]
        hj = _get(out, JOINT)
        hg = _get(out, GENTOT)
        refs = {n: _get(out, n) for n in corr_names}
        hn = _get(out, "nominal_ptll_yll") if "nominal_ptll_yll" in out else None

    hs = hj[{"acceptance": True}].project("ptll", "yll", "ptVGen", "absYVGen")
    R = _with_overflow(hs, "ptVGen").astype(np.float64)
    Ng = _with_overflow(hg.project("ptVGen", "absYVGen"), "ptVGen").astype(np.float64)
    pt = np.asarray(hs.axes["ptll"].edges, float)
    yl = np.asarray(hs.axes["yll"].edges, float)
    Te = np.asarray(hs.axes["ptVGen"].edges, float)
    Ye = np.asarray(hs.axes["absYVGen"].edges, float)
    # crop the reco ptll axis to the fit's 0-44
    npt = int(np.searchsorted(pt, reco_pt_hi + 1e-9))
    R = R[:npt]
    pt = pt[: npt + 1]

    var = {}
    for n, h in refs.items():
        names = [a.name for a in h.axes]
        v = np.asarray(h.values(flow=False), float)
        order = [names.index("ptll"), names.index("yll"), names.index("vars")]
        v = np.transpose(v, order)[:npt]
        var[n] = (v, [str(x) for x in h.axes["vars"]])
    nom = None
    if hn is not None:
        nn = [a.name for a in hn.axes]
        nv = np.asarray(hn.values(flow=False), float)
        nom = np.transpose(nv, [nn.index("ptll"), nn.index("yll")])[:npt]
    return dict(R=R, N_gen=Ng, pt=pt, yl=yl, Te=Te, Ye=Ye, var=var, nominal=nom)


def native_corr():
    """The correction pickles on their own (absY, qT) grid."""
    import validate_variations as VV
    import validate_variations_reco as VVR

    out = {}
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
        out[pkl] = (labels, VV.central_label(labels), vals,
                    np.asarray(ax["absY"].edges, float),
                    np.asarray(ax["qT"].edges, float))
    return out


CARD_QT = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28,
           33, 44]
CARD_Y = [0, 0.15, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.8, 2.5]


def merge_blocks(edges, k, tol=1e-9):
    """Merge ``edges`` in blocks of k bins; None if it does not divide."""
    n = len(edges) - 1
    if n % k:
        return None
    return np.asarray([edges[i] for i in range(0, n, k)] + [edges[-1]], float)


def qt_ladder(Te_fine, tail_at=44.0):
    """The resolution ladder in gen qT, passing exactly through the card's grid.

    Te_fine are the fine histmaker's ptVGen edges [0, 1, 1.5, ..., 44, 100]; the
    resolved region is everything below ``tail_at`` and everything above it is
    one tail group, so the [44, 100]-plus-overflow RANGE artefact is held fixed
    while the granularity moves. The card's edges are a strict sub-union of the
    fine ones by construction (rebin_pt keeps every second reco edge), which is
    what makes the card's own row of this table an exact control.
    """
    i44 = int(np.argmin(np.abs(Te_fine - tail_at)))
    fine = np.asarray(Te_fine[: i44 + 1], float)
    out = [("fine", fine)]
    for k in (1, 2, 4, 5, 10, 20):
        e = merge_blocks(CARD_QT, k)
        if e is not None:
            out.append((f"card/{k}" if k > 1 else "card", e))
    return i44, out


def qt_merges(Te_fine, qt_edges, Tn, i44, tail="card"):
    """(M_R, M_rho) for one qT resolution.

    ``M_R`` (n_coarse, n_gen_columns) merges the histmaker's gen qT columns --
    the 39 resolved ones below 44 plus the [44, 100] bin plus the > 100 overflow.
    ``M_rho`` (n_coarse, n_native) merges the correction file's own qT axis the
    same way. They differ in exactly one place, and that place is the point:
    the correction file stops at 100 GeV, so whatever sits above 100 in the MC
    can only ever be given the (44, 100] response. ``tail='card'`` reproduces the
    shipped treatment (one trailing bin holding every qT > 44); ``tail='split'``
    resolves [44, 100] and leaves > 100 on its own.
    """
    res = merge_matrix(Te_fine[: i44 + 1], qt_edges, "qT resolved")
    nres, ncol = res.shape                      # ncol = i44 resolved columns
    ntot = i44 + 2                              # + [44, 100] + the > 100 overflow
    resn = merge_matrix(Tn, qt_edges, "qT native")
    tailn = merge_matrix(Tn, np.array([qt_edges[-1], 100.0]), "qT tail")
    if tail == "card":
        M_R = np.zeros((nres + 1, ntot))
        M_R[:nres, :ncol] = res
        M_R[nres, ncol:] = 1.0
        M_rho = np.vstack([resn, tailn])
    else:
        M_R = np.zeros((nres + 2, ntot))
        M_R[:nres, :ncol] = res
        M_R[nres, ncol] = 1.0
        M_R[nres + 1, ncol + 1] = 1.0
        M_rho = np.vstack([resn, tailn, tailn])
    return M_R, M_rho


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--histmaker", required=True)
    ap.add_argument("--corr", nargs="+", default=[CORR_MAIN, CORR_AS])
    ap.add_argument("--csv", required=True)
    ap.add_argument("--tail", default="card", choices=["card", "split"])
    args = ap.parse_args()

    import validate_variations as VV

    D = load_fine(args.histmaker, args.corr)
    Te, Ye = D["Te"], D["Ye"]
    R, Ng = D["R"], D["N_gen"]
    npt, nyl, nT, nY = R.shape
    i44 = int(np.argmin(np.abs(Te - 44.0)))
    print(f"fine gen grid : ptVGen {nT} columns "
          f"({i44} resolved below 44, [44,100], >100), absYVGen {nY}")
    print(f"reco          : ptll {npt} x yll {nyl}")
    print(f"N_gen total {Ng.sum():.6g};  [44,100] {Ng[-2].sum()/Ng.sum():.4f}; "
          f">100 {Ng[-1].sum()/Ng.sum():.4f}; qT>44 total "
          f"{(Ng[-2].sum()+Ng[-1].sum())/Ng.sum():.4f}")
    if D["nominal"] is not None:
        print(f"identity: (R summed over gen) / nominal_ptll_yll - 1 = "
              f"{R.sum() / D['nominal'].sum() - 1:.3e}  (the gen |Y|>2.5 leak)")

    nat = native_corr()

    def native_for(L):
        for _p, (labels, cen, vals, Yn, Tn) in nat.items():
            if L in labels:
                return (vals[:, :, labels.index(L)],
                        vals[:, :, labels.index(cen)], Yn, Tn)
        return (None, None, None, None)

    Rf = R.reshape(npt * nyl, nT * nY)
    den_reco = Rf.sum(axis=1)

    refs = {}
    for hname in args.corr:
        v, labels = D["var"][hname]
        cen = VV.central_label(labels)
        c = v[..., labels.index(cen)].reshape(-1)
        for L in labels:
            if L == cen or VV.variation_for(L) is None:
                continue
            with np.errstate(divide="ignore", invalid="ignore"):
                refs[L] = (np.where(c > 0,
                                    v[..., labels.index(L)].reshape(-1) / c,
                                    np.nan), c)
    print(f"{len(refs)} directions with a mapped variation")

    _, Tn0 = None, None
    for _p, (_l, _c, _v, _Yn, _Tn) in nat.items():
        Tn0, Yn0 = _Tn, _Yn
        break

    qt_grids = [("fine", np.asarray(Te[: i44 + 1], float))]
    for k in (1, 2, 4, 5, 10, 20):
        e = merge_blocks(CARD_QT, k)
        if e is not None:
            qt_grids.append((("card" if k == 1 else f"card/{k}"), e))
    # |Y| ladder. It CANNOT go finer than the card's own 10 bins, and that is a
    # fact about the reference, not a limitation of this run: the theory
    # correction is applied as a BIN LOOKUP on the correction file's own grid
    # (correctionsTensor_helper.makeCorrectionsTensor -- "returns what is in the
    # bin of the histogram", no interpolation), whose absY edges are
    # [0, .15, .3, .5, .7, .9, 1.1, 1.3, 1.5, 1.8, 2.0, 2.5]. The card's gen |Y|
    # edges are exactly those minus the 2.0 one, so a |Y| grid that is not a
    # union of correction cells has no bin-averaged response to compare against.
    # The midpoint-refined 20-bin axis this run carries is such a grid, so the
    # ladder starts at the card's.
    y_grids = []
    for k in (2, 4, 10, 20):
        e = merge_blocks(list(Ye), k)
        if e is not None:
            y_grids.append((("card" if k == 2 else f"card/{k // 2}"), e))

    top = np.ones((npt, nyl), bool)
    top[-1, :] = False
    top = top.reshape(-1)

    # ---- the alpha_s projection, built from the REFERENCE responses ---------
    # A's columns are the histmaker's own per-event responses, so the design
    # matrix is identical at every resolution and model-free; the only thing
    # that moves between rows of the table is the residual being projected.
    n_evt = None
    for hname in args.corr:
        v, labels = D["var"][hname]
        n_evt = v[..., labels.index(VV.central_label(labels))].reshape(-1)
        break
    basis = [L for L in BASIS if L in refs]
    AS_UP, AS_STEP = "pdfCT18ZNNLO_as_0120", 0.002
    have_as = AS_UP in refs

    def as_solver(exclude=None):
        cols = [np.nan_to_num(refs[AS_UP][0] - 1.0) / AS_STEP]
        cols += [np.nan_to_num(refs[b][0] - 1.0) for b in basis if b != exclude]
        return fisher(np.stack(cols, axis=1), n_evt, 0)

    sig_as = as_solver()[0] if have_as else np.nan
    print(f"Fisher sigma(alpha_s) from the reference responses: {sig_as:.4e}")

    prof_store = {}
    rows = []
    for qname, qe in qt_grids:
        M_R, M_rho = qt_merges(Te, qe, Tn0, i44, tail=args.tail)
        for yname, ye in y_grids:
            MY = merge_matrix(Ye, ye, "absY")
            MYn = merge_matrix(Yn0, ye, "absY native")
            M = np.kron(M_R, MY)
            Rc = Rf @ M.T
            nq, ny = M_R.shape[0], MY.shape[0]
            for L, (rr, w) in refs.items():
                num, den, _Yn, _Tn = native_for(L)
                if num is None:
                    continue
                n_c = MYn @ num @ M_rho.T
                d_c = MYn @ den @ M_rho.T
                with np.errstate(divide="ignore", invalid="ignore"):
                    rho = np.where(d_c != 0, n_c / d_c, 1.0).T.reshape(-1)
                rB = (Rc @ rho) / den_reco
                good = np.isfinite(rr) & (rr != 0) & (w > 0)
                dev = np.abs(rB / rr - 1.0)
                eq = np.nan
                if have_as:
                    eq = as_solver(exclude=L)[1](
                        np.where(good, rB / rr - 1.0, 0.0))
                if yname == "card":
                    d2 = (rB / rr - 1.0).reshape(npt, nyl)
                    wc = np.nan_to_num(w).reshape(npt, nyl)
                    prof_store.setdefault(qname, {})[L] = (
                        np.nansum(np.abs(d2) * wc, axis=1) / wc.sum(axis=1))
                rows.append(dict(
                    qgrid=qname, ygrid=yname, nT=nq, nY=ny, ngen=nq * ny,
                    direction=L, eq_as_grain=eq, sigma_as=sig_as,
                    grain_max=float(dev[good].max()),
                    grain_wmean=float(np.average(dev[good], weights=w[good])),
                    grain_max_notop=float(dev[good & top].max()),
                    grain_wmean_notop=float(
                        np.average(dev[good & top], weights=w[good & top])),
                    response_wmean=float(
                        np.average(np.abs(rr[good] - 1.0), weights=w[good])),
                ))
            sub = [r for r in rows if r["qgrid"] == qname and r["ygrid"] == yname]
            g = np.array([r["grain_wmean"] for r in sub])
            gm = np.array([r["grain_max"] for r in sub])
            print(f"qT {qname:<8} |Y| {yname:<8} {nq:3d} x {ny:3d} = {nq*ny:4d} : "
                  f"wmean med {np.median(g):.3e} worst {g.max():.3e} | "
                  f"max med {np.median(gm):.3e} worst {gm.max():.3e}", flush=True)

    # ---- where in reco ptll the residual sits, finest vs the card's grid ----
    pt = D["pt"]
    for qname in ("fine", "card"):
        if qname not in prof_store:
            continue
        P = np.array([prof_store[qname][L] for L in sorted(prof_store[qname])])
        med = np.median(P, axis=0)
        print(f"\nmedian |GRAIN| per reco ptll bin, gen qT grid = {qname} "
              f"(x 1e4):")
        print("   " + " ".join(f"{pt[i]:g}:{med[i]*1e4:.2f}"
                               for i in range(len(med))))
    if "fine" in prof_store and "card" in prof_store:
        Pf = np.array([prof_store["fine"][L] for L in sorted(prof_store["fine"])])
        Pc = np.array([prof_store["card"][L] for L in sorted(prof_store["card"])])
        mf, mc = np.median(Pf, axis=0), np.median(Pc, axis=0)
        for lo, hi, tag in ((1.0, 12.0, "1-12 GeV (fine grid == correction grid)"),
                            (12.0, 20.0, "12-20 GeV"),
                            (20.0, 44.0, "20-44 GeV"),
                            (0.0, 1.0, "0-1 GeV (fine grid still coarser)")):
            sel = (pt[:-1] >= lo - 1e-9) & (pt[:-1] < hi - 1e-9)
            if sel.any():
                print(f"   {tag:<44} card {np.median(mc[sel]):.2e} -> "
                      f"fine {np.median(mf[sel]):.2e}  "
                      f"({np.median(mc[sel]) / max(np.median(mf[sel]), 1e-30):.1f}x)")

    import csv
    with open(args.csv, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader(); wr.writerows(rows)
    print(f"table -> {args.csv}")


if __name__ == "__main__":
    main()
