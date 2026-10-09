#!/usr/bin/env python3
"""Read the lattice arms against the cold reference arms on card A.

Everything is computed from the fitresults and from the external term READ BACK
OUT OF THE LATTICE CARD (nothing about the constraint is retyped here).

* convergence: nllvalreduced, edmval, iterations (len(epoch_loss)), negative
  eigenvalues and condition number of the postfit covariance.
* loss decomposition  fun = ln(data) + lc(priors) + lpen(wall) + lext(lattice),
  each from the arm's own postfit theta:
    lc   = 0.5 * sum over constrained params of ((theta - mean)/sigma)^2 for the
           model (param_priors meta: mask/sigmas/means) + 0.5 * sum cw theta^2
           for the card nuisances (indata.constraintweights)
    lpen = exp(2 tau) * sum_c relu(bound_c - value_c)^2   (walled arms only)
    lext = 0.5 (t - mu)^T H (t - mu)                      (lattice arms only)
  so Delta chi2_data = 2 * (ln_arm - ln_ref) compares the DATA term alone.
* NP lambdas in physical units, pulls vs the lattice mean, chi2_lat at every
  arm's tune.
* damping conditions of np_damping_wall at |Y| = 0 and 2.5 (both CS and TMD).
* basin markers: resumScaleMuF, resumTNP_b_qg, pdfEig23 (theta).
* alpha_s: ONLY Delta in sigma units vs each reference, and sigma(alpha_s).
  The central value is blinded (additive, same offset across all these data
  fits: same parameter name, same integer data) and is never printed.

usage: analyze_fits.py <tag>=<fitresult>[:walled][:lattice] ...
"""
import json
import sys

import h5py
import numpy as np
from wums import ioutils

from rabbit import inputdata, io_tools
from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall

CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARDA = f"{CEPH}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
import os as _os

_SUFFIX = "_l4zero" if _os.environ.get("LAT_L4ZERO", "1") == "1" else ""
LATCARD = f"{CEPH}/260923_lattice_fits/cards/cardA_latticeASWZ{_SUFFIX}_statsyst.hdf5"
LATCARD_STAT = (
    f"{CEPH}/260923_lattice_fits/cards/cardA_latticeASWZ{_SUFFIX}_statonly.hdf5"
)
TAU = 5.0
WIDTH_AS = 0.002
# resumScaleMuF is NOT fitted in this build (DEFAULT_FROZEN; the scale envelope replaced it),
# so the 260911 marker is unavailable. lumi / resumTNP_b_qqV / pdfEig14 separate the two
# current unwalled minima (alphas-scan-discontinuity 260921-jump-params: lumi -1.07 main vs +0.89 second).
MARKERS = ["lumi", "resumTNP_b_qqV", "pdfEig14", "resumTNP_b_qg", "pdfEig23"]


def term_from_card(card):
    with h5py.File(card, "r") as f:
        tg = f["external_terms"]["lattice_cs"]
        pr = [s.decode() if isinstance(s, bytes) else s for s in tg["params"][...]]
        g = np.asarray(tg["grad_values"][...]).reshape(
            tuple(tg["grad_values"].attrs["original_shape"])
        )
        H = np.asarray(tg["hess_dense"][...]).reshape(
            tuple(tg["hess_dense"].attrs["original_shape"])
        )
    C = np.linalg.inv(H)
    return pr, -C @ g, H, C


def read(path):
    r = io_tools.get_fitresult(path)
    h = r["parms"].get()
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in h.axes[0]]
    vals, errs = h.values(), np.sqrt(h.variances())
    cov = r["cov"].get().values()
    meta = ioutils.pickle_load_h5py(h5py.File(path, "r")["meta"])
    loss = np.asarray(r["epoch_loss"].get()) if "epoch_loss" in r else None
    return dict(
        names=names,
        vals=vals,
        errs=errs,
        cov=cov,
        meta=meta,
        nll=float(r["nllvalreduced"]),
        edm=float(r["edmval"]),
        nit=None if loss is None else int(np.size(loss)),
    )


def main():
    arms = []
    for tok in sys.argv[1:]:
        tag, rest = tok.split("=", 1)
        parts = rest.split(":")
        arms.append(
            dict(
                tag=tag,
                path=parts[0],
                walled="walled" in parts[1:],
                lattice="lattice" in parts[1:],
            )
        )

    ind = inputdata.FitInputData(CARDA)
    inp = wall.resolve_wall_inputs(ind)
    specs, anchors = inp["specs"], inp["anchors"]
    print(
        f"[wall] forms {inp['np_model']}/{inp['np_model_nu']}  binding |Y| = {inp['ymax']} ({inp['ymax_source']})"
    )
    conds = wall.damping_conditions(inp["np_model"], inp["np_model_nu"], inp["ymax"])
    systs = [s.decode() if isinstance(s, bytes) else str(s) for s in ind.systs]
    cw = np.asarray(ind.constraintweights)
    cwd = dict(zip(systs, cw))

    lat = {}
    for key, card in [("statsyst", LATCARD), ("statonly", LATCARD_STAT)]:
        pr, mu, H, C = term_from_card(card)
        width = np.array([specs[n][1][1] for n in pr])
        c0 = np.array([specs[n][1][0] for n in pr])
        lat[key] = dict(
            params=pr,
            mu=mu,
            H=H,
            C=C,
            mu_phys=c0 + width * mu,
            sig_phys=np.sqrt(np.diag(C)) * width,
        )
        rho = f"rho {C[0,1]/np.sqrt(C[0,0]*C[1,1]):+.4f}" if len(pr) == 2 else "(1D)"
        print(
            f"[lat:{key}] {card}\n     {pr} mu_phys {lat[key]['mu_phys']} sig_phys {lat[key]['sig_phys']} {rho}"
        )
    L = lat["statsyst"]

    for a in arms:
        a.update(read(a["path"]))
        idx = {n: i for i, n in enumerate(a["names"])}
        a["idx"] = idx
        th = {n: float(a["vals"][i]) for n, i in idx.items()}
        a["th"] = th
        a["phys"] = {
            n: (
                float(wall.physical_from_theta(specs[n], th[n]))
                if n in th
                else float(anchors[n])
            )
            for n in inp["names"]
        }
        a["phys_err"] = {
            n: (
                a["errs"][idx[n]] * specs[n][1][1]
                if n in idx and specs[n][0] == "quad"
                else 0.0
            )
            for n in inp["names"]
        }
        pp = a["meta"]["param_priors"]
        pn = [p.decode() if isinstance(p, bytes) else str(p) for p in pp["params"]]
        a["model_names"] = pn
        mask = np.asarray(pp["mask"], dtype=bool)
        sig = np.asarray(pp["sigmas"], dtype=float)
        mean = (
            np.asarray(pp["means"], dtype=float)
            if pp["means"] is not None
            else np.zeros(len(pn))
        )
        lc_model = sum(
            0.5 * ((th[n] - mean[i]) / sig[i]) ** 2 for i, n in enumerate(pn) if mask[i]
        )
        lc_card = sum(0.5 * cwd[n] * th[n] ** 2 for n in systs if n in th)
        a["n_model_constrained"] = int(mask.sum())
        lpen = 0.0
        if a["walled"]:
            # only conditions the wall ARMS: one depending solely on held lambdas is dropped by the wall
            # (np_damping_wall.py:795-816), e.g. lambda4_nu >= margin when lambda4_nu is frozen at 0.
            armed = [c for c in conds if any(n in idx for n in c.names)]
            lpen = float(
                sum(c.penalty(a["phys"], wall.numpy_relu2) for c in armed)
                * np.exp(2 * TAU)
            )
        t = np.array([th[n] for n in L["params"]])
        chi2lat = {
            k: float((t - v["mu"]) @ v["H"] @ (t - v["mu"])) for k, v in lat.items()
        }
        lext = 0.5 * chi2lat["statsyst"] if a["lattice"] else 0.0
        a.update(
            lc=lc_model + lc_card,
            lc_model=lc_model,
            lc_card=lc_card,
            lpen=lpen,
            lext=lext,
            chi2lat=chi2lat,
        )
        a["ln"] = a["nll"] - a["lc"] - lpen - lext
        w = np.linalg.eigvalsh(a["cov"])
        a["neg_eig"], a["cond"] = int((w < 0).sum()), float(
            w.max() / max(abs(w.min()), 1e-300)
        )
        a["sig_as"] = float(a["errs"][idx["alphaS"]] * WIDTH_AS)
        npn = [n for n in inp["names"] if n in idx and specs[n][0] == "quad"]
        ii = [idx[n] for n in npn]
        wv = np.array([specs[n][1][1] for n in npn])
        a["np_cov_phys"] = dict(
            names=npn, cov=(a["cov"][np.ix_(ii, ii)] * np.outer(wv, wv)).tolist()
        )
        a["cond_vals"] = [
            (c.label, float(c.value(a["phys"], wall.numpy_relu2)), c.bound)
            for c in conds
        ]

    bar = "=" * 100
    print(bar + "\nCONVERGENCE\n" + bar)
    for a in arms:
        print(
            f"  {a['tag']:12s} nll {a['nll']:.6f}  edm {a['edm']:.3e}  nit {a['nit']}  neg_eig(cov) {a['neg_eig']}  "
            f"cond {a['cond']:.3e}  sigma(alphaS) {a['sig_as']:.6f}  model priors {a['n_model_constrained']}"
        )
    print(bar + "\nLOSS DECOMPOSITION  nll = ln(data) + lc + lpen + lext\n" + bar)
    for a in arms:
        print(
            f"  {a['tag']:12s} nll {a['nll']:11.4f} lc {a['lc']:9.4f} (model {a['lc_model']:.4f} card {a['lc_card']:.4f}) "
            f"lpen {a['lpen']:9.4f} lext {a['lext']:8.4f} => ln {a['ln']:11.4f}"
        )
    refs = [a for a in arms if not a["lattice"]]
    print(
        bar
        + "\nDELTA chi2_data = 2 (ln - ln_ref), and Delta alphaS in sigma units (blinded: differences only)\n"
        + bar
    )
    for a in arms:
        for r in refs:
            if a is r:
                continue
            das = (a["th"]["alphaS"] - r["th"]["alphaS"]) * WIDTH_AS
            print(
                f"  {a['tag']:12s} vs {r['tag']:12s}: Dchi2_data {2*(a['ln']-r['ln']):+9.3f}  Dchi2_total {2*(a['nll']-r['nll']):+9.3f}  "
                f"Dalpha_s/sigma_ref {das / r['sig_as']:+.3f}  /sigma_arm {das / a['sig_as']:+.3f}"
            )
    print(bar + "\nNP LAMBDAS (physical)  and lattice pulls\n" + bar)
    for a in arms:
        s = "  ".join(
            f"{n} {a['phys'][n]:+.5f}({a['phys_err'][n]:.5f})"
            for n in inp["names"]
            if n in a["idx"]
        )
        print(f"  {a['tag']:12s} {s}")
        pulls = [
            (a["phys"][n] - L["mu_phys"][i]) / L["sig_phys"][i]
            for i, n in enumerate(L["params"])
        ]
        print(
            f"  {'':12s} pulls vs lattice (stat+syst marginal sigma): "
            + ", ".join(f"{n} {p:+.2f}" for n, p in zip(L["params"], pulls))
            + f"   chi2_lat statsyst {a['chi2lat']['statsyst']:.3f}  statonly {a['chi2lat']['statonly']:.3f}  (2 dof)"
        )
    c_names = {c.label: c.names for c in conds}
    print(
        bar
        + "\nDAMPING CONDITIONS  (value >= bound; FAIL if value < 0, 'margin' if 0 <= value < bound)\n"
        + bar
    )
    for a in arms:
        print(f"  {a['tag']}")
        for lab, v, b in a["cond_vals"]:
            held = all(n not in a["idx"] for n in c_names.get(lab, ()))
            flag = "FAIL" if v < 0 else ("margin" if v < b else "ok")
            if held:
                flag += "(held)"
            print(f"     {flag:6s} {v:+.5f}  (>= {b:g})  {lab}")
    print(bar + "\nBASIN MARKERS (theta)\n" + bar)
    for a in arms:
        print(
            f"  {a['tag']:12s} "
            + "  ".join(f"{m} {a['th'][m]:+.3f}" for m in MARKERS if m in a["th"])
        )
    # L2 distances in theta over model params except alphaS
    print("  L2 distance over param-model thetas (alphaS excluded):")
    model = sorted(
        set.intersection(*[set(a["model_names"]) for a in arms]) - {"alphaS"}
    )
    print(f"  (over {len(model)} model params common to all arms)")
    for a in arms:
        row = []
        for b in arms:
            row.append(
                np.sqrt(
                    sum(
                        (a["th"][n] - b["th"][n]) ** 2
                        for n in model
                        if n in a["th"] and n in b["th"]
                    )
                )
            )
        print(f"    {a['tag']:12s} " + " ".join(f"{x:6.3f}" for x in row))
    out = {
        a["tag"]: dict(
            nll=a["nll"],
            edm=a["edm"],
            nit=a["nit"],
            neg_eig=a["neg_eig"],
            ln=a["ln"],
            lc=a["lc"],
            lpen=a["lpen"],
            lext=a["lext"],
            phys=a["phys"],
            phys_err=a["phys_err"],
            chi2lat=a["chi2lat"],
            sig_as=a["sig_as"],
            np_cov_phys=a["np_cov_phys"],
            markers={m: a["th"][m] for m in MARKERS if m in a["th"]},
            conds=a["cond_vals"],
        )
        for a in arms
    }
    return out


if __name__ == "__main__":
    import os

    res = main()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json.dump(
        res, open(os.path.join(here, "analysis.json"), "w"), indent=1, default=float
    )
