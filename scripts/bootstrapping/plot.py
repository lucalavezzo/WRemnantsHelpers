"""
You have ran the fit with different toys, and put them in a directory, containing many subdirectories of the form:
/ZMassDilepton_toys_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toys_<toyN>_<toyN+1>/fitresults.hdf5
where toyN is the toy number.
You want to read the the fit results from all the toys, and plot them.
This is the script for you.
"""

import os
import sys
import argparse
import numpy as np
from hist import Hist
import matplotlib.pyplot as plt
import mplhep as hep
import h5py
import glob
import re
sys.path.append("../../WRemnants/")
import combinetf2.io_tools

hep.style.use("CMS")

def load_results_from_dir(
        indirs,
        fitresult_name='fitresults.hdf5',
        fitresult_result=None,
        params=['pdfAlphaS'],
        skip_toy0=False
    ):
    
    fit_values = {}
    fit_variances = {}

    # create a list of directories to process in case there are wildcards
    dirs_to_process = []
    for dir in indirs:
        if "*" in dir or "?" in dir or "[" in dir:
            matched_dirs = glob.glob(dir)
            if not matched_dirs:
                print(f"No directories matched pattern {dir}")
                continue
            dirs_to_process.extend(matched_dirs)
        else:
            dirs_to_process.append(dir)

    # Loop over all subdirectories in the input directory and read the fit results
    for subdir in dirs_to_process:

        if "toys_0" in subdir and skip_toy0:
            print(f"Skipping toy 0 in {subdir} as requested.")
            continue

        print("Reading fit results from", subdir)
        
        try:

            # Handle wildcard in fitresult_name
            if "*" in fitresult_name or "?" in fitresult_name or "[" in fitresult_name:
                pattern = os.path.join(subdir, fitresult_name)
                matched_files = glob.glob(pattern)
                if not matched_files:
                    print(f"No files matched pattern {pattern}")
                    continue
                fitresult_paths = matched_files
            else:
                fitresult_paths = [os.path.join(subdir, fitresult_name)]

            for fitresult_path in fitresult_paths:

                print(f"\tProcessing fit result file: {fitresult_path}")

                with h5py.File(fitresult_path, mode="r") as f:
                    avail_fitresult_results = list(f.keys())
              
                fitresult_results_to_process = []
                if type(fitresult_result) is str:
                    
                    # Check if fitresult_result is a regex (contains special regex characters)
                    if any(c in fitresult_result for c in ".^$*+?{}[]\\|()"):
                        regex = re.compile(fitresult_result)
                        print(regex)
                        matched = [r for r in avail_fitresult_results if regex.fullmatch(r)]
                        if not matched:
                            print(f"\t\tNo fitresult_result matched regex '{fitresult_result}' in {avail_fitresult_results}")
                        fitresult_results_to_process.extend(matched)
                    elif fitresult_result in avail_fitresult_results:
                        fitresult_results_to_process.append(fitresult_result)
                    else:
                        print(f"\t\tfitresult_result '{fitresult_result}' not found in {avail_fitresult_results}")

                else:
                    fitresult_results_to_process.append(fitresult_result)


                for fitresult_result_to_process in fitresult_results_to_process:

                    print(f"\t\tProcessing fit result: {fitresult_result_to_process}")
                    
                    fitresult, meta = combinetf2.io_tools.get_fitresult(
                        fitresult_path, result=fitresult_result_to_process.replace("results_", ""), meta=True
                    )
                    pulls = fitresult['parms'].get()
                    if params == "*":
                        params = [n for n in pulls.axes[0]]
                    for param in params:
                        if param not in fit_values:
                            fit_values[param] = np.array([])
                            fit_variances[param] = np.array([])
                        fit_values[param] = np.append(
                            fit_values[param], pulls[param].value
                        )
                        fit_variances[param] = np.append(
                            fit_variances[param], pulls[param].variance
                        )
                        if param == 'pdfAlphaS':
                            print(f"\t\t{pulls[param].value}")
                
        except Exception as e:
            print(f"Error reading fit results from {subdir}: {e}")
            continue

    return fit_values, fit_variances

def plot_alphaS_postfit(fit_values, outdir, postfix=None):

    fit_values = np.array(fit_values)

    # calculate the alphaS post-fit value from the pull
    alphaS = 0.118
    sigma_alphaS = 0.0015
    fit_values = alphaS + fit_values * sigma_alphaS

    # plot the results
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.set_xlabel(r"$\alpha_S$")
    ax.set_ylabel("Number of toys")
    h_toys = Hist.new.Reg(100, 0.115, 0.125, name="alphaS", label="$\alpha_S$").Weight()
    h_toys.fill(fit_values)
    sample_mean = np.mean(fit_values)
    sample_std_dev = np.std(fit_values, ddof=1)
    std_error_mean = sample_std_dev / np.sqrt(len(fit_values))
    std_error_std_dev = (2 * sample_std_dev**4 / (len(fit_values) - 1))**0.25
    print(f"Mean of fit values: {sample_mean}")
    print(f"Std of fit values: {sample_std_dev}")
    print(f"Standard error on mean: {std_error_mean}")
    print(f"Standard error on std dev: {std_error_std_dev}")
    hep.histplot(
        h_toys,
        ax=ax,
        label= "$\\bar{x}$ = " + \
            "{:.4f}".format(sample_mean) + \
            "\n" + \
            "Standard error on $\\bar{x}$ = " + \
            "{:.4f}".format(std_error_mean) + \
            "\n" + \
            "$\\sigma_x$ = " + \
            "{:.2e}".format(sample_std_dev) + \
            "\n" + \
            "Standard error on $\\sigma_x$ = " + \
            "{:.2e}".format(std_error_std_dev)
    )
    ax.legend(loc='upper right', fontsize='small')
    
    # save the figure
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    fig.tight_layout()
    fname = os.path.join(outdir, "pdfAlphaS_postfit")
    if postfix:
        fname += f"_{postfix}"
    print("Saving", fname)
    fig.savefig(fname + ".pdf", bbox_inches='tight')
    fig.savefig(fname + ".png", bbox_inches='tight', dpi=300)

def plot_pulls(fit_values, outdir, postfix=None, nparams=20):

    # define leading nparams parameters to plot
    fit_values = {k:v for k, v in fit_values.items() if 'pdf' in k}
    largest_pull_params = sorted(
        fit_values.keys(), key=lambda x: np.abs(np.mean(fit_values[x])), reverse=True
    )[:nparams]
    largest_mean_pulls = [np.mean(fit_values[param]) for param in largest_pull_params]
    largest_std_pulls = [np.std(fit_values[param]) for param in largest_pull_params]

    # plot them
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    ax.set_xlabel("Mean Pull over toys")
    ax.axvline(0, color='k', linestyle='--')
    ax.set_xlim(-1.2, 1.2)
    for i, param in enumerate(largest_pull_params):
        ax.errorbar(
            largest_mean_pulls[i], -i, xerr=largest_std_pulls[i], fmt='o', color='black',
            capsize=5, elinewidth=2, markeredgewidth=2
        )
    ax.set_yticks(range(-len(largest_pull_params) + 1, 1))
    ax.set_yticklabels(largest_pull_params[::-1], fontsize='xx-small')
    figname = os.path.join(outdir, "mean_pulls")
    if postfix:
        figname += f"_{postfix}"
    fig.tight_layout()
    print("Saving", figname)
    fig.savefig(figname + ".pdf", bbox_inches='tight')
    fig.savefig(figname + ".png", bbox_inches='tight', dpi=300)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--indir",
        action='append',
        required=True,
        help="Name (or grep expression) of the input directory from which to read the fitresults. Supports multiple arguments.",
    )
    parser.add_argument(
        "--fitresultName",
        type=str,
        default='fitresults.hdf5',
        help="Name (or grep expression) of the fit result file to read from each subdirectory. Default is 'fitresults.hdf5'.",
    )
    parser.add_argument(
        "--fitresultResult",
        type=str,
        default=None,
        help="Name (or grep expression) of the fit result to read from the fit result file. Default is None.",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        default="/home/submit/lavezzo/public_html/alphaS/bootstrapping/",
        help="Output directory to save the plots.",
    )
    parser.add_argument(
        "--postfix",
        type=str,
        default=None,
        help="Postfix to add to the output file names. If not specified, no postfix will be added."
    )
    parser.add_argument(
        "-p",
        "--pulls",
        action='store_true',
        help="Plot mean pull over toys"
    )
    parser.add_argument(
        "--noAlphaSHist",
        action='store_true',
        help="Do not plot the alphaS histogram"
    )
    parser.add_argument(
        "--skipToy0",
        action='store_true',
        help="Skip toy 0 in the fit results. This is useful if you want to skip the first toy, which is usually the non-randomized toy."
    )
    args = parser.parse_args()

    if not args.noAlphaSHist:

        fit_values, fit_variances = load_results_from_dir(
            indirs=args.indir,
            fitresult_name=args.fitresultName,
            fitresult_result=args.fitresultResult,
            params=["pdfAlphaS"],
            skip_toy0=args.skipToy0
        )

        plot_alphaS_postfit(fit_values['pdfAlphaS'], args.outdir, args.postfix)
        
    if args.pulls:

        fit_values, fit_variances = load_results_from_dir(
            indirs=args.indir,
            fitresult_name=args.fitresultName,
            fitresult_result=args.fitresultResult,
            params="*"
        )

        plot_pulls(fit_values, args.outdir, args.postfix, nparams=20)

    
if __name__ == "__main__":
    main()