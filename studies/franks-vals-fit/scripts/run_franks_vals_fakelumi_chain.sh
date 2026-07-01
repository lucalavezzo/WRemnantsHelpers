#!/bin/bash
# FranksVals fakelumi chain: nominal_fakelumi, asym_fakelumi,
# inflate5x_fakelumi.  Each adds --fakelumi 1.1 to setupRabbit so a
# free-floating ~10% log-normal lumi nuisance is added; then rabbit_fit
# -t 0 on ptll only.  Self-queues behind any other FranksVals run.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

INFILE="/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Theorymodels/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"

# Queue behind any other FranksVals wrapper that is still running.
echo "Waiting for other run_franks_vals_*.sh to finish (if running)..."
while pgrep -af "run_franks_vals_(quad_realdata|asym|quad_inflate5x)\.sh" > /dev/null; do
    sleep 60
done
echo "Other FranksVals fits cleared at $(date) -- starting fakelumi chain"

run_one() {
    local TAG="$1"          # e.g. quad_fakelumi
    local EXTRA_SETUP="$2"  # extra setupRabbit args (npUnc, noSymmetrize, scaleParams)

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
            --fakelumi 1.1 \
            $EXTRA_SETUP
    fi

    echo "=== $TAG :: rabbit_fit (ptll mapping only) ==="
    rabbit_fit.py "$SETUP" \
        -t 0 \
        --computeVariations \
        -m Project ch0 ptll \
        --computeSaturatedProjectionTests \
        --computeHistErrors --computeHistImpacts --doImpacts \
        -o "$FITDIR" \
        --globalImpacts --saveHists --saveHistsPerProcess

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

# Three configurations, mirroring the no-fakelumi runs.
run_one "quad_fakelumi"        ""
run_one "asym_fakelumi"        "--noSymmetrize scetlibNP"
run_one "quad_inflate5x_fakelumi" "--scaleParams scetlibNP=5"

echo
echo "DONE_OK $(date)"
