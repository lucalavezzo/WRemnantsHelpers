#!/bin/bash
# Two more FranksVals fits with the NP-monotonicity wall regularizer:
#   1) asym + reg              (--noSymmetrize, --noConstrainParams,
#                               + NPMonotonicityFranksWall at tau=5)
#   2) asym + reg + fakelumi
# Same recipe as the other chains: ptll-only Project mapping, --realData,
# -t 0, --computeSaturatedProjectionTests; produces ptll postfit +
# pulls/impacts plots, prints impacts and lambda postfit.  Self-queues
# behind any other FranksVals wrapper.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

INFILE="/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Theorymodels/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"

echo "Waiting for other run_franks_vals_*.sh to finish (if running)..."
while pgrep -af "run_franks_vals_(quad_realdata|asym|quad_inflate5x|fakelumi_chain|asym_inflate5x_chain)\.sh" > /dev/null; do
    sleep 60
done
echo "Other FranksVals fits cleared at $(date)"

TAU=5
REG_MODULE_BASE="wremnants.postprocessing.np_monotonicity_franks"
NOCONSTRAIN_REGEX='scetlibNPgammaLambda2|chargeVgenNP0scetlibNPZlambda2|chargeVgenNP0scetlibNPZdelta_lambda2|chargeVgenNP0scetlibNPZlambda4'

run_one() {
    local TAG="$1"          # e.g. asym_reg
    local EXTRA_SETUP="$2"  # extra setupRabbit args

    local POSTFIX="franks_vals_${TAG}_realdata"
    local OUTDIR="$MY_OUT_DIR/260519_franks_vals_${TAG}_realdata"
    local PLOTDIR="$MY_PLOT_DIR/260519_franks_vals_${TAG}_realdata"
    local FITDIR="$OUTDIR/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${POSTFIX}"
    local SETUP="$FITDIR/ZMassDilepton.hdf5"

    mkdir -p "$OUTDIR" "$PLOTDIR"
    echo
    echo "=== $TAG :: setupRabbit ==="
    if [ ! -f "$SETUP" ]; then
        python "$WREM_BASE/scripts/rabbit/setupRabbit.py" \
            -i "$INFILE" \
            --fitvar ptll-yll-cosThetaStarll_quantile-phiStarll_quantile \
            -o "$OUTDIR" \
            --noi alphaS --pdfUncFromCorr \
            --npUnc LatticeNoConstraintsFranks \
            --axlim ptll 0j 44j \
            --postfix "$POSTFIX" \
            --realData \
            --noSymmetrize scetlibNP \
            --noConstrainParams "$NOCONSTRAIN_REGEX" \
            $EXTRA_SETUP
    fi

    echo "=== $TAG :: rabbit_fit (ptll mapping only, wall at tau=$TAU) ==="
    rabbit_fit.py "$SETUP" \
        -t 0 \
        --computeVariations \
        -m Project ch0 ptll \
        --computeSaturatedProjectionTests \
        --computeHistErrors --computeHistImpacts --doImpacts \
        -o "$FITDIR" \
        --globalImpacts --saveHists --saveHistsPerProcess \
        -r "${REG_MODULE_BASE}.NPMonotonicityFranksWall" \
           "${REG_MODULE_BASE}.NPMonotonicityFranksMapping" \
        --regularizationStrength "$TAU"

    local FIT="$FITDIR/fitresults.hdf5"
    echo "=== $TAG :: ptll postfit ==="
    bash "$MY_WORK_DIR/workflows/plotPtll.sh" "$FIT" -o "$PLOTDIR/ptll_postfit" -p "$POSTFIX"

    echo "=== $TAG :: pulls and impacts ==="
    bash "$MY_WORK_DIR/workflows/pullsAndImpacts.sh" "$FIT" -o "$PLOTDIR/pulls_impacts" -p "$POSTFIX"

    echo "=== $TAG :: pdfAlphaS impacts ==="
    python /home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_print_impacts.py "$FIT" --scale 2.0

    echo "=== $TAG :: scetlibNP postfit values ==="
    python /home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_print_pulls_and_constraints.py "$FIT" --keepNuisances 'scetlibNP|fakelumi'
}

run_one "asym_reg"           ""
run_one "asym_reg_fakelumi"  "--fakelumi 1.1"

echo
echo "DONE_OK $(date)"
