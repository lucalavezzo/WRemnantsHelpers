"""Postfit-NP comparison table for the FranksVals (LatticeNoConstraintsFranks)
NP model. Mirrors studies/260511_np_monotonicity_wall/scripts/build_compare_table.py
but with the FranksVals param set: 4 nuisances (lambda_4_nu and lambda_inf_nu
are fixed in Frank's config, so omitted). Uses np_param_map_franks.json for
linearization; no helper_internal kfactor=10 (the new branch does not apply it).
"""

import argparse, json, os, sys, subprocess
import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")
from rabbit.io_tools import get_fitresult
from scipy.stats import chi2 as chi2_dist

PMAP_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "np_param_map_franks.json"
)
with open(PMAP_JSON) as f:
    PMAP = json.load(f)

# Column order and display labels. FranksVals: only 4 floating NPs.
NPS = [
    ("scetlibNPgammaLambda2", r"$\gamma_{\Lambda_2}$"),
    ("chargeVgenNP0scetlibNPZlambda2", r"$\Lambda_2$"),
    ("chargeVgenNP0scetlibNPZdelta_lambda2", r"$\Delta\Lambda_2$"),
    ("chargeVgenNP0scetlibNPZlambda4", r"$\Lambda_4$"),
]

POI = "pdfAlphaS"

DISPLAY_NAME = {
    "prefit": r"prefit (FranksVals)",
    "nominal": r"nominal (avg sym)",
    "asym": r"asymmetric NP",
    "inflate5x": r"NP priors $\times 5$ (avg sym)",
    "asym_inflate5x": r"asymmetric NP + NP priors $\times 5$",
    "asym_reg": r"asymmetric NP + wall ($\tau{=}5$)",
    "quadratic": r"nominal (quadratic sym)$^*$",
    "nominal_fakelumi": r"nominal (avg sym) + fakelumi",
    "asym_fakelumi": r"asymmetric NP + fakelumi",
    "inflate5x_fakelumi": r"NP priors $\times 5$ (avg sym) + fakelumi",
    "asym_inflate5x_fakelumi": r"asymmetric NP + NP priors $\times 5$ + fakelumi",
    "asym_reg_fakelumi": r"asymmetric NP + wall ($\tau{=}5$) + fakelumi",
    "quadratic_fakelumi": r"nominal (quadratic sym) + fakelumi$^*$",
    "lambda4asym": r"$\Lambda_4$ only asym (others avg sym)",
    "lambda4asym_fakelumi": r"$\Lambda_4$ only asym (others avg sym) + fakelumi",
}

SECTIONS = [
    ["prefit"],
    # average symmetrization (the framework default for NP nuisances)
    ["nominal", "nominal_fakelumi", "inflate5x", "inflate5x_fakelumi"],
    # quadratic symmetrization (SymAvg + SymDiff split — see footnote *)
    ["quadratic", "quadratic_fakelumi"],
    # mixed: only Lambda_4 asymmetric, others avg sym
    ["lambda4asym", "lambda4asym_fakelumi"],
    # asymmetric (--noSymmetrize): NP templates kept asymmetric in the tensor
    [
        "asym",
        "asym_fakelumi",
        "asym_inflate5x",
        "asym_inflate5x_fakelumi",
        "asym_reg",
        "asym_reg_fakelumi",
    ],
]

SKIP_LABELS = set()

# kfactor=5 for any config that passed --scaleParams 'scetlibNP=5'.
KFACTOR_OVERRIDES = {
    "prefit": {},
    "nominal": {},
    "asym": {},
    "nominal_fakelumi": {},
    "asym_fakelumi": {},
    "inflate5x": {nuis: 5.0 for nuis, _ in NPS},
    "inflate5x_fakelumi": {nuis: 5.0 for nuis, _ in NPS},
    "asym_inflate5x": {nuis: 5.0 for nuis, _ in NPS},
    "asym_inflate5x_fakelumi": {nuis: 5.0 for nuis, _ in NPS},
    "asym_reg": {},  # no --scaleParams; wall + free-floating
    "asym_reg_fakelumi": {},
    "quadratic": {},
    "quadratic_fakelumi": {},
    "lambda4asym": {},
    "lambda4asym_fakelumi": {},
}

# fakelumi at setupRabbit time uses log-normal kappa = 1.1; postfit
# pull theta -> percent yield as (kappa^theta - 1) * 100.
FAKELUMI_KAPPA = 1.1

# fakelumi-on -> no-fakelumi pairs for 2*Delta NLL chi^2_1 test.
FAKELUMI_PAIRS = {
    "nominal_fakelumi": "nominal",
    "asym_fakelumi": "asym",
    "inflate5x_fakelumi": "inflate5x",
    "asym_inflate5x_fakelumi": "asym_inflate5x",
    "asym_reg_fakelumi": "asym_reg",
    "quadratic_fakelumi": "quadratic",
    "lambda4asym_fakelumi": "lambda4asym",
}


def get_parm(parms, name):
    """Look up a nuisance pull by name. Falls back to `<name>SymAvg` for
    fits run with quadratic symmetrization, which splits each systematic
    into a SymAvg (symmetric direction) + SymDiff (asymmetric direction)
    pair. SymAvg is the closest analogue to the single-nuisance pull
    that physical_shift assumes; SymDiff is dumped to stdout as a side
    note since it has no place in the linearization."""
    names = list(parms.axes[0])
    if name in names:
        i = names.index(name)
        return float(parms.values()[i]), float(np.sqrt(parms.variances()[i]))
    alt = f"{name}SymAvg"
    if alt in names:
        i = names.index(alt)
        return float(parms.values()[i]), float(np.sqrt(parms.variances()[i]))
    return None, None


def physical_shift(nuis, theta, sigma_theta, kfactor=1.0):
    info = PMAP["nuisances"][nuis]
    nom = info["nominal"]
    up = info["Up_template_value"]
    dn = info["Down_template_value"]
    d_up = (up - nom) * kfactor
    d_dn = (nom - dn) * kfactor
    val = nom + max(theta, 0) * d_up - max(-theta, 0) * d_dn
    slope = d_up if theta >= 0 else d_dn
    return val, abs(slope) * sigma_theta


def fmt_cell(theta, err, nuis, mode, kfactor=1.0):
    if theta is None:
        return "---"
    if err == 0.0:
        return "frozen"
    if mode == "physical":
        v, vu = physical_shift(nuis, theta, err, kfactor=kfactor)
        return f"${v:+.4f}\\pm{vu:.4f}$"
    return f"${theta:+.3f}\\pm{err:.3f}$"


def load_fit(path):
    fr, _ = get_fitresult(path, meta=True)
    parms = fr["parms"].get()
    out = {"path": path, "params": {}}
    for nuis, _ in NPS:
        out["params"][nuis] = get_parm(parms, nuis)
    # Surface SymDiff pulls from quadratic fits (not in the main table).
    names = list(parms.axes[0])
    diffs = [
        n
        for n in names
        if n.endswith("SymDiff") and any(n.startswith(nm) for nm, _ in NPS)
    ]
    if diffs:
        print(
            f"  Note: {os.path.basename(os.path.dirname(path))} carries SymDiff pulls (quadratic split):"
        )
        for n in diffs:
            i = names.index(n)
            v = float(parms.values()[i])
            s = float(np.sqrt(parms.variances()[i]))
            print(f"    {n:55s} theta = {v:+.3f} +/- {s:.3f}")
    out["alphaS"] = get_parm(parms, POI)
    out["fakelumi"] = get_parm(parms, "fakelumi")
    try:
        v = fr["nllvalreduced"]
        out["nllvalreduced"] = float(v.get()) if hasattr(v, "get") else float(v[()])
    except Exception:
        out["nllvalreduced"] = None
    # Saturated p-value for the ptll projection (works for fits run with
    # -m Project ch0 ptll --computeSaturatedProjectionTests).
    out["sat_p_ptll"] = None
    if "mappings" in fr:
        try:
            m = fr["mappings"]["Project ch0 ptll"]
            cs = float(m["chi2_saturated"])
            n = float(m["ndf"])
            if cs == cs and n > 0:
                out["sat_p_ptll"] = chi2_dist.sf(cs, n) * 100
        except (KeyError, TypeError, ValueError):
            pass
    return out


def build_latex(fits, mode):
    nom_lab, nom = fits[0]
    nom_aS = nom["alphaS"]

    header_np = " & ".join([lab for _, lab in NPS])
    lines = [
        r"\documentclass[10pt]{article}",
        r"\usepackage[a4paper,landscape,margin=1cm]{geometry}",
        r"\usepackage{graphicx}",
        r"\usepackage{booktabs}",
        r"\pagestyle{empty}",
        r"\begin{document}",
        r"\noindent\resizebox{\textwidth}{!}{%",
        r"  \begin{tabular}{l" + "c" * len(NPS) + "rrrrr}",
        r"    \hline\hline",
        r"    Configuration & "
        + header_np
        + r" & Sat.\ $p$ ($p_T^{\ell\ell}$)"
        + r" & $\Delta$pull$(\alpha_S)\,[10^{-3}]$"
        + r" & $\sigma(\alpha_S)\,[10^{-3}]$"
        + r" & fakelumi $[\%]$"
        + r" & $2\Delta\mathrm{NLL}\,(\chi^2_1)$ \\",
        r"    \hline",
    ]
    prefit_d = {
        "path": "<prefit>",
        "params": {nuis: (0.0, 1.0) for nuis, _ in NPS},
        "alphaS": None,
        "sat_p_ptll": None,
        "_is_prefit": True,
    }
    fits_by_label = {"prefit": prefit_d}
    fits_by_label.update({lab: d for lab, d in fits if lab not in SKIP_LABELS})

    ordered = []
    used = set()
    for sec_idx, section in enumerate(SECTIONS):
        for lab in section:
            if lab in SKIP_LABELS:
                continue
            if lab in fits_by_label and lab not in used:
                ordered.append((sec_idx, lab, fits_by_label[lab]))
                used.add(lab)
    for lab, d in fits:
        if lab in SKIP_LABELS:
            continue
        if lab not in used:
            ordered.append((len(SECTIONS), lab, d))

    prev_sec = None
    for sec_idx, lab, d in ordered:
        if prev_sec is not None and sec_idx != prev_sec:
            lines.append(r"    \hline")
        prev_sec = sec_idx

        cells = []
        koverride = KFACTOR_OVERRIDES.get(lab, {})
        for nuis, _ in NPS:
            t, e = d["params"][nuis]
            k = koverride.get(nuis, 1.0)
            # Prefit row in physical mode: show the actual histmaker template
            # ranges (asymmetric where applicable) instead of a symmetric
            # +/- band derived from sigma_theta=1. Theta mode stays at the
            # bare 0 +/- 1 prior.
            if d.get("_is_prefit") and mode == "physical":
                info = PMAP["nuisances"][nuis]
                nom = info["nominal"]
                d_up = (info["Up_template_value"] - nom) * k
                d_dn = (nom - info["Down_template_value"]) * k
                if abs(d_up - d_dn) < 1e-6:
                    cells.append(f"${nom:+.4f}\\pm{d_up:.4f}$")
                else:
                    cells.append(f"${nom:+.4f}^{{+{d_up:.4f}}}_{{-{d_dn:.4f}}}$")
            else:
                cells.append(fmt_cell(t, e, nuis, mode, kfactor=k))

        if d.get("_is_prefit"):
            d_as = "---"
            sig_hess = "---"
        else:
            a = d["alphaS"]
            if a == (None, None) or a is None:
                d_as = "---"
                sig_hess = "---"
            else:
                d_as = "ref" if (lab == nom_lab) else f"${(a[0] - nom_aS[0])*2:+.3f}$"
                sig_hess = f"${a[1]*2:.3f}$"

        sp = d.get("sat_p_ptll")
        sp_cell = f"${sp:.2f}\\%$" if sp is not None else "---"

        # fakelumi percent pull = (kappa^theta - 1) * 100
        fl = d.get("fakelumi")
        if d.get("_is_prefit") or fl in (None, (None, None)) or fl[0] is None:
            fl_cell = "---"
        else:
            theta_fl, _ = fl
            pct = (FAKELUMI_KAPPA**theta_fl - 1.0) * 100.0
            fl_cell = f"${pct:+.2f}\\%$"

        # 2*Delta NLL chi^2_1 for the fakelumi LR test (fakelumi row vs partner).
        chi2_cell = "---"
        partner_lab = FAKELUMI_PAIRS.get(lab)
        if partner_lab is not None:
            partner = fits_by_label.get(partner_lab)
            nll_fl = d.get("nllvalreduced")
            nll_no = partner.get("nllvalreduced") if partner is not None else None
            if nll_fl is not None and nll_no is not None:
                dnll2 = 2.0 * (nll_no - nll_fl)
                if dnll2 > 0:
                    sigma_eq = dnll2**0.5
                    pval = chi2_dist.sf(dnll2, df=1)
                    chi2_cell = (
                        f"${dnll2:.2f}\\ ({sigma_eq:.2f}\\sigma,\\ p\\!=\\!{pval:.2g})$"
                    )
                else:
                    chi2_cell = f"${dnll2:.2f}\\ (\\mathrm{{n/a}})$"

        lab_tex = DISPLAY_NAME.get(lab, lab.replace("_", r"\_"))
        lines.append(
            f"    {lab_tex} & "
            + " & ".join(cells)
            + f" & {sp_cell} & {d_as} & {sig_hess}"
            + f" & {fl_cell} & {chi2_cell} \\\\"
        )

    lines += [
        r"    \hline\hline",
        r"  \end{tabular}%",
        r"}",
        r"\par\vspace{0.6em}",
        r"\footnotesize FranksVals NP model (\texttt{LatticeNoConstraintsFranks}). "
        + (
            r"NP cells: postfit physical value (linearized interp.\ from \texttt{np\_param\_map\_franks.json}), "
            r"with per-config kfactor overrides applied. "
            if mode == "physical"
            else r"NP cells: raw rabbit nuisance pull $\theta \pm \sigma_\theta$ (no kfactor / no physical linearization). "
            r"Prior is $\mathcal{N}(0,1)$ on each $\theta$. "
        )
        + r"$\Delta$pull$(\alpha_S)=(\theta-\theta_{\rm nom})\times 2$ in $10^{-3}$; "
        r"$\sigma(\alpha_S)$ also $\times 2$ (Hessian). "
        r"Sat.\ $p$ from the saturated-likelihood test on the $p_T^{\ell\ell}$ projection. "
        r"All rows are real-data fits ($-t\,0$); $\alpha_S$ POI stays blinded so only the "
        r"reference-relative $\Delta$pull is meaningful. "
        r"$^*$Quadratic-symmetrized rows: rabbit splits each shape syst into a SymAvg "
        r"(symmetric direction) + SymDiff (asymmetric direction) nuisance pair; the "
        r"table shows only the SymAvg pull / constraint, SymDiff values are printed "
        r"to stdout during rendering.",
        r"\end{document}",
    ]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "specs",
        nargs="+",
        help="LABEL=path entries (order matters; first = reference for ΔαS)",
    )
    p.add_argument("--mode", choices=["physical", "theta"], default="physical")
    p.add_argument("--output", "-o", required=True, help="Output directory")
    args = p.parse_args()

    fits = []
    for spec in args.specs:
        lab, path = spec.split("=", 1)
        try:
            fits.append((lab, load_fit(path)))
        except Exception as e:
            print(f"WARNING: could not load {lab} ({path}): {e}")
            fits.append(
                (
                    lab,
                    {
                        "path": path,
                        "params": {nm: (None, None) for nm, _ in NPS},
                        "alphaS": None,
                        "sat_p_ptll": None,
                        "_failed": True,
                    },
                )
            )

    os.makedirs(args.output, exist_ok=True)
    suffix = "" if args.mode == "physical" else f"_{args.mode}"
    tex_path = os.path.join(args.output, f"np_compare_franks{suffix}.tex")
    with open(tex_path, "w") as fh:
        fh.write(build_latex(fits, args.mode))
    print(f"Wrote {tex_path}")

    # pdflatex is not in the container (Arch-based wmass image); compile
    # on the host if available, otherwise just print a hint.
    import shutil as _sh

    if _sh.which("pdflatex"):
        r = subprocess.run(
            [
                "pdflatex",
                "-interaction=batchmode",
                "-output-directory",
                args.output,
                tex_path,
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            print("pdflatex failed:")
            print(r.stdout[-2000:])
            sys.exit(1)
        print(f"Wrote {os.path.join(args.output, f'np_compare_franks{suffix}.pdf')}")
    else:
        print(
            f"pdflatex not found in PATH; compile {tex_path} on the host with: "
            f"pdflatex -interaction=batchmode -output-directory {args.output} {tex_path}"
        )


if __name__ == "__main__":
    main()
