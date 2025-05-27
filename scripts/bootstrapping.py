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
sys.path.append("../../WRemnants/")
import combinetf2.io_tools

parser = argparse.ArgumentParser()
parser.add_argument(
    "indir",
    type=str,
    help="Input directory containing 'ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toys_<toyN>_<toyN+1>/fitresults.hdf5' which we want to read.",
)
parser.add_argument(
    "-o",
    "--outdir",
    type=str,
    default="/home/submit/lavezzo/public_html/alphaS/bootstrapping/",
    help="Output directory to save the plots.",
)
args = parser.parse_args()

def load_results_from_dir(indir, grep, fitresult_name='fitresults.hdf5'):
    alphaS = 0.118
    sigma_alphaS = 0.002
    input_dir = indir
    fit_values = [] # list to store the fit values

    # Loop over all subdirectories in the input directory and read the fit results
    for subdir in os.listdir(input_dir):
        #print(f"Subdir: {subdir}")
        if not subdir.startswith(grep):
            continue
        print(f"Reading fit results from {subdir}")
        try:
            subdir_path = os.path.join(input_dir, subdir)
            fitresult_path = os.path.join(subdir_path, fitresult_name)
            fitresult, meta = combinetf2.io_tools.get_fitresult(
                fitresult_path, result=None, meta=True
            )
            #print(f"Fit result: {fitresult}")
            pull = fitresult['parms'].get()['pdfAlphaS'].value
            fit_value = alphaS + pull * sigma_alphaS
            fit_values.append(fit_value)
        except Exception as e:
            print(f"Error reading fit results from {subdir}: {e}")
            continue
    return fit_values

def plot_fit_results(fit_values, ax):

    # plot the results
    h_toys = Hist.new.Reg(100, 0.115, 0.125, name="alphaS", label="$\alpha_S$").Weight()
    h_toys.fill(fit_values)
    sample_mean = np.mean(fit_values)
    sample_std_dev = np.std(fit_values, ddof=1)
    print(f"Mean of fit values: {sample_mean}")
    print(f"Std of fit values: {sample_std_dev}")
    hep.histplot(h_toys, ax=ax, label=r"Mean: {:.4f} $\pm$ {:.4f}".format(sample_mean, sample_std_dev))

fig, ax = plt.subplots(1, 1, figsize=(10, 6))
ax.set_xlabel(r"$\alpha_S$")
ax.set_ylabel("Number of toys")

fit_values = load_results_from_dir(
    args.indir, 
    grep="ZMassDilepton_ptVGen_absYVGen_helicitySig_seed", 
    fitresult_name='fitresults.hdf5'
)

plot_fit_results(fit_values, ax)
ax.legend(loc='upper right')
if not os.path.exists(args.outdir):
    os.makedirs(args.outdir)
fig.tight_layout()
fig.savefig(os.path.join(args.outdir, "250525_toys_unfolding_toy0.pdf"), bbox_inches='tight')
fig.savefig(os.path.join(args.outdir, "250525_toys_unfolding_toy0.png"), bbox_inches='tight', dpi=300)
