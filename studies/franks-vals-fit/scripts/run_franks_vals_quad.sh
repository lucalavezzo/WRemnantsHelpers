#!/bin/bash
# FranksVals fit with the default quadratic symmetrization on NP nuisances
# (matches colleague's setup for validation).
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

INFILE="/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Theorymodels/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"
OUTDIR="$MY_OUT_DIR/260519_franks_vals_quad"

mkdir -p "$OUTDIR"
echo "Output dir: $OUTDIR"
echo "Input: $INFILE"

# Default: --symmetrizeTheoryUnc=quadratic --symmetrizePdfUnc=quadratic
# (already set in setupRabbit.py).  We only override the np model.
bash "$MY_WORK_DIR/workflows/fitter.sh" "$INFILE" \
    -o "$OUTDIR" \
    -p "franks_vals_quad" \
    -e "--npUnc LatticeNoConstraintsFranks"

echo "DONE_OK $(date)"
