#!/bin/bash
# Compare AN vs FranksVals histmaker outputs on ptll (Zmumu_2016PostVFP).
# Three plots:
#   - Nominal (vars=pdf0) -- should be ~same shape (both use real data
#     after the corr) modulo the different theory-corr file.
#   - Lambda_4 Up template (AN vars=lambda40.12 vs Frank vars=lambda41.0).
#   - Lambda_4 Down template (AN vars=lambda40.01 vs Frank vars=lambda40.0).
# The reco-level hist used is the per-process Corr histogram with axes
# [yll, ptll, cosThetaStarll_quantile, phiStarll_quantile, vars]; we
# project on ptll.
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

run() {
    local TAG="$1" AN_VARS="$2" FR_VARS="$3"
    local RRANGE="$4 $5"
    python "$MY_WORK_DIR/scripts/compare_file_hists.py" \
        --narf \
        "$AN_HM" "$FR_HM" \
        --proc Zmumu_2016PostVFP \
        --hist "$AN_HIST" "$FR_HIST" \
        --labels "AN (LatticeNPLambda4BugfixLambda6)" "FranksVals (LatticeNPLambda4Bugfix)" \
        --axes ptll \
        --selectByHist "vars $AN_VARS" "vars $FR_VARS" \
        --rrange $RRANGE \
        --binwnorm 1 \
        --postfix "$TAG" \
        -o "$OUT"
}

# Same vars label (pdf0) on both -> compare nominals
run "nominal"      pdf0       pdf0       0.85 1.15
# Lambda_4 Up: AN at physical 0.12, Frank at physical 1.0
run "Lambda4_Up"   lambda40.12  lambda41.0   0.85 1.15
# Lambda_4 Down: AN at physical 0.01, Frank at physical 0.0
run "Lambda4_Down" lambda40.01  lambda40.0   0.85 1.15

echo "Wrote plots to $OUT"
