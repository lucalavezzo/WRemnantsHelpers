#!/bin/bash
# Real-data (blinded) FranksVals fit + plots/prints.
# Quadratic symmetrization on NP (default), so directly comparable to
# colleague's setup.  POI pdfAlphaS stays blinded (no --unblind).
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

INFILE="/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Theorymodels/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"
OUTDIR="$MY_OUT_DIR/260519_franks_vals_quad_realdata"
PLOTDIR="$MY_PLOT_DIR/260519_franks_vals_quad_realdata"
POSTFIX="franks_vals_quad_realdata"

mkdir -p "$OUTDIR" "$PLOTDIR"
echo "Output dir: $OUTDIR"
echo "Plot dir:   $PLOTDIR"
echo "Input:      $INFILE"

# Reuse the existing real-data setup tensor (written by setupRabbit
# with --realData in the previous run); skip re-running setupRabbit.
# fitter.sh's fit step hardcodes 5 Project mappings, which means
# --computeSaturatedProjectionTests would run a saturated fit for *each*
# (rabbit_fit.py:413-417). Call rabbit_fit directly with just the ptll
# mapping to keep wall time short.
FITDIR="$OUTDIR/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${POSTFIX}"
SETUP="$FITDIR/ZMassDilepton.hdf5"

if [ ! -f "$SETUP" ]; then
    echo "Setup tensor missing -- running setupRabbit"
    python "$WREM_BASE/scripts/rabbit/setupRabbit.py" \
        -i "$INFILE" \
        --fitvar ptll-yll-cosThetaStarll_quantile-phiStarll_quantile \
        -o "$OUTDIR" \
        --noi alphaS --pdfUncFromCorr \
        --npUnc LatticeNoConstraintsFranks \
        --axlim ptll 0j 44j \
        --postfix "$POSTFIX" \
        --realData
fi

echo
echo "=== Calling rabbit_fit on $SETUP (ptll mapping only) ==="
rabbit_fit.py "$SETUP" \
    -t 0 \
    --computeVariations \
    -m Project ch0 ptll \
    --computeSaturatedProjectionTests \
    --computeHistErrors --computeHistImpacts --doImpacts \
    -o "$FITDIR" \
    --globalImpacts --saveHists --saveHistsPerProcess

# Locate the fitresults file
FIT="$FITDIR/fitresults.hdf5"
echo
echo "=== Fitresults: $FIT ==="
ls -la "$FIT"

# Plot ptll postfit. `rabbit_plot_hists.py` reads the fitresults
# directly (default mode is postfit; --prefit would flip it). The
# saturated p-value lands in the plot frame from the fitresults
# metadata stored by --computeSaturatedProjectionTests.
echo
echo "=== Plotting ptll postfit ==="
bash "$MY_WORK_DIR/workflows/plotPtll.sh" "$FIT" -o "$PLOTDIR/ptll_postfit" -p "$POSTFIX"

# Pulls and impacts on pdfAlphaS
echo
echo "=== Pulls and impacts ==="
bash "$MY_WORK_DIR/workflows/pullsAndImpacts.sh" "$FIT" -o "$PLOTDIR/pulls_impacts" -p "$POSTFIX"

# Print pdfAlphaS impacts (scale=2 -> unit = sigma_AN)
echo
echo "=== pdfAlphaS impacts (scale=2 -> sigma_AN) ==="
python /home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_print_impacts.py "$FIT" --scale 2.0

# Print scetlibNP postfit values (pulls + constraints) — these are the
# lambdas (TMD: lambda2, lambda4, delta_lambda2 ; CS gamma: lambda2_nu).
echo
echo "=== scetlibNP postfit values ==="
python /home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_print_pulls_and_constraints.py "$FIT" --keepNuisances 'scetlibNP'

echo
echo "DONE_OK $(date)"
