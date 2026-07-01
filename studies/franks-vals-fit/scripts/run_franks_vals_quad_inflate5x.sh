#!/bin/bash
# Real-data (blinded) FranksVals fit with NP priors inflated 5x.
# Same recipe as run_franks_vals_quad_realdata.sh (quadratic
# symmetrization, ptll-only Project mapping, --realData, -t 0) plus
# --scaleParams 'scetlibNP=5' so every scetlibNP-prefixed nuisance has
# its kfactor multiplied by 5.  POI pdfAlphaS stays blinded.
#
# Self-queues behind run_franks_vals_asym.sh if that is still running,
# so the two fits don't compete for cores.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

INFILE="/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Theorymodels/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"
OUTDIR="$MY_OUT_DIR/260519_franks_vals_quad_inflate5x_realdata"
PLOTDIR="$MY_PLOT_DIR/260519_franks_vals_quad_inflate5x_realdata"
POSTFIX="franks_vals_quad_inflate5x_realdata"

mkdir -p "$OUTDIR" "$PLOTDIR"

# Self-queue behind the asym fit.
echo "Waiting for run_franks_vals_asym.sh to finish (if running)..."
while pgrep -af "run_franks_vals_asym.sh" > /dev/null; do
    sleep 60
done
echo "Asym fit cleared at $(date) -- starting inflate5x"

echo "Output dir: $OUTDIR"
echo "Plot dir:   $PLOTDIR"
echo "Input:      $INFILE"

FITDIR="$OUTDIR/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${POSTFIX}"
SETUP="$FITDIR/ZMassDilepton.hdf5"

if [ ! -f "$SETUP" ]; then
    echo "=== Running setupRabbit (NP priors inflated 5x) ==="
    python "$WREM_BASE/scripts/rabbit/setupRabbit.py" \
        -i "$INFILE" \
        --fitvar ptll-yll-cosThetaStarll_quantile-phiStarll_quantile \
        -o "$OUTDIR" \
        --noi alphaS --pdfUncFromCorr \
        --npUnc LatticeNoConstraintsFranks \
        --axlim ptll 0j 44j \
        --postfix "$POSTFIX" \
        --realData \
        --scaleParams 'scetlibNP=5'
fi

echo
echo "=== Calling rabbit_fit (ptll mapping only, -t 0 real data) ==="
rabbit_fit.py "$SETUP" \
    -t 0 \
    --computeVariations \
    -m Project ch0 ptll \
    --computeSaturatedProjectionTests \
    --computeHistErrors --computeHistImpacts --doImpacts \
    -o "$FITDIR" \
    --globalImpacts --saveHists --saveHistsPerProcess

FIT="$FITDIR/fitresults.hdf5"
echo
echo "=== Fitresults: $FIT ==="
ls -la "$FIT"

echo
echo "=== Plotting ptll postfit ==="
bash "$MY_WORK_DIR/workflows/plotPtll.sh" "$FIT" -o "$PLOTDIR/ptll_postfit" -p "$POSTFIX"

echo
echo "=== Pulls and impacts ==="
bash "$MY_WORK_DIR/workflows/pullsAndImpacts.sh" "$FIT" -o "$PLOTDIR/pulls_impacts" -p "$POSTFIX"

echo
echo "=== pdfAlphaS impacts (scale=2 -> sigma_AN) ==="
python /home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_print_impacts.py "$FIT" --scale 2.0

echo
echo "=== scetlibNP postfit values ==="
python /home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_print_pulls_and_constraints.py "$FIT" --keepNuisances 'scetlibNP'

echo
echo "DONE_OK $(date)"
