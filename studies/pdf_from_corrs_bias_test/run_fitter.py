import argparse
import os
import shlex
import subprocess
import glob

PDF_TO_THEORY_CORR = {
    "ct18z": "scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO",
    "herapdf20": "scetlib_dyturbo_LatticeNP_HERAPDF20_N3p0LL_N2LO",
    "msht20": "scetlib_dyturbo_LatticeNP_MSHT20_N3p0LL_N2LO",
    "msht20an3lo": "scetlib_dyturbo_LatticeNP_MSHT20aN3LO_N3p0LL_N2LO",
    "nnpdf40": "scetlib_dyturbo_LatticeNP_NNPDF40_N3p0LL_N2LO",
    "pdf4lhc21": "scetlib_dyturbo_LatticeNP_PDF4LHC21_N3p0LL_N2LO",
    "nnpdf31": "scetlib_dyturbo_LatticeNP_NNPDF31_N3p0LL_N2LO",
    "ct18": "scetlib_dyturbo_LatticeNP_CT18_N3p0LL_N2LO",
}

DEFAULT_PDFS = [
    "ct18z",
    "herapdf20",
    "msht20",
    "msht20an3lo",
    "nnpdf40",
    "pdf4lhc21",
    "nnpdf31",
    "ct18",
]


def normalize_pdf(pdf):
    return pdf.lower()


def normalize_pdf_list(pdfs):
    out = []
    seen = set()
    for pdf in pdfs:
        norm = normalize_pdf(pdf)
        if norm not in PDF_TO_THEORY_CORR or norm in seen:
            continue
        out.append(norm)
        seen.add(norm)
    return out


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run fitter for split histmaker outputs, using pseudodata read from "
            "a different histfile via --pseudoDataFile."
        )
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing per-PDF histmaker outputs.",
    )
    parser.add_argument(
        "--file-pattern",
        default="mz_dilepton_pdfFromCorrBias_{pdf}.hdf5",
        help=(
            "Filename pattern used for both central and pseudodata files. "
            "Must include '{pdf}'."
        ),
    )
    parser.add_argument(
        "--central-pdfs",
        nargs="+",
        choices=sorted(PDF_TO_THEORY_CORR.keys()),
        default=DEFAULT_PDFS,
        help="Central PDF set names.",
    )
    parser.add_argument(
        "--pseudodata-pdfs",
        nargs="+",
        choices=sorted(PDF_TO_THEORY_CORR.keys()),
        default=DEFAULT_PDFS,
        help="PDF set names used to build pseudodata. Default: same as central PDFs.",
    )
    parser.add_argument(
        "--pseudodata-axis",
        default="vars",
        help="Axis used for pseudodata variation selection.",
    )
    parser.add_argument(
        "--pseudodata-idx",
        default="0",
        help="Index on --pseudodata-axis (default: 0).",
    )
    parser.add_argument(
        "--postfix",
        default=None,
        help="Optional extra postfix for output directory names.",
    )
    parser.add_argument(
        "--filter-proc-groups",
        nargs="+",
        default=["Zmumu"],
        help="Process groups passed to setupRabbit --filterProcGroups.",
    )
    parser.add_argument(
        "--asym",
        action="store_true",
        help="Enable contour scan on pdfAlphaS.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Run even if output directory already exists.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    workdir = os.environ.get("MY_WORK_DIR")
    if not workdir:
        raise RuntimeError("MY_WORK_DIR is not set. Source setup.sh first.")

    fitter = os.path.join(workdir, "workflows", "fitter.sh")
    if "{pdf}" not in args.file_pattern:
        raise ValueError("--file-pattern must include '{pdf}' placeholder.")

    central_pdfs = normalize_pdf_list(args.central_pdfs)
    pseudodata_pdfs = normalize_pdf_list(args.pseudodata_pdfs)
    if len(pseudodata_pdfs) == 0:
        print("Recieved no pseudodata PDFs, will use central PDFs as pseudodata PDFs.")
        pseudodata_pdfs = central_pdfs

    for central_pdf in central_pdfs:
        central_file = os.path.join(
            args.input_dir, args.file_pattern.format(pdf=central_pdf)
        )
        if not os.path.exists(central_file):
            print(f"[skip] Missing central file: {central_file}")
            continue

        for pseudodata_pdf in pseudodata_pdfs:
            if pseudodata_pdf == central_pdf:
                continue

            pseudodata_file = os.path.join(
                args.input_dir, args.file_pattern.format(pdf=pseudodata_pdf)
            )
            if not os.path.exists(pseudodata_file):
                print(f"[skip] Missing pseudodata file: {pseudodata_file}")
                continue

            pseudodata_hist = f"nominal_{PDF_TO_THEORY_CORR[pseudodata_pdf]}_Corr"
            out_postfix = "pdfBiasTest_Zmumu"
            if args.postfix:
                out_postfix += f"_{args.postfix}"
            out_postfix += f"_{central_pdf}_pseudo{pseudodata_pdf}"

            existing = [
                d
                for d in glob.glob(os.path.join(args.input_dir, f"*_{out_postfix}"))
                if os.path.exists(os.path.join(d, "fitresults.hdf5"))
            ]
            if existing and not args.force:
                print(f"[skip] Existing fitresults for {out_postfix}")
                continue
            if existing and args.force:
                print(f"[overwrite] Existing fitresults for {out_postfix}: {existing}")

            extra_setup_parts = [
                f"--pseudoData {pseudodata_hist}",
                f"--pseudoDataFile {pseudodata_file}",
                f"--pseudoDataAxes {args.pseudodata_axis}",
                f"--pseudoDataIdxs {args.pseudodata_idx}",
                f"--filterProcGroups {' '.join(args.filter_proc_groups)}",
                f"--postfix {out_postfix}",
            ]
            extra_fit_parts = ["--pseudoData", "-t 0", "--unblind"]
            if args.asym:
                extra_fit_parts.extend(
                    [
                        "--scan pdfAlphaS",
                        "--contourScan pdfAlphaS",
                        "-v 4",
                        "--scanRange 3.0",
                        "--scanPoints 45",
                    ]
                )

            cmd = [
                fitter,
                central_file,
                "-e",
                " ".join(extra_setup_parts),
                "-f",
                " ".join(extra_fit_parts),
            ]
            print("\n" + " ".join(shlex.quote(x) for x in cmd))
            if args.dry_run:
                continue
            subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
