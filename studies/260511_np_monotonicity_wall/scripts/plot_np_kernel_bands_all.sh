#!/bin/bash
# Generate CS+TMD plots with 68% uncertainty bands for all the configs in
# our comparison table. Toys sampled in θ-space from the postfit Hessian
# inverse and translated to physical NP values via the template
# interpolation in np_param_map.json (see plot_np_kernel.py docstring).
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

B=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
P=ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_
DIR=$MY_PLOT_DIR/260514_np_kernels
SCRIPT=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/260511_np_monotonicity_wall/scripts/plot_np_kernel.py

mkdir -p "$DIR"

# Helper: one call to the band plotter.
run_band() {
  # $1 = output basename (e.g. nominal)
  # $2 = fitresults path
  # $3..= --kfactor args
  local out="$1"; shift
  local frpath="$1"; shift
  echo ""
  echo "=== ${out} ==="
  python "$SCRIPT" \
    --from-fitresults "$frpath" \
    --kfactor "$@" \
    --label "${out} postfit" \
    -o "$DIR/${out}_band.png"
}

# Common kfactor sets (matches build_compare_table.py / scaleParams used at setup time).
NOM_K=(scetlibNPgammaLambda2=2.62 scetlibNPgammaLambda4=1.12 scetlibNPgammaLambdaInf=3.33)
INFV2_K=(scetlibNPgammaLambda2=4.32 scetlibNPgammaLambda4=1.12 scetlibNPgammaLambdaInf=3.33
         chargeVgenNP0scetlibNPZlambda4=1.55)
INF2_K=(scetlibNPgammaLambda2=5.24 scetlibNPgammaLambda4=2.24 scetlibNPgammaLambdaInf=3.33
        chargeVgenNP0scetlibNPZlambda2=2.0 chargeVgenNP0scetlibNPZdelta_lambda2=2.0 chargeVgenNP0scetlibNPZlambda4=2.0)
INF3_K=(scetlibNPgammaLambda2=7.86 scetlibNPgammaLambda4=3.36 scetlibNPgammaLambdaInf=3.33
        chargeVgenNP0scetlibNPZlambda2=3.0 chargeVgenNP0scetlibNPZdelta_lambda2=3.0 chargeVgenNP0scetlibNPZlambda4=3.0)
INF5_K=(scetlibNPgammaLambda2=13.1 scetlibNPgammaLambda4=5.60 scetlibNPgammaLambdaInf=3.33
        chargeVgenNP0scetlibNPZlambda2=5.0 chargeVgenNP0scetlibNPZdelta_lambda2=5.0 chargeVgenNP0scetlibNPZlambda4=5.0)
UNCONS_K=()  # NPUnconstrained: no scaleParams

run_band nominal      "$B/${P}NPCS100pct/fitresults.hdf5"            "${NOM_K[@]}"
run_band inflatedV2   "$B/${P}NPCS100pctV2/fitresults.hdf5"          "${INFV2_K[@]}"
run_band inflate2x    "$B/${P}Inflate2x/fitresults.hdf5"             "${INF2_K[@]}"
run_band inflate3x    "$B/${P}Inflate3x/fitresults.hdf5"             "${INF3_K[@]}"
run_band inflate5x    "$B/${P}Inflate5x/fitresults.hdf5"             "${INF5_K[@]}"
run_band inflate5x_reg5         "$B/${P}Inflate5x_reg5/data_satp/fitresults.hdf5"     "${INF5_K[@]}"
run_band unconstrained_tau5     "$B/${P}NPUnconstrained/data_tau5_satp/fitresults.hdf5"   "${UNCONS_K[@]}"

echo ""
echo "DONE_OK"
ls "$DIR"/*_band.png
