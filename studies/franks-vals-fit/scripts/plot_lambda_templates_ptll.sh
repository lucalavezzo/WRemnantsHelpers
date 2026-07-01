#!/bin/bash
# Plot FranksVals lambda template variations on the FIT axis (ptll),
# using rabbit_plot_hists.py --prefit with --varNames so each lambda
# nuisance shows as nominal +/- variation overlaid on the prefit
# prediction. The same script's defaults are used as plotPtll.sh so the
# style matches existing analysis plots.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

FIT="/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260519_franks_vals_quad_realdata/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_franks_vals_quad_realdata/fitresults.hdf5"
OUT="$MY_PLOT_DIR/260519_franks_vals_lambda_templates_ptll"
mkdir -p "$OUT"

RRANGE="${1:-0.98} ${2:-1.02}"

plot_one() {
    local TAG="$1" NAME="$2" LABEL="$3"
    rabbit_plot_hists.py "$FIT" \
        --prefit \
        -m 'Project ch0 ptll' \
        --varNames "$NAME" \
        --varLabels "$LABEL" \
        --config "$WREM_BASE/wremnants/utilities/styles/styles.py" \
        --title CMS --titlePos 0 --subtitle Preliminary \
        --processGrouping z_dilepton \
        --rrange $RRANGE \
        --yscale 1.25 \
        --postfix "lambda_${TAG}" \
        -o "$OUT"
}

plot_one "TMD_Lambda2"  "chargeVgenNP0scetlibNPZlambda2"        'TMD $\Lambda_2$'
plot_one "TMD_Lambda4"  "chargeVgenNP0scetlibNPZlambda4"        'TMD $\Lambda_4$'
plot_one "CS_lambda2"   "scetlibNPgammaLambda2"                  'CS $\gamma\,\lambda_2$'
plot_one "TMD_dLambda2" "chargeVgenNP0scetlibNPZdelta_lambda2"  'TMD $\Delta\Lambda_2$'

echo "Wrote plots to $OUT (rrange=$RRANGE)"
