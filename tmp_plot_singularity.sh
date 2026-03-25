#!/usr/bin/env bash
set -euo pipefail
cd /home/submit/lavezzo/alphaS/main/WRemnants
export PYTHONPATH="${PYTHONPATH:-}"
source setup.sh
/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_plot_hists.py /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260303_histmaker_dilepton_unfolding/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5 -m 'Project ch0 ptll' --prefit --config /home/submit/lavezzo/alphaS/main/WRemnants/wremnants/utilities/styles/styles.py --title CMS --titlePos 0 -o /home/submit/lavezzo/public_html/alphaS/260304_AN_Figures/Figures/uncertainties/ --processGrouping z_dilepton --rrange 0.88 1.12 --varNames pdf22CT18ZSymAvg pdf4CT18ZSymDiff pdf26CT18ZSymDiff --varLabels 'CT18Z 22 (Avg.)' 'CT18Z 4 (Diff.)' 'CT18Z 26 (Diff.)' --yscale 1.25 --noExtraText --subtitle Preliminary --lowerLegPos 'upper right' --noData --postfix pdfs --showVariations both
