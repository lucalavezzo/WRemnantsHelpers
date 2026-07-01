"""Postfit-NP table for the NewVarsCT18ZLambda6 + LatticeNoConstraintsFranksLambda4Neg
fit (tanh_6, CT18ZNNLO, asymmetric Lambda_4 to -0.4). Reuses the franks build_compare
machinery for the 4 floating nuisances, and adds a footer listing the fixed tanh_6
NP parameters so the reader sees the full setup at a glance.

Usage:
    python build_table_lambda4neg.py LABEL=path/to/fitresults.hdf5 [...] --mode physical -o OUTDIR
"""

import argparse, json, os, sys, subprocess
import numpy as np

sys.path.insert(
    0, "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/franks-vals-fit/scripts"
)
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")

from rabbit.io_tools import get_fitresult
from scipy.stats import chi2 as chi2_dist

PMAP_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "np_param_map_lambda4neg.json"
)
with open(PMAP_JSON) as f:
    PMAP = json.load(f)

# Column order and display labels. tanh_6 + asym-Lambda4: 4 floating NPs.
NPS = [
    ("scetlibNPgammaLambda2", r"$\gamma_{\Lambda_2}$"),
    ("chargeVgenNP0scetlibNPZlambda2", r"$\Lambda_2$"),
    ("chargeVgenNP0scetlibNPZdelta_lambda2", r"$\Delta\Lambda_2$"),
    ("chargeVgenNP0scetlibNPZlambda4", r"$\Lambda_4$"),
]

POI = "pdfAlphaS"

DISPLAY_NAME = {
    "prefit": r"prefit (tanh\_6 + asym $\Lambda_4$)",
    "nominal": r"nominal (avg sym)",
}


def physical_postfit(info, theta, sigma_theta):
    """param(theta) and its local sigma."""
    nominal = info["nominal"]
    d_up = info["Up_template_value"] - nominal
    d_dn = nominal - info["Down_template_value"]
    if theta >= 0:
        param = nominal + theta * d_up
        slope = d_up
    else:
        param = nominal + theta * d_dn  # theta<0, d_dn > 0 -> param decreases
        slope = d_dn
    sigma_param = abs(slope) * sigma_theta
    return param, sigma_param


def fmt_pm(val, sig, digits=4):
    return f"${val:+.{digits}f}\\pm{sig:.{digits}f}$"


def fmt_asym(nominal, d_up, d_dn, digits=4):
    return f"${nominal:+.{digits}f}^{{+{d_up:.{digits}f}}}_{{-{d_dn:.{digits}f}}}$"


def load_fit(path):
    """Return dict with thetas (postfit), theta_sigmas, alphaS pull info, sat-pval."""
    fr, _meta = get_fitresult(path, meta=True)
    parms = fr["parms"].get()
    out = {}
    pulls, errs = parms.values(), np.sqrt(parms.variances())
    names = list(parms.axes[0])
    for k in [n[0] for n in NPS] + [POI]:
        if k in names:
            i = names.index(k)
            out[k] = (float(pulls[i]), float(errs[i]))
    # Saturated chi2 p-value for the ptll projection, if present
    sat_p = None
    if "chi2" in fr:
        try:
            chi2_node = fr["chi2"].get()
            # chi2 layout varies; just try to grab a scalar
            sat_p = float(chi2_node)  # not robust — placeholder
        except Exception:
            pass
    out["__sat_p__"] = sat_p
    return out


def build_latex(fits, mode):
    """fits: ordered list of (label, fitdict)."""
    # Header
    header = (
        ["Configuration"]
        + [n[1] for n in NPS]
        + [
            r"$\sigma(\alpha_S)\,[10^{-3}]$",
            r"$\Delta$pull$(\alpha_S)\,[10^{-3}]$",
        ]
    )
    colspec = "l" + "c" * len(NPS) + "rr"

    rows = []
    # prefit row
    pre_cells = ["prefit (tanh\\_6 + asym $\\Lambda_4$)"]
    for k, _label in NPS:
        info = PMAP["nuisances"][k]
        nominal = info["nominal"]
        d_up = info["Up_template_value"] - nominal
        d_dn = nominal - info["Down_template_value"]
        if abs(d_up - d_dn) < 1e-6:
            pre_cells.append(fmt_pm(nominal, d_up))
        else:
            pre_cells.append(fmt_asym(nominal, d_up, d_dn))
    pre_cells += ["---", "---"]
    rows.append(" & ".join(pre_cells) + r" \\")

    # Reference alphaS pull (first fit) for delta-pull column
    ref_alphaS = fits[0][1].get(POI, (None, None))[0]

    # data rows
    for label, fd in fits:
        cells = [DISPLAY_NAME.get(label, label.replace("_", "\\_"))]
        for k, _ in NPS:
            theta, sigma = fd.get(k, (None, None))
            if theta is None:
                cells.append("---")
                continue
            if mode == "physical":
                info = PMAP["nuisances"][k]
                val, sig = physical_postfit(info, theta, sigma)
                cells.append(fmt_pm(val, sig))
            else:
                cells.append(f"${theta:+.3f}\\pm{sigma:.3f}$")
        alphaS = fd.get(POI, (None, None))
        if alphaS[0] is None:
            cells += ["---", "---"]
        else:
            theta_aS, sigma_aS = alphaS
            cells.append(f"${sigma_aS*2:.3f}$")  # sigma_AN convention factor 2
            if ref_alphaS is None or label == fits[0][0]:
                cells.append("ref")
            else:
                cells.append(f"${(theta_aS - ref_alphaS)*2:+.3f}$")
        rows.append(" & ".join(cells) + r" \\")

    # Fixed-parameters footer block
    fixed = PMAP.get("fixed_parameters", {})
    fixed_lines = []
    for k, v in fixed.items():
        side = v.get("side", "?")
        name = v.get("param_AN", k).replace("_", r"\_")
        fixed_lines.append(f"${name}$ ({side}) $= {v['value']}$")
    fixed_footer = "; ".join(fixed_lines)

    tex = []
    tex.append(r"\documentclass[10pt]{article}")
    tex.append(r"\usepackage[a4paper,landscape,margin=1cm]{geometry}")
    tex.append(r"\usepackage{graphicx}")
    tex.append(r"\usepackage{booktabs}")
    tex.append(r"\pagestyle{empty}")
    tex.append(r"\begin{document}")
    tex.append(r"\noindent\resizebox{\textwidth}{!}{%")
    tex.append(r"  \begin{tabular}{" + colspec + "}")
    tex.append(r"    \hline\hline")
    tex.append("    " + " & ".join(header) + r" \\")
    tex.append(r"    \hline")
    for r in rows:
        tex.append("    " + r)
    tex.append(r"    \hline\hline")
    tex.append(r"  \end{tabular}%")
    tex.append(r"}")
    tex.append(r"\par\vspace{0.5em}")
    tex.append(
        r"\footnotesize\textbf{NP model:} \texttt{LatticeNoConstraintsFranksLambda4Neg} "
        r"(tanh\_6 both sides, asymmetric $\Lambda_4$ Down = explicit \texttt{lambda4-0.4} SCETlib template). "
        r"NP cells: postfit physical value (linearized from \texttt{np\_param\_map\_lambda4neg.json}). "
        r"$\sigma(\alpha_S)$ in $10^{-3}$ = Hessian $\sigma_\theta \times 2$. "
        r"$\Delta$pull$(\alpha_S)$ = $(\theta - \theta_{\rm ref}) \times 2$ in $10^{-3}$. "
        r"All rows are real-data fits ($-t\,0$); $\alpha_S$ POI stays blinded."
    )
    tex.append(r"\par\vspace{0.4em}")
    tex.append(
        r"\footnotesize\textbf{Fixed NP parameters (tanh\_6 setup):} "
        + fixed_footer
        + r"."
    )
    tex.append(r"\end{document}")
    return "\n".join(tex)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("specs", nargs="+", help="LABEL=path entries")
    p.add_argument("--mode", choices=["physical", "theta"], default="physical")
    p.add_argument("--output", "-o", required=True)
    args = p.parse_args()

    fits = []
    for spec in args.specs:
        if "=" not in spec:
            print(f"WARN: bad spec '{spec}', skipping")
            continue
        label, path = spec.split("=", 1)
        if not os.path.isfile(path):
            print(f"WARN: missing {path} for {label}, skipping")
            continue
        fits.append((label, load_fit(path)))

    if not fits:
        print("No fits loaded.")
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    suffix = "" if args.mode == "physical" else f"_{args.mode}"
    tex_path = os.path.join(args.output, f"np_table_lambda4neg{suffix}.tex")
    with open(tex_path, "w") as fh:
        fh.write(build_latex(fits, args.mode))
    print(f"Wrote {tex_path}")

    # try pdflatex
    try:
        subprocess.run(
            [
                "pdflatex",
                "-interaction=batchmode",
                "-output-directory",
                args.output,
                tex_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pdf_path = tex_path.replace(".tex", ".pdf")
        print(f"Wrote {pdf_path}")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(
            f"pdflatex not run inside container; compile on host: "
            f"pdflatex -interaction=batchmode -output-directory {args.output} {tex_path}"
        )


if __name__ == "__main__":
    main()
