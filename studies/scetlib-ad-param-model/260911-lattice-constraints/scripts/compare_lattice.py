#!/usr/bin/env python3
"""Five-way read: plain / ridge / spectral / walled / LATTICE-PRIOR.

Reuses ``../260910-spectral-precond/scripts/compare_arms.py`` for the four
existing arms' transcribed log numbers, its fitresult reader (which waits out
h5 contention rather than forcing it), and the wall module's theta->physical
resolver and damping conditions -- so what is evaluated here is literally what
the wall would impose, on the same coordinate the model fits.

What this adds beyond that four-way script:

* The LATTICE PRIOR is read back OUT OF THE CARD the fit actually used
  (``external_terms/lattice_cs``: g and H in theta), and inverted to
  (mu, C). Nothing about the prior is re-typed here -- if the card and this
  report disagree, the card wins and this crashes.
* A LOSS DECOMPOSITION. rabbit's ``fun`` is
  ``ln + lc + lpenalty + lext`` (fitter._compute_nll). The arms differ in
  ``lc`` (the lattice arm frees two model priors), in ``lpenalty`` (only the
  walled arm) and in ``lext`` (only the lattice arm), so comparing ``fun``
  across them compares different things. All four pieces are computed here
  from each arm's own postfit theta, and the DATA term ``ln`` is what is
  compared.
* The lattice chi2 AT EVERY ARM'S TUNE -- i.e. how far each existing minimum
  sits from the lattice constraint, in its own units.
* The question the task exists for: are the NP uncertainties DATA-determined?
  Answered by decomposing the posterior precision into prior + data along the
  prior's own eigendirections.

POLICY, inherited: alphaS's central value is blinded and never printed. sigma,
losses, EDM, chi2 and p-values are safe under additive blinding.

usage: compare_lattice.py <fit_DATALAT_*.log>
"""
import json
import os
import subprocess
import sys

import h5py
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.abspath(
    os.path.join(HERE, "..", "..", "260910-spectral-precond", "scripts")
)
BAS = os.path.abspath(os.path.join(HERE, "..", "..", "260910-basins", "scripts"))
CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
LATCARD = f"{CEPH}/study_scratch/260911-lattice/card_latticeCS.hdf5"
TAU = 5.0  # the walled arm's --regularizationStrength

sys.path.insert(0, SPEC)
import compare_arms as CA  # noqa: E402

from rabbit import inputdata, io_tools  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402

WIDTH_AS = 0.002
MODEL_PREFIXES = CA.MODEL_PREFIXES


def parsed(logfile):
    return json.loads(
        subprocess.check_output(
            [sys.executable, os.path.join(BAS, "parse_fitlog.py"), logfile]
        ).decode()
    )


def read_full(path):
    """theta, sigma and the FULL covariance (for the NP block)."""
    src = CA._local_copy(path)
    res = io_tools.get_fitresult(src)
    h = res["parms"].get()
    names = [str(n) for n in h.axes[0]]
    vals = h.values()
    errs = np.sqrt(h.variances())
    cov = res["cov"].get().values()
    return names, vals, errs, cov


def lattice_prior_from_card(card):
    """(params, mu_theta, cov_theta) read back out of the card's own term."""
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
    mu = -C @ g
    return list(pr), mu, C


def main():
    logfile = sys.argv[1]
    p = parsed(logfile)

    ARMS = list(CA.ARMS) + [
        dict(
            tag="lattice",
            postfix="DATALAT",
            fit=f"{CEPH}/260911_lattice/fitresults_DATALAT.hdf5",
            fun=p["fun"],
            nit=p["nit"],
            nfev=p["nfev"],
            nhev=p["nhev"],
            minimize_s=p["minimize_s"],
            edm=p["edm"],
            sat_2dnll=p.get("sat_2dnll"),
            sat_ndof=p.get("sat_ndof"),
            lin_chi2=p.get("lin_chi2"),
            lin_ndof=p.get("lin_ndof"),
            sat_p=p.get("sat_p"),
            lin_p=p.get("lin_p"),
            load0=p.get("load0"),
            precond=None,
            walled=False,
            lattice=True,
            status=p.get("status"),
            log=os.path.relpath(logfile, os.path.dirname(HERE)),
        )
    ]
    print(f"[fifth arm parsed from] {logfile}")
    for k in (
        "fun",
        "nit",
        "nfev",
        "nhev",
        "minimize_s",
        "edm",
        "status",
        "exit_status",
        "maxrss_gib",
        "n_rejected",
        "frac_rejected",
    ):
        if p.get(k) is not None:
            print(f"    {k:14s} {p[k]}")
    print()

    inp = wall.resolve_wall_inputs(inputdata.FitInputData(CA.CARD))
    conds = wall.damping_conditions(inp["np_model"], inp["np_model_nu"], inp["ymax"])
    lat_names, lat_mu, lat_cov = lattice_prior_from_card(LATCARD)
    lat_H = np.linalg.inv(lat_cov)
    lat_s = np.sqrt(np.diag(lat_cov))
    specs = inp["specs"]
    lat_phys_mu = np.array(
        [
            float(wall.physical_from_theta(specs[n], lat_mu[i]))
            for i, n in enumerate(lat_names)
        ]
    )
    lat_width = np.array(
        [specs[n][1][1] if specs[n][0] == "quad" else 1.0 for n in lat_names]
    )
    print("=" * 78)
    print("THE LATTICE PRIOR, read back out of the card the fit used")
    print("=" * 78)
    print(f"  card      {LATCARD}")
    print(f"  params    {lat_names}")
    print(f"  theta mu  {np.array2string(lat_mu, precision=6)}")
    print(f"  theta sig {np.array2string(lat_s, precision=6)}")
    print(f"  rho       {lat_cov[0,1] / (lat_s[0] * lat_s[1]):+.6f}")
    print(f"  widths    {np.array2string(lat_width, precision=4)}  (theta -> physical)")
    print(f"  phys  mu  {np.array2string(lat_phys_mu, precision=6)}")
    print(f"  phys  sig {np.array2string(lat_s * lat_width, precision=6)}")
    ev, evec = np.linalg.eigh(lat_cov)
    for k in range(len(ev)):
        print(
            f"  eigendir {k}: sigma {np.sqrt(ev[k]):.6g}  "
            f"direction {np.array2string(evec[:, k], precision=4)}"
        )
    print()

    live = []
    for a in ARMS:
        if not os.path.exists(a["fit"]) or os.path.getsize(a["fit"]) < 10_000_000:
            print(f"[skip] {a['tag']:9s} no usable fitresult: {a['fit']}")
            continue
        names, vals, errs, cov = read_full(a["fit"])
        a["names"], a["vals"], a["errs"], a["cov"] = names, vals, errs, cov
        a["idx"] = {n: i for i, n in enumerate(names)}
        a["theta"] = {n: float(vals[i]) for i, n in enumerate(names)}
        a["sig"] = {n: float(errs[i]) for i, n in enumerate(names)}
        a["phys"] = {
            n: (
                float(wall.physical_from_theta(specs[n], a["theta"][n]))
                if n in a["theta"]
                else float(inp["anchors"][n])
            )
            for n in inp["names"]
        }
        live.append(a)

    W = 13

    def row(label, fmt, key=None, fn=None):
        cells = []
        for a in live:
            v = fn(a) if fn else a.get(key)
            if v is None:
                cells.append("n/a".rjust(W))
            elif fmt == "s":
                cells.append(str(v)[: W - 1].rjust(W))
            else:
                cells.append(format(v, fmt).rjust(W))
        print(f"  {label:34s}" + "".join(cells))

    bar = "=" * (36 + W * len(live))
    print(bar)
    print("CONVERGENCE AND COST")
    print(bar)
    print("  " + "arm".ljust(34) + "".join(a["tag"].rjust(W) for a in live))
    print("  " + "postfix".ljust(34) + "".join(a["postfix"].rjust(W) for a in live))
    print("-" * len(bar))
    row("loss (fun, NOT comparable as-is)", ".4f", "fun")
    row("iterations (nit)", "d", "nit")
    row("Hessian-vector products (nhev)", "d", "nhev")
    row("minimize() [s]", ".0f", "minimize_s")
    row("loadavg at launch", ".0f", "load0")
    row("EDM", ".3e", "edm")
    row("saturated 2*dNLL", ".2f", "sat_2dnll")
    row("saturated p [%] (as logged)", ".2f", "sat_p")
    print("-" * len(bar))
    row("sigma(theta_alphaS)", ".6f", fn=lambda a: a["sig"]["alphaS"])
    row("sigma(alpha_s)", ".6f", fn=lambda a: a["sig"]["alphaS"] * WIDTH_AS)
    print("  [alphaS CENTRAL VALUE IS BLINDED - not printed]")

    # ---- negative Hessian eigenvalues: is each stop a real minimum? ---------
    print()
    print("--- posterior covariance: is it a genuine minimum? ---")
    for a in live:
        c = a["cov"]
        w = np.linalg.eigvalsh(0.5 * (c + c.T))
        print(
            f"  {a['tag']:9s} n={c.shape[0]}  min eig {w.min():+.4e}  "
            f"max eig {w.max():.4e}  cond {w.max()/max(w.min(),1e-300):.3e}  "
            f"negative: {int((w < 0).sum())}"
        )

    # ---- LOSS DECOMPOSITION -------------------------------------------------
    print()
    print(bar)
    print(
        "LOSS DECOMPOSITION   fun = ln(data) + lc(priors) + lpenalty(wall) + lext(lattice)"
    )
    print(bar)
    for a in live:
        names = a["names"]
        model = [n for n in names if n.startswith(MODEL_PREFIXES)]
        card = [n for n in names if not n.startswith(MODEL_PREFIXES)]
        free = {"alphaS"}
        if a.get("lattice"):
            free |= set(lat_names)
        th_model = np.array([a["theta"][n] for n in model if n not in free])
        th_card = np.array([a["theta"][n] for n in card])
        lc = 0.5 * (np.sum(th_model**2) + np.sum(th_card**2))
        lpen = 0.0
        if a.get("walled"):
            lpen = float(
                sum(c.penalty(a["phys"], wall.numpy_relu2) for c in conds)
                * np.exp(2 * TAU)
            )
        lext = 0.0
        if a.get("lattice"):
            t = np.array([a["theta"][n] for n in lat_names])
            lext = float(0.5 * (t - lat_mu) @ lat_H @ (t - lat_mu))
        ln = a["fun"] - lc - lpen - lext
        a["ln"], a["lc"], a["lpen"], a["lext"] = ln, lc, lpen, lext
        print(
            f"  {a['tag']:9s} fun {a['fun']:11.4f}   lc {lc:9.4f} "
            f"({len(th_model)} model + {len(th_card)} card constrained)"
            f"   lpenalty {lpen:8.4f}   lext {lext:8.4f}"
            f"   =>  ln(data) {ln:11.4f}"
        )
    base = next((a for a in live if a["tag"] == "plain"), None)
    if base:
        print()
        print("  --- relative to the plain arm (chi2 = 2 x NLL) ---")
        for a in live:
            print(
                f"  {a['tag']:9s} D(data ln) {a['ln']-base['ln']:+9.4f}  "
                f"D(chi2_data) {2*(a['ln']-base['ln']):+9.3f}   |   "
                f"D(total fun) {a['fun']-base['fun']:+9.4f}  "
                f"D(chi2_tot) {2*(a['fun']-base['fun']):+9.3f}"
            )

    # ---- the NP tune --------------------------------------------------------
    print()
    print(bar)
    print("PHYSICAL NP TUNE  (anchor + width*theta)")
    print(bar)
    print(
        "  "
        + "lambda".ljust(20)
        + "anchor".rjust(10)
        + "".join(a["tag"].rjust(W) for a in live)
    )
    print("-" * len(bar))
    for n in inp["names"]:
        cells = "".join(format(a["phys"][n], ".6f").rjust(W) for a in live)
        held = "" if n in live[0]["theta"] else "  (held)"
        print(f"  {n:20s}{float(inp['anchors'][n]):10.5f}{cells}{held}")

    print()
    print("--- damping conditions: how many are UNPHYSICAL (coeff < 0) ---")
    for a in live:
        bad = [
            (c.label, float(c.value(a["phys"], wall.numpy_relu2)))
            for c in conds
            if float(c.value(a["phys"], wall.numpy_relu2)) < 0.0
        ]
        pen = sum(float(c.penalty(a["phys"], wall.numpy_relu2)) for c in conds)
        print(
            f"  {a['tag']:9s} {len(bad)}/{len(conds)} unphysical, "
            f"bare penalty {pen:.6g}"
        )
        for lab, v in bad:
            print(f"      {lab:62s} {v:+13.6g}")

    print()
    print("--- CS kernel sign structure  P(u) = l2nu*u + l4nu*u^2 ---")
    for a in live:
        l2, l4 = a["phys"]["lambda2_nu"], a["phys"]["lambda4_nu"]
        root = -l2 / l4 if l4 != 0 else np.inf
        if root > 0:
            side = "b_T <" if l2 < 0 else "b_T >"
            print(
                f"  {a['tag']:9s} l2nu={l2:+.6g} l4nu={l4:+.6g}  -> "
                f"anti-damping for {side} {np.sqrt(root):.3g} GeV^-1"
            )
        else:
            print(
                f"  {a['tag']:9s} l2nu={l2:+.6g} l4nu={l4:+.6g}  -> P >= 0 everywhere"
            )

    # ---- lattice tension at every arm's tune --------------------------------
    print()
    print(bar)
    print("LATTICE TENSION at each arm's postfit CS tune")
    print(bar)
    for a in live:
        t = np.array([a["theta"][n] for n in lat_names])
        d = t - lat_mu
        chi2 = float(d @ lat_H @ d)
        pulls = d / lat_s
        proj = evec.T @ d / np.sqrt(ev)
        print(
            f"  {a['tag']:9s} chi2_lat {chi2:9.3f} (2 dof, p = "
            f"{100*stats.chi2.sf(chi2, 2):7.3f} %)   "
            f"marginal pulls {np.array2string(pulls, precision=2)}   "
            f"eigen pulls {np.array2string(proj, precision=2)}"
        )
    print("  (marginal pull = (theta-mu)/sigma_marginal; eigen pull is the one that")
    print("   enters chi2 -- with rho = -0.91 they are very different numbers)")

    # ---- ARE THE NP UNCERTAINTIES DATA-DETERMINED? --------------------------
    print()
    print(bar)
    print("ARE THE NP UNCERTAINTIES DATA-DETERMINED?")
    print(bar)
    for a in live:
        ii = [a["idx"][n] for n in lat_names]
        Cp = a["cov"][np.ix_(ii, ii)]
        sp = np.sqrt(np.diag(Cp))
        rho = Cp[0, 1] / (sp[0] * sp[1])
        if a.get("lattice"):
            ref, reflab = lat_cov, "lattice prior"
        elif a.get("walled"):
            ref, reflab = None, "wall (no Gaussian ref)"
        else:
            ref, reflab = np.eye(2), "default sigma=1 theta prior"
        print(
            f"  {a['tag']:9s} posterior sigma(theta) "
            f"{np.array2string(sp, precision=5)}  rho {rho:+.4f}"
        )
        print(
            f"            physical sigma "
            f"{np.array2string(sp * lat_width, precision=6)}"
        )
        if ref is not None:
            # VARIANCE REDUCTION along the reference prior's eigendirections.
            # Deliberately not called "the data's share of the precision":
            # Cp is the MARGINAL posterior 2x2 (profiled over the other 3718
            # parameters), so precisions do not simply add along u unless u is
            # also an eigenvector of Cp. What 1 - var_post/var_prior does say,
            # and all it says, is how much narrower the posterior is than the
            # prior in that direction -- i.e. whether the width is the prior's
            # or the data's.
            evr, evcr = np.linalg.eigh(ref)
            for k in range(2):
                u = evcr[:, k]
                var_prior = float(u @ ref @ u)
                var_post = float(u @ Cp @ u)
                f_data = 1.0 - var_post / var_prior
                print(
                    f"            vs {reflab}, eigdir {k}: prior sigma "
                    f"{np.sqrt(var_prior):.5f} -> posterior {np.sqrt(var_post):.5f}"
                    f"   variance reduction {100*f_data:6.2f} %"
                )
        else:
            print(
                f"            ({reflab}: lambda2_nu is RAILED -- its sigma is the "
                f"wall width 1/sqrt(2 e^{{2 tau}} w^2) = "
                f"{1/np.sqrt(2*np.exp(2*TAU)*lat_width[0]**2):.5f}, not a measurement)"
            )

    # ---- basin --------------------------------------------------------------
    print()
    print(bar)
    print("BASIN: L2 distance between arms over the model parameters")
    print("       (alphaS EXCLUDED so nothing unblinds)")
    print(bar)
    keys = [
        n for n in live[0]["names"] if n.startswith(MODEL_PREFIXES) and n != "alphaS"
    ]
    print("  " + " " * 12 + "".join(a["tag"].rjust(W) for a in live))
    for a in live:
        cells = []
        for b in live:
            d = np.array([a["theta"][k] - b["theta"][k] for k in keys])
            cells.append(format(np.linalg.norm(d), ".3f").rjust(W))
        print(f"  {a['tag']:12s}" + "".join(cells))
    print(f"  (L2 over {len(keys)} model parameters)")

    # the biggest single contributors to the lattice arm's distance from each
    lat = next((a for a in live if a.get("lattice")), None)
    if lat is not None:
        print()
        print("  --- what drives the lattice arm's distance? top 6 per pair ---")
        for b in live:
            if b is lat:
                continue
            d = {k: lat["theta"][k] - b["theta"][k] for k in keys}
            top = sorted(d, key=lambda k: -abs(d[k]))[:6]
            print(f"    vs {b['tag']:9s} " + "  ".join(f"{k}={d[k]:+.3f}" for k in top))

    print()
    print("--- card nuisances ---")
    for a in live:
        cn = [n for n in a["names"] if not n.startswith(MODEL_PREFIXES)]
        cv = np.array([a["theta"][n] for n in cn])
        i = int(np.argmax(np.abs(cv)))
        print(
            f"  {a['tag']:9s} n={len(cv)}  max|pull| {abs(cv[i]):.3f} "
            f"({cn[i]})   >2sig: {int((np.abs(cv) > 2).sum())}   "
            f">3sig: {int((np.abs(cv) > 3).sum())}"
        )

    print("COMPARE_LATTICE_DONE")


if __name__ == "__main__":
    main()
