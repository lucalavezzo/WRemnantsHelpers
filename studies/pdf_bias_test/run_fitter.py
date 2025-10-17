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
    "msht20an3lo",
]

DEFAULT_PSEUDODATA_PDFS = [
    "ct18",
    "ct18z",
    "nnpdf30",
    "nnpdf40",
    "pdf4lhc21",
    "msht20",
    "msht20an3lo",
]

def get_pdf_map_name(pdf_key: str) -> str:
    info = theory_tools.pdfMap.get(pdf_key)
    if info:
        return info["name"]
    return f"pdf{pdf_key.upper()}"

def parse_args():
    parser = argparse.ArgumentParser(description="Run fitter workflow over a set of PDFs.")
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing mz_dilepton_<pdf>.hdf5 inputs.",
    )
    parser.add_argument(
        "--central-pdfs",
        nargs="+",
        default=DEFAULT_CENTRAL_PDFS,
        help="PDF set names to use as central inputs.",
    )
    parser.add_argument(
        "--pseudodata-pdfs",
        nargs="+",
        default=DEFAULT_PSEUDODATA_PDFS,
        help="PDF set names to use for pseudo-data.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    for pdf_central in args.central_pdfs:
        input_file = f"{args.input_dir}/mz_dilepton_{pdf_central}.hdf5"
        pseudo_data_args = " ".join(
            ["nominal_" + get_pdf_map_name(p) + "UncertByHelicity" for p in args.pseudodata_pdfs]
        )

        extra_setup = (
            f"--pseudoData {pseudo_data_args} "
            f"--postfix pdfBiasTest_Zmumu_{pdf_central} "
            f"--pseudoDataIdxs 0 --pseudoDataAxes pdfVar --filterProcGroups Zmumu"
        )
        extra_fit = "--pseudoData -t 0 --unblind"
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
