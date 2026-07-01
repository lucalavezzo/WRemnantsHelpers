#!/bin/bash
# Within-histmaker ratio comparison: for each of AN and FranksVals,
# overlay nominal + Lambda_4 Up + Lambda_4 Down on ptll (Zmumu).  This
# shows directly how big each histmaker's Lambda_4 template excursion
# is, with ratios in the bottom panel relative to that histmaker's
# nominal.  If the AN excursion is ~1% but Frank's is ~10%, the
# label-scale difference is real shape strength.  If both excursions
# are the same size, the labels are misleading and the templates are
# nearly equivalent.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

AN_HM=/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5
FR_HM=/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Theorymodels/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5
AN_HIST=nominal_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr
FR_HIST=nominal_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr

OUT="$MY_PLOT_DIR/260520_AN_vs_franks_ptll"
mkdir -p "$OUT"

# AN within: nominal (ref) vs Lambda_4 Up vs Lambda_4 Down
python "$MY_WORK_DIR/scripts/plot_narf_hists.py" "$AN_HM" \
    --filterProcs Zmumu_2016PostVFP \
    --hists "$AN_HIST" "$AN_HIST" "$AN_HIST" \
    --labels "AN: nominal" "AN: Lambda_4 Up (0.12)" "AN: Lambda_4 Down (0.01)" \
    --selectByHist "vars pdf0" "vars lambda40.12" "vars lambda40.01" \
    --axes ptll \
    --rrange 0.97 1.03 \
    --xlabel "ptll [GeV]" \
    --outname "AN_within_Lambda4" \
    -o "$OUT"

# FranksVals within: nominal (ref) vs Lambda_4 Up vs Lambda_4 Down
python "$MY_WORK_DIR/scripts/plot_narf_hists.py" "$FR_HM" \
    --filterProcs Zmumu_2016PostVFP \
    --hists "$FR_HIST" "$FR_HIST" "$FR_HIST" \
    --labels "Frank: nominal" "Frank: Lambda_4 Up (1.0)" "Frank: Lambda_4 Down (0.0)" \
    --selectByHist "vars pdf0" "vars lambda41.0" "vars lambda40.0" \
    --axes ptll \
    --rrange 0.97 1.03 \
    --xlabel "ptll [GeV]" \
    --outname "Franks_within_Lambda4" \
    -o "$OUT"

echo "Wrote $OUT/{AN_within_Lambda4,Franks_within_Lambda4}.{pdf,png}"
