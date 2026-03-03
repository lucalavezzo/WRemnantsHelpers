import argparse
import os
import re
import shlex
import subprocess

PDF_TO_THEORY_CORR = {
    "ct18z": "scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO",
    "herapdf20": "scetlib_dyturbo_LatticeNP_HERAPDF20_N3p0LL_N2LO",
    "msht20": "scetlib_dyturbo_LatticeNP_MSHT20_N3p0LL_N2LO",
    "msht20an3lo": "scetlib_dyturbo_LatticeNP_MSHT20aN3LO_N3p0LL_N2LO",
    "nnpdf40": "scetlib_dyturbo_LatticeNP_NNPDF40_N3p0LL_N2LO",
    "pdf4lhc21": "scetlib_dyturbo_LatticeNP_PDF4LHC21_N3p0LL_N2LO",
    "nnpdf31": "scetlib_dyturbo_LatticeNP_NNPDF31_N3p0LL_N2LO",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Thin convenience wrapper around rabbit_plot_hists.py for a single "
            "fitresults.hdf5 file."
        )
    )
    parser.add_argument("fitresult_file", help="Path to fitresults.hdf5")
    parser.add_argument(
        "--result",
        default=None,
        help="Result key. If omitted, infer from pseudodata PDF in directory name.",
    )
    parser.add_argument(
        "--mapping",
        nargs="+",
        default=["Project", "ch0", "ptll"],
        help="Mapping arguments passed after -m.",
    )
    parser.add_argument("--outdir", required=True, help="Output directory.")
    parser.add_argument("--postfix", default="", help="Output postfix.")
    parser.add_argument("--title", default="CMS")
    parser.add_argument("--subtitle", default="Preliminary")
    parser.add_argument("--rrange", nargs=2, type=float, default=[0.95, 1.05])
    parser.add_argument(
        "--data-name",
        default="auto",
        help="Data label. 'auto' -> 'Pseudodata (<pdf>)' when inferable.",
    )
    parser.add_argument(
        "--uncertainty-label",
        default="Total unc.",
        help="Label for the uncertainty band.",
    )
    parser.add_argument("--varNames", nargs="*", default=None)
    parser.add_argument("--varLabels", nargs="*", default=None)
    parser.add_argument("--varColors", nargs="*", default=None)
    parser.add_argument("--varGroupNames", nargs="*", default=None)
    parser.add_argument("--varGroupLabels", nargs="*", default=None)
    parser.add_argument("--varGroupColors", nargs="*", default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def infer_pair_from_path(path):
    directory = os.path.basename(os.path.dirname(os.path.abspath(path)))
    match = re.search(r"_([a-z0-9]+)_pseudo([a-z0-9]+)$", directory)
    if not match:
        return None, None
    central, pseudo = match.group(1), match.group(2)
    if central not in PDF_TO_THEORY_CORR or pseudo not in PDF_TO_THEORY_CORR:
        return None, None
    return central, pseudo


def infer_result_name(pseudo_pdf):
    return f"nominal_{PDF_TO_THEORY_CORR[pseudo_pdf]}_Corr_vars"


def main():
    args = parse_args()
    if not os.path.exists(args.fitresult_file):
        raise FileNotFoundError(args.fitresult_file)

    _, pseudo_pdf = infer_pair_from_path(args.fitresult_file)
    result_name = args.result or (
        infer_result_name(pseudo_pdf) if pseudo_pdf is not None else None
    )
    if result_name is None:
        raise RuntimeError(
            "Could not infer --result from path; please pass --result explicitly."
        )

    if args.data_name == "auto":
        data_name = (
            f"Pseudodata ({pseudo_pdf})" if pseudo_pdf is not None else "Pseudodata"
        )
    else:
        data_name = args.data_name

    cmd = [
        "rabbit_plot_hists.py",
        args.fitresult_file,
        "--prefit",
        "--result",
        result_name,
        "--dataHist",
        "nobs",
        "--dataName",
        data_name,
        "-m",
        *args.mapping,
        "-o",
        args.outdir,
        "--title",
        args.title,
        "--subtitle",
        args.subtitle,
        "--legCols",
        "1",
        "--rrange",
        str(args.rrange[0]),
        str(args.rrange[1]),
        "--upperPanelUncertaintyBand",
        "--uncertaintyLabel",
        args.uncertainty_label,
    ]
    if args.postfix:
        cmd.extend(["-p", args.postfix])
    if args.varNames:
        cmd.extend(["--varNames", *args.varNames])
    if args.varLabels:
        cmd.extend(["--varLabels", *args.varLabels])
    if args.varColors:
        cmd.extend(["--varColors", *args.varColors])
    if args.varGroupNames:
        cmd.extend(["--varGroupNames", *args.varGroupNames])
    if args.varGroupLabels:
        cmd.extend(["--varGroupLabels", *args.varGroupLabels])
    if args.varGroupColors:
        cmd.extend(["--varGroupColors", *args.varGroupColors])

    print("Running:\n" + " ".join(shlex.quote(x) for x in cmd))
    if not args.dry_run:
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
