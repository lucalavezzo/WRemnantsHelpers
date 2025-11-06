import argparse
import os

from wremnants import theory_tools

DEFAULT_CENTRAL_PREDS = [
    "scetlib_dyturboCT18Z_pdfasCorr",
    "scetlib_dyturboMSHT20_pdfasCorr",
    "scetlib_dyturboN3p1LL_pdfasCorr",
    "scetlib_dyturboN4p0LL_pdfasCorr",
    "scetlib_nnlojetN3p1LLN3LO_pdfasCorr",
    "scetlib_nnlojetN4p0LLN3LO_pdfasCorr",
]
DEFAULT_PSEUDODATA_PREDS = [
    "scetlib_dyturboCT18Z_pdfasCorr",
    "scetlib_dyturboMSHT20_pdfasCorr",
    "scetlib_dyturboN3p1LL_pdfasCorr",
    "scetlib_dyturboN4p0LL_pdfasCorr",
    "scetlib_nnlojetN3p1LLN3LO_pdfasCorr",
    "scetlib_nnlojetN4p0LLN3LO_pdfasCorr",
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
        help="PDF set names to use as central inputs.",
    )
    parser.add_argument(
        "--pseudodata-preds",
        nargs="+",
        default=DEFAULT_PSEUDODATA_PREDS,
        help="PDF set names to use for pseudo-data.",
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
            ["nominal_" + p + "ByHelicity" for p in args.pseudodata_preds]
        )

        postfix = f"predBiasTest_Zmumu"
        if args.postfix:
            postfix += f"_{args.postfix}"
        postfix += f"_{pred_central}"
        extra_setup = (
            f"--alphaSTheoryCorr {pred_central} "
            f"--pseudoData {pseudo_data_args} --pseudoDataIdxs 0 --pseudoDataAxes vars "
            f"--filterProcGroups Zmumu "
            f"--postfix {postfix} "
            f"--noi alphaS "
            f"--select 'ptll 0j 20j'"
        )
        extra_fit = "--pseudoData -t 0 --unblind "
        if args.asym:
            extra_fit += "--scan predAlphaS --contourScan predAlphaS -v 4 --scanRange 3.0 --scanPoints 45 "

        setup_command = f"python /home/submit/lavezzo/alphaS/kenneth/WRemnants/scripts/rabbit/setupRabbit.py -i {input_file} --fitvar ptll-yll-cosThetaStarll_quantile-phiStarll_quantile -o {os.path.dirname(input_file)} --noi alphaS {extra_setup}"
        carrot = (
            os.path.dirname(input_file)
            + f"/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_{postfix}/ZMassDilepton.hdf5"
        )
        fit_command = f"rabbit_fit.py {carrot} --computeVariations -m Project ch0 ptll --computeHistErrors --doImpacts -o {os.path.dirname(carrot)} --globalImpacts --saveHists --saveHistsPerProcess {extra_fit}"
        try:
            print(setup_command)
            os.system(setup_command)
            print(fit_command)
            os.system(fit_command)
        except Exception as e:
            print(f"Error running command: {fit_command}\n{e}")


if __name__ == "__main__":
    main()
