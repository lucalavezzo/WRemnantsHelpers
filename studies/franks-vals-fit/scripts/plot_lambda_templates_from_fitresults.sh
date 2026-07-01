#!/bin/bash
# Plot FranksVals lambda template variations on ptll using
# rabbit_plot_hists.py --prefit --varNames so the templates come from
# the rabbit input tensor (i.e. as the fit sees them, including the
# quadratic symmetrization applied in the quad fit and the raw
# asymmetric templates in the asym fit).
# One plot per NP, for both quad and asym fitresults so they can be
# compared side-by-side.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

QUAD_FIT="/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260519_franks_vals_quad_realdata/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_franks_vals_quad_realdata/fitresults.hdf5"
ASYM_FIT="/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260519_franks_vals_asym_realdata/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_franks_vals_asym_realdata/fitresults.hdf5"

OUT="$MY_PLOT_DIR/260519_franks_vals_lambda_templates_from_fitresults"
mkdir -p "$OUT/quad" "$OUT/asym"

# Caller can override the ratio panel range.
RLO="${1:-0.97}"
RHI="${2:-1.03}"

plot_one() {
    local FIT="$1" SUBDIR="$2" TAG="$3" NAME="$4" LABEL="$5"
    rabbit_plot_hists.py "$FIT" \
        --prefit \
        -m 'Project ch0 ptll' \
        --varNames "$NAME" \
        --varLabels "$LABEL" \
        --config "$WREM_BASE/wremnants/utilities/styles/styles.py" \
        --title CMS --titlePos 0 --subtitle Preliminary \
        --processGrouping z_dilepton \
        --rrange "$RLO" "$RHI" \
        --yscale 1.25 \
        --postfix "lambda_${TAG}" \
        -o "$OUT/$SUBDIR"
}

run_set() {
    local FIT="$1" SUBDIR="$2"
    echo "=== $SUBDIR ($FIT) ==="
    plot_one "$FIT" "$SUBDIR" "TMD_Lambda2"  "chargeVgenNP0scetlibNPZlambda2"        'TMD $\Lambda_2$'
    plot_one "$FIT" "$SUBDIR" "TMD_Lambda4"  "chargeVgenNP0scetlibNPZlambda4"        'TMD $\Lambda_4$'
    plot_one "$FIT" "$SUBDIR" "CS_lambda2"   "scetlibNPgammaLambda2"                  'CS $\gamma\,\lambda_2$'
    plot_one "$FIT" "$SUBDIR" "TMD_dLambda2" "chargeVgenNP0scetlibNPZdelta_lambda2"  'TMD $\Delta\Lambda_2$'
}

run_set "$QUAD_FIT" "quad"
run_set "$ASYM_FIT" "asym"

echo
echo "Wrote plots to $OUT/{quad,asym}  (rrange=$RLO $RHI)"
