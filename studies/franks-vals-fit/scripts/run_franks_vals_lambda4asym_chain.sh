#!/bin/bash
# FranksVals fit with ONLY TMD Lambda_4 kept asymmetric; all other NP
# nuisances use the framework default symmetrization ("average").
# Mirror with a fakelumi twin.  Real data, blinded, ptll-only Project
# mapping.  Self-queues behind any other FranksVals wrapper.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

INFILE="/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Theorymodels/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"

# Self-queue: wait for other rabbit_fit.py processes (any FranksVals fit) to finish.
SELF_PID=$$
echo "Self pid=$SELF_PID. Waiting for other rabbit_fit.py to finish (if running)..."
while [ -n "$(pgrep -af 'rabbit_fit.py.*franks_vals|setupRabbit.*franks_vals' || true)" ]; do
    sleep 60
done
echo "Other rabbit_fit cleared at $(date)"

# `--noSymmetrize` accepts a regex matched via re.search against the
# per-direction var name (e.g. <name>Up/<name>Down).  This regex
# targets only the TMD Lambda_4 nuisance, leaving the three others
# (CS gamma lambda_2, TMD Lambda_2, TMD Delta_Lambda_2) at the
# framework default ("average").
LAMBDA4_REGEX='chargeVgenNP0scetlibNPZlambda4'

run_one() {
    local TAG="$1"          # e.g. lambda4asym
    local EXTRA_SETUP="$2"  # extra setupRabbit args (e.g. --fakelumi 1.1)

    local POSTFIX="franks_vals_${TAG}_realdata"
    local OUTDIR="$MY_OUT_DIR/260520_franks_vals_${TAG}_realdata"
    local PLOTDIR="$MY_PLOT_DIR/260520_franks_vals_${TAG}_realdata"
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
            --noSymmetrize "$LAMBDA4_REGEX" \
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

run_one "lambda4asym"          ""
run_one "lambda4asym_fakelumi" "--fakelumi 1.1"

echo
echo "DONE_OK $(date)"
