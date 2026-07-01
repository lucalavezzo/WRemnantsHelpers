#!/bin/bash
# AN/OLD-NP-values (LatticeNoConstraints, NOT FranksVals): unconstrained
# NPs (no Gaussian prior), asymmetric templates (--noSymmetrize), and
# the existing np_monotonicity NP-monotonicity wall at tau=5.
#
# Two configs: with and without fakelumi.  Self-queues behind any other
# franks_vals_* or AN_* wrapper.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

# AN's standard LatticeNoConstraints histmaker (NOT FranksVals).
HM=/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5

echo "Waiting for other FranksVals wrappers to finish (excluding self pid=$$)..."
while [ -n "$(pgrep -af 'run_franks_vals_[A-Za-z0-9_]*\.sh' | grep -v "^$$ " || true)" ]; do
    sleep 60
done
echo "Other fits cleared at $(date)"

TAU=5
REG_MODULE_BASE="wremnants.postprocessing.np_monotonicity"
# AN regex matches the 6 LatticeNoConstraints NPs (3 CS + 3 TMD).
NP_REGEX='scetlibNPgamma|scetlibNPZlambda|scetlibNPZdelta_lambda'

run_one() {
    local TAG="$1"          # "" or "_fakelumi"
    local EXTRA_SETUP="$2"  # extra setupRabbit args

    local POSTFIX="AN_unconstrained_asym_reg${TAG}_realdata"
    local OUTDIR="$MY_OUT_DIR/260520_${POSTFIX}"
    local PLOTDIR="$MY_PLOT_DIR/260520_${POSTFIX}"
    local FITDIR="$OUTDIR/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${POSTFIX}"
    local SETUP="$FITDIR/ZMassDilepton.hdf5"

    mkdir -p "$OUTDIR" "$PLOTDIR"
    echo
    echo "=== $TAG :: setupRabbit ==="
    if [ ! -f "$SETUP" ]; then
        python "$WREM_BASE/scripts/rabbit/setupRabbit.py" \
            -i "$HM" \
            --fitvar ptll-yll-cosThetaStarll_quantile-phiStarll_quantile \
            -o "$OUTDIR" \
            --noi alphaS --pdfUncFromCorr \
            --npUnc LatticeNoConstraints \
            --axlim ptll 0j 44j \
            --postfix "$POSTFIX" \
            --realData \
            --noSymmetrize "$NP_REGEX" \
            --noConstrainParams "$NP_REGEX" \
            $EXTRA_SETUP
    fi

    echo "=== $TAG :: rabbit_fit (ptll mapping only, wall at tau=$TAU) ==="
    # NO --doImpacts / --globalImpacts / --computeHistImpacts:
    # the wall + asymmetric NPs + free-floating lambda_inf-frozen
    # combination makes the Hessian non-invertible in
    # impacts_parms (TF Op:MatrixInverse fails).  Same family of
    # numerical issue as the quadratic_fakelumi Cholesky failure;
    # skipping the impacts step is the canonical workaround (matches
    # run_unconstrained_tau3_satp.sh in the AN study).
    rabbit_fit.py "$SETUP" \
        -t 0 \
        --computeVariations \
        -m Project ch0 ptll \
        --computeSaturatedProjectionTests \
        --computeHistErrors \
        -o "$FITDIR" \
        --saveHists \
        --freezeParameters scetlibNPgammaLambdaInf \
        -r "${REG_MODULE_BASE}.NPMonotonicityWall" \
           "${REG_MODULE_BASE}.NPMonotonicityMapping" \
        --regularizationStrength "$TAU"

    local FIT="$FITDIR/fitresults.hdf5"
    echo "=== $TAG :: ptll postfit ==="
    bash "$MY_WORK_DIR/workflows/plotPtll.sh" "$FIT" -o "$PLOTDIR/ptll_postfit" -p "$POSTFIX"

    # pulls/impacts plot needs doImpacts data; skipping for this config.

    echo "=== $TAG :: scetlibNP postfit values ==="
    python /home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_print_pulls_and_constraints.py "$FIT" --keepNuisances 'scetlibNP|fakelumi'
}

run_one ""              ""
run_one "_fakelumi"     "--fakelumi 1.1"

echo
echo "DONE_OK $(date)"
