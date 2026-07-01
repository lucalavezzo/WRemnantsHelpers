#!/bin/bash
# Plot FranksVals lambda template variations on the FIT axis (ptll),
# from the reco-level histogram (NOT gen-level): each NP variation has
# the corr weight applied to the actual reco ptll spectrum, so this
# shows the asymmetry on the observable that goes into the fit.
#
# Histogram used:
#   nominal_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr
#   axes = [yll, ptll, cosThetaStarll_quantile, phiStarll_quantile, vars]
# We --axes ptll to project, --selectByHist 'vars <label>' to pick the
# nominal / Up / Down templates per variation pair.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

INFILE="/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Theorymodels/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"
HIST="nominal_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr"
PROC="Zmumu_2016PostVFP"
OUT="$MY_PLOT_DIR/260519_franks_vals_lambda_templates"

mkdir -p "$OUT"

# Caller can override the ratio panel range, default is tight.
RLO="${1:-0.97}"
RHI="${2:-1.03}"

plot_pair() {
    local TAG="$1" UP_LBL="$2" DN_LBL="$3"
    python "$MY_WORK_DIR/scripts/plot_narf_hists.py" "$INFILE" \
        --filterProcs "$PROC" \
        --hists "$HIST" "$HIST" "$HIST" \
        --labels "nominal" "Up: ${UP_LBL}" "Down: ${DN_LBL}" \
        --selectByHist "vars pdf0" "vars ${UP_LBL}" "vars ${DN_LBL}" \
        --axes ptll \
        --rrange "$RLO" "$RHI" \
        --xlabel "ptll [GeV]" \
        --outname "lambda_template_${TAG}" \
        -o "$OUT"
}

# Asymmetric pairs (FranksVals: +0.6/-0.4 around 0.4 for TMD).
plot_pair "TMD_Lambda2"  lambda21.0           lambda20.0
plot_pair "TMD_Lambda4"  lambda41.0           lambda40.0
# Symmetric pairs.
plot_pair "CS_lambda2"   lambda2_nu0.25       lambda2_nu0.05
plot_pair "TMD_dLambda2" delta_lambda20.02   delta_lambda2-0.02

echo "Wrote plots to $OUT  (rrange=$RLO $RHI)"
