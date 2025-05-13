"""
You have ran the fit with different toys, and put them in a directory,
/ZMassDilepton_toys_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toys_<toyN>_<toyN+1>/fitresults.hdf5
where toyN is the toy number.
You want to read the the fit results from all the toys, and plot them.
This is the script for you.
"""

import os
import sys
import argparse
from hist import Hist
import matplotlib.pyplot as plt
import mplhep as hep
sys.path.append("../../WRemnants/")
import combinetf2.io_tools

parser = argparse.ArgumentParser()
parser.add_argument(
    "indir",
    type=str,
    help="Input directory containing 'ZMassDilepton_toys_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toys_<toyN>_<toyN+1>/fitresults.hdf5' which we want to read.",
)
parser.add_argument(
    "--result",
    default=None,
    type=str,
    help="fitresults key in file (e.g. 'asimov'). Leave empty for data fit result.",
)
args = parser.parse_args()

alphaS = 0.118
sigma_alphaS = 0.002
input_dir = args.indir
fit_values = [] # list to store the fit values

# Loop over all subdirectories in the input directory and read the fit results
for subdir in os.listdir(input_dir):
    if not subdir.startswith("ZMassDilepton_toys_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toys_"):
        continue
    subdir_path = os.path.join(input_dir, subdir)
    fitresult_path = os.path.join(subdir_path, "fitresults.hdf5")
    fitresult, meta = combinetf2.io_tools.get_fitresult(
        args.infile, result=args.result, meta=True
    )
    pull = fitresult['parms'].get()['pdfAlphaS'].value
    fit_value = alphaS + pull * sigma_alphaS
    fit_values.append(fit_value)

h_toys = Hist.new.Reg(100, 0.1, 0.3, name="alphaS", label="$\alpha_S$").Weight()
h_toys.fill(fit_values)
fig, axs = plt.subplots(1, 1, figsize=(10, 6))