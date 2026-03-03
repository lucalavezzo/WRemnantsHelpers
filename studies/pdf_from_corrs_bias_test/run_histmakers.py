import argparse
import datetime
import os
import shlex
import subprocess

PDF_TO_THEORY_CORR = {
    "ct18z": "scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO",
    "ct18": "scetlib_dyturbo_LatticeNP_CT18_N3p0LL_N2LO",
    "herapdf20": "scetlib_dyturbo_LatticeNP_HERAPDF20_N3p0LL_N2LO",
    "msht20": "scetlib_dyturbo_LatticeNP_MSHT20_N3p0LL_N2LO",
    "msht20an3lo": "scetlib_dyturbo_LatticeNP_MSHT20aN3LO_N3p0LL_N2LO",
    "nnpdf40": "scetlib_dyturbo_LatticeNP_NNPDF40_N3p0LL_N2LO",
    "pdf4lhc21": "scetlib_dyturbo_LatticeNP_PDF4LHC21_N3p0LL_N2LO",
    "nnpdf31": "scetlib_dyturbo_LatticeNP_NNPDF31_N3p0LL_N2LO",
}
pdfs_for_bc_uncs = [
    "msht20mcrange_renorm",
    "msht20mbrange_renorm",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run histmaker in a loop over central PDFs, using a fixed "
            "PDF->theoryCorr mapping (one correction set per run)."
        )
    )
    parser.add_argument(
        "--central-pdfs",
        nargs="+",
        default=list(PDF_TO_THEORY_CORR.keys()),
        choices=list(PDF_TO_THEORY_CORR.keys()),
        help="Central PDFs to run (mapping selects theoryCorr). (Default: %(default)s)",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=450,
        help="Parallel jobs for histmaker.",
    )
    parser.add_argument(
        "--filter-procs",
        nargs="+",
        default=[],
        help="Processes to filter.",
    )
    parser.add_argument(
        "--axes",
        nargs="+",
        default=["ptll", "yll"],
        help="Axes for mz_dilepton.py.",
    )
    parser.add_argument(
        "--outdir",
        default=None,
        help=(
            "Output directory. Default: "
            "$MY_OUT_DIR/<YYMMDD>_histmaker_dilepton_pdfFromCorrBias/"
        ),
    )
    parser.add_argument(
        "--postfix-prefix",
        default="pdfFromCorrBias",
        help="Prefix used in per-run postfix names (`<prefix>_<central_pdf>`).",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=-1,
        help="Value for --maxFiles passed to mz_dilepton.py.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them.",
    )
    return parser.parse_args()


def require_env(var_name):
    value = os.environ.get(var_name)
    if not value:
        raise RuntimeError(f"{var_name} is not set. Source setup.sh first.")
    return value


def build_theory_corr_list(base_corr):
    return [base_corr, f"{base_corr}_pdfvars", f"{base_corr}_pdfas"]


def main():
    args = parse_args()

    wrem_base = require_env("WREM_BASE")
    my_out_dir = require_env("MY_OUT_DIR")
    nano_dir = os.environ.get("NANO_DIR", "/scratch/submit/cms/wmass/NanoAOD/")

    if args.outdir is None:
        tag = datetime.datetime.now().strftime("%y%m%d")
        outdir = os.path.join(
            my_out_dir, f"{tag}_histmaker_dilepton_pdfFromCorrBiasTest/"
        )
    else:
        outdir = args.outdir
    if not args.dry_run:
        os.makedirs(outdir, exist_ok=True)

    histmaker = os.path.join(wrem_base, "scripts/histmakers/mz_dilepton.py")
    print(f"Output directory: {outdir}")
    print(f"Using histmaker: {histmaker}")

    for central_pdf in args.central_pdfs:
        base_corr = PDF_TO_THEORY_CORR[central_pdf]
        corr_list = build_theory_corr_list(base_corr)
        postfix = f"{args.postfix_prefix}_{central_pdf}"
        other_pdfs = ["herapdf20ext"] if central_pdf == "herapdf20" else []

        cmd = [
            "python",
            histmaker,
            "--dataPath",
            nano_dir,
            "-o",
            outdir,
            "--maxFiles",
            str(args.max_files),
            "--axes",
            *args.axes,
            "--csVarsHist",
            "--forceDefaultName",
            "-j",
            str(args.jobs),
            "--pdfs",
            *[central_pdf, *pdfs_for_bc_uncs, *other_pdfs],
            "--theoryCorr",
            *corr_list,
            "--postfix",
            postfix,
        ]
        if args.filter_procs:
            cmd.append("--filterProcs")
            cmd.extend(args.filter_procs)

        printable = " ".join(shlex.quote(x) for x in cmd)
        print(f"\n[{central_pdf}] {printable}")
        if args.dry_run:
            continue
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
