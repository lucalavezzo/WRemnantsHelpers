import argparse
import os

from wremnants import theory_tools

DEFAULT_CENTRAL_PDFS = [
    "ct18",
    "ct18z",
    "nnpdf31",
    "nnpdf40",
    "pdf4lhc21",
    "msht20",
    "herapdf20",
]


def get_pdf_map_name(pdf_key: str) -> str:
    info = theory_tools.pdfMap.get(pdf_key)
    if info:
        return info["name"]
    return f"pdf{pdf_key.upper()}"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run fitter workflow over a set of PDFs."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing mz_dilepton_<pdf>.hdf5 inputs.",
    )
    parser.add_argument(
        "--postfix",
        default=None,
        help="Postfix for output sub-directory.",
    )
    parser.add_argument(
        "--central-pdfs",
        nargs="+",
        choices=DEFAULT_CENTRAL_PDFS,
        default=DEFAULT_CENTRAL_PDFS,
        help="PDF set names to use as central inputs.",
    )
    parser.add_argument(
        "--asym",
        action="store_true",
        help="For use with asymmetric uncertainties. Performs a contour scan on pdfAlphaS.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    for pdf_central in args.central_pdfs:
        input_file = f"{args.input_dir}/mz_dilepton_{pdf_central}.hdf5"

        postfix = f"Zmumu"
        if args.postfix:
            postfix += f"_{args.postfix}"
        postfix += f"_{pdf_central}"
        extra_setup = f"--filterProcGroups Zmumu " f"--postfix {postfix} "
        extra_fit = ""
        if args.asym:
            extra_fit += "--scan pdfAlphaS --contourScan pdfAlphaS -v 4 --scanRange 3.0 --scanPoints 45 "
        fit_command = (
            f"{os.environ['MY_WORK_DIR']}/workflows/fitter.sh "
            f"{input_file} -e '{extra_setup}' -f '{extra_fit}'"
        )
        try:
            os.system(fit_command)
        except Exception as e:
            print(f"Error running command: {fit_command}\n{e}")


if __name__ == "__main__":
    main()
