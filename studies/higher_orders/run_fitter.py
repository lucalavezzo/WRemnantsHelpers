import argparse
import os

DEFAULT_CENTRAL_PREDS = [
    "scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO",
    "scetlib_dyturbo_LatticeNP_CT18Z_N2p1LL_N2LO",
    "scetlib_dyturbo_LatticeNP_CT18Z_N4p0LL_N2LO",
    "scetlib_dyturbo_LatticeNP_CT18Z_N3p1LL_N2LO",
    # "scetlib_nnlojetN3p1LLN3LO",
    # "scetlib_nnlojetN4p0LLN3LO",
]


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
        "--asym",
        action="store_true",
        help="For use with asymmetric uncertainties. Performs a contour scan on predAlphaS.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    for pred_central in args.central_preds:
        print(f"Processing {pred_central}")
        input_file = (
            f"{args.input_dir}/mz_dilepton_{pred_central}_Corr_maxFiles_m1.hdf5"
        )

        postfix = f""
        if args.postfix:
            postfix += f"_{args.postfix}"
        postfix += f"{pred_central}"
        extra_setup = f"--postfix {postfix} "
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
        print(f"Finished processing {pred_central}\n")
        print()

    print("All done!")


if __name__ == "__main__":
    main()
