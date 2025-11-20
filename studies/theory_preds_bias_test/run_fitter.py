import argparse
import os

from wremnants import theory_tools

DEFAULT_CENTRAL_PREDS = [
    "scetlib_dyturbo",
    "scetlib_dyturboMSHT20",
    "scetlib_dyturboN3p1LL",
    "scetlib_dyturboN4p0LL",
    "scetlib_nnlojetN3p1LLN3LO",
    "scetlib_nnlojetN4p0LLN3LO",
]
DEFAULT_PSEUDODATA_PREDS = [
    "scetlib_dyturbo",
    "scetlib_dyturboMSHT20",
    "scetlib_dyturboN3p1LL",
    "scetlib_dyturboN4p0LL",
    "scetlib_nnlojetN3p1LLN3LO",
    "scetlib_nnlojetN4p0LLN3LO",
]


def get_pred_map_name(pred_key: str) -> str:
    info = theory_tools.predMap.get(pred_key)
    if info:
        return info["name"]
    return f"pred{pred_key.upper()}"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run fitter workflow over a set of preds."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing mz_dilepton_<pred>.hdf5 inputs.",
    )
    parser.add_argument(
        "--postfix",
        default=None,
        help="Postfix for output sub-directory.",
    )
    parser.add_argument(
        "--central-preds",
        nargs="+",
        default=DEFAULT_CENTRAL_PREDS,
        help="PDF set names to use as central inputs. (default: %(default)s)",
    )
    parser.add_argument(
        "--pseudodata-preds",
        nargs="+",
        default=DEFAULT_PSEUDODATA_PREDS,
        help="PDF set names to use for pseudo-data. (default: %(default)s)",
    )
    parser.add_argument(
        "--asym",
        action="store_true",
        help="For use with asymmetric uncertainties. Performs a contour scan on predAlphaS.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    for pred_central in args.central_preds:
        input_file = f"{args.input_dir}/mz_dilepton_{pred_central}.hdf5"
        pseudo_data_args = " ".join(
            [
                "nominal_" + p + "Corr"
                for p in args.pseudodata_preds
            ]
        )

        postfix = f"predBiasTest_Zmumu"
        if args.postfix:
            postfix += f"_{args.postfix}"
        postfix += f"_{pred_central}"
        extra_setup = (
            f"--pseudoData {pseudo_data_args} --pseudoDataIdxs 0 --pseudoDataAxes vars "
            f"--filterProcGroups Zmumu "
            f"--postfix {postfix} "
        )
        extra_fit = "--pseudoData -t 0 --unblind "
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
