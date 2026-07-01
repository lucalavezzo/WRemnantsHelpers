"""Build postfit-NP LaTeX/PDF tables for the 1D ptll-only and 1D yll-only
fits (rebuilt workspaces via `setupRabbit --fitvar ptll|yll`). Sister to
build_compare_table.py — same column structure but no `Sat.p (ptll)`
column (the saturated chi² for a 1D fit *is* the 1D goodness-of-fit, shown
as the single `Sat.p (1D)` column).

Two tables, one PDF: top = ptll-only, bottom = yll-only.
"""

import argparse, json, os, sys, subprocess
import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")
from rabbit.io_tools import get_fitresult
from scipy.stats import chi2 as chi2_dist

PMAP_JSON = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/scripts/np_param_map.json"
with open(PMAP_JSON) as f:
    PMAP = json.load(f)

# Column order and display labels — same as the 4D table.
NPS = [
    ("scetlibNPgammaLambda2", r"$\gamma_{\Lambda_2}$"),
    ("scetlibNPgammaLambda4", r"$\gamma_{\Lambda_4}$"),
    ("scetlibNPgammaLambdaInf", r"$\gamma_{\Lambda_\infty}$"),
    ("chargeVgenNP0scetlibNPZlambda2", r"$\Lambda_2$"),
    ("chargeVgenNP0scetlibNPZdelta_lambda2", r"$\Delta\Lambda_2$"),
    ("chargeVgenNP0scetlibNPZlambda4", r"$\Lambda_4$"),
]
POI = "pdfAlphaS"

# Pretty labels — keep aligned with the 4D table's DISPLAY_NAME conventions.
DISPLAY_NAME = {
    "nominal": "nominal",
    "unconstrained": r"unconstrained ($\tau{=}5$)",
    "inflate5x_reg5": r"inflated $\times 5$ + reg ($\tau{=}5$)",
}

# Per-config kfactors (same as the 4D table; see build_compare_table.py).
# unconstrained config has no scaleParams → all kfactors = 1.
KFACTOR_OVERRIDES = {
    "nominal": {
        "scetlibNPgammaLambda2": 2.62,
        "scetlibNPgammaLambda4": 1.12,
        "scetlibNPgammaLambdaInf": 3.33,
    },
    "unconstrained": {},
    "inflate5x_reg5": {
        "scetlibNPgammaLambda2": 13.1,
        "scetlibNPgammaLambda4": 5.60,
        "scetlibNPgammaLambdaInf": 3.33,
        "chargeVgenNP0scetlibNPZlambda2": 5.0,
        "chargeVgenNP0scetlibNPZdelta_lambda2": 5.0,
        "chargeVgenNP0scetlibNPZlambda4": 5.0,
    },
}


def get_parm(parms, name):
    names = list(parms.axes[0])
    if name not in names:
        return None, None
    i = names.index(name)
    return float(parms.values()[i]), float(np.sqrt(parms.variances()[i]))


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


def fmt_cell(theta, err, nuis, kfactor=1.0):
    if theta is None:
        return "---"
    if err == 0.0:
        return "frozen"
    v, vu = physical_shift(nuis, theta, err, kfactor=kfactor)
    return f"${v:+.4f}\\pm{vu:.4f}$"


def load_fit(path):
    fr, _ = get_fitresult(path, meta=True)
    parms = fr["parms"].get()
    out = {"path": path, "params": {}}
    for nuis, _ in NPS:
        out["params"][nuis] = get_parm(parms, nuis)
    out["alphaS"] = get_parm(parms, POI)
    # 1D saturated p-value: from the standard saturated chi² (nllvalreduced, ndfsat).
    try:
        nllv = (
            float(fr["nllvalreduced"].get())
            if hasattr(fr["nllvalreduced"], "get")
            else float(fr["nllvalreduced"][()])
        )
        ndf = (
            int(fr["ndfsat"].get())
            if hasattr(fr["ndfsat"], "get")
            else int(fr["ndfsat"][()])
        )
        out["sat_p_1d"] = chi2_dist.sf(2.0 * nllv, ndf) * 100
    except Exception:
        out["sat_p_1d"] = None
    return out


def build_one_table(obs_label, fits, ref_label):
    """Build the body lines for one observable (ptll or yll)."""
    header_np = " & ".join([lab for _, lab in NPS])
    lines = [
        rf"  \multicolumn{{{len(NPS)+4}}}{{l}}{{\textbf{{1D {obs_label}-only fits}}}} \\",
        r"  \hline",
        r"  Configuration & "
        + header_np
        + r" & Sat.\ $p$ (1D)"
        + r" & $\Delta$pull$(\alpha_S)\,[10^{-3}]$"
        + r" & $\sigma(\alpha_S)\,[10^{-3}]$ \\",
        r"  \hline",
    ]
    ref = fits[ref_label] if ref_label in fits else None
    ref_aS = (
        ref["alphaS"][0]
        if ref and ref.get("alphaS") and ref["alphaS"][0] is not None
        else None
    )
    for lab in ["nominal", "unconstrained", "inflate5x_reg5"]:
        if lab not in fits:
            continue
        d = fits[lab]
        cells = []
        koverride = KFACTOR_OVERRIDES.get(lab, {})
        for nuis, _ in NPS:
            t, e = d["params"][nuis]
            k = koverride.get(nuis, 1.0)
            cells.append(fmt_cell(t, e, nuis, kfactor=k))
        a = d.get("alphaS")
        if a == (None, None) or a is None:
            d_as = "---"
            sig_as = "---"
        else:
            d_as = (
                "ref"
                if (lab == ref_label)
                else (
                    f"${(a[0] - ref_aS)*2:+.3f}$"
                    if ref_aS is not None
                    else f"${a[0]*2:+.3f}$"
                )
            )
            sig_as = f"${a[1]*2:.3f}$"
        sp = d.get("sat_p_1d")
        sp_cell = f"${sp:.2f}\\%$" if sp is not None else "---"
        lab_tex = DISPLAY_NAME.get(lab, lab.replace("_", r"\_"))
        lines.append(
            f"  {lab_tex} & "
            + " & ".join(cells)
            + f" & {sp_cell} & {d_as} & {sig_as} \\\\"
        )
    lines.append(r"  \hline")
    return lines


def build_latex(ptll_fits, yll_fits):
    header_np = " & ".join([lab for _, lab in NPS])
    body = [
        r"\documentclass[10pt]{article}",
        r"\usepackage[a4paper,landscape,margin=1cm]{geometry}",
        r"\usepackage{graphicx}",
        r"\usepackage{booktabs}",
        r"\pagestyle{empty}",
        r"\begin{document}",
        r"\noindent\resizebox{\textwidth}{!}{%",
        r"  \begin{tabular}{l" + "c" * len(NPS) + "rrr}",
        r"    \hline\hline",
    ]
    body += build_one_table("ptll", ptll_fits, ref_label="nominal")
    body += [r"  \hline"]
    body += build_one_table("yll", yll_fits, ref_label="nominal")
    body += [
        r"    \hline\hline",
        r"  \end{tabular}%",
        r"}",
        r"\par\vspace{0.6em}",
        r"\footnotesize NP cells: postfit physical value (linearized template interp.\ from "
        r"\texttt{np\_param\_map.json}), with per-config kfactor overrides applied. "
        r"$\Delta$pull$(\alpha_S)=(\theta-\theta_{\rm nom})\times 2$ in $10^{-3}$; $\sigma(\alpha_S)$ also $\times 2$. "
        r"Each row's `Sat.\ $p$ (1D)' is the saturated chi² goodness-of-fit of the 1D distribution "
        r"the fit minimizes against (rebuilt with \texttt{setupRabbit --fitvar ptll} or \texttt{--fitvar yll}). "
        r"$\sigma(\alpha_S)$ is the postfit Hessian uncertainty.",
        r"\end{document}",
    ]
    return "\n".join(body) + "\n"


def parse_specs(specs):
    """Parse arguments of the form OBS:LABEL=path → {OBS: {LABEL: path}}."""
    out = {"ptll": {}, "yll": {}}
    for spec in specs:
        if ":" not in spec or "=" not in spec:
            raise SystemExit(f"Bad spec '{spec}'; expected OBS:LABEL=path")
        obs, rest = spec.split(":", 1)
        lab, path = rest.split("=", 1)
        if obs not in out:
            raise SystemExit(f"Unknown observable '{obs}' (expected ptll or yll)")
        out[obs][lab] = path
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "specs",
        nargs="+",
        help="OBS:LABEL=path entries; OBS in {ptll,yll}; LABEL in {nominal,unconstrained,inflate5x_reg5}",
    )
    p.add_argument("--output", "-o", required=True, help="Output directory")
    args = p.parse_args()
    specs = parse_specs(args.specs)
    fits = {"ptll": {}, "yll": {}}
    for obs, lab_paths in specs.items():
        for lab, path in lab_paths.items():
            try:
                fits[obs][lab] = load_fit(path)
            except Exception as e:
                print(f"WARNING: could not load {obs}:{lab} ({path}): {e}")
    os.makedirs(args.output, exist_ok=True)
    tex_path = os.path.join(args.output, "np_compare_1d.tex")
    with open(tex_path, "w") as fh:
        fh.write(build_latex(fits["ptll"], fits["yll"]))
    print(f"Wrote {tex_path}")
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
    print(f"Wrote {os.path.join(args.output, 'np_compare_1d.pdf')}")


if __name__ == "__main__":
    main()
