#!/bin/bash
# Real-data (blinded) FranksVals fit with ASYMMETRIC NP nuisances
# (`--noSymmetrize scetlibNP`).  Mirrors run_franks_vals_quad_realdata.sh:
# ptll-only Project mapping so the saturated test runs once.  POI
# pdfAlphaS stays blinded (no --unblind).
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

INFILE="/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Theorymodels/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"
OUTDIR="$MY_OUT_DIR/260519_franks_vals_asym_realdata"
PLOTDIR="$MY_PLOT_DIR/260519_franks_vals_asym_realdata"
POSTFIX="franks_vals_asym_realdata"

mkdir -p "$OUTDIR" "$PLOTDIR"
echo "Output dir: $OUTDIR"
echo "Plot dir:   $PLOTDIR"
echo "Input:      $INFILE"

FITDIR="$OUTDIR/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${POSTFIX}"
SETUP="$FITDIR/ZMassDilepton.hdf5"

# Setup tensor: --realData writes real data into data_obs;
# --noSymmetrize 'scetlibNP' keeps the NP nuisances asymmetric.
if [ ! -f "$SETUP" ]; then
    echo "=== Running setupRabbit (asymmetric NP) ==="
    python "$WREM_BASE/scripts/rabbit/setupRabbit.py" \
        -i "$INFILE" \
        --fitvar ptll-yll-cosThetaStarll_quantile-phiStarll_quantile \
        -o "$OUTDIR" \
        --noi alphaS --pdfUncFromCorr \
        --npUnc LatticeNoConstraintsFranks \
        --axlim ptll 0j 44j \
        --postfix "$POSTFIX" \
        --realData \
        --noSymmetrize 'scetlibNP'
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
