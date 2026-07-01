#!/bin/bash
# 1D fits — proper version: rebuild the workspace with setupRabbit --fitvar <obs>,
# then rabbit_fit on it. (-m only controls projection outputs, not the fit dim,
# so the v1 wrapper was secretly 4D — see 2026-05-14 runlog finding.)
#
# 6 combinations: {nominal AN priors, unconstrained τ=5, Inflate5x_reg5}
# × {ptll, yll}. No projection tests needed — the 1D saturated chi2 IS the
# 1D goodness-of-fit. No impacts.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
HM=/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5

SETUP=$WREM_BASE/scripts/rabbit/setupRabbit.py
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py
REG_CLS=(wremnants.postprocessing.np_monotonicity.NPMonotonicityWall
         wremnants.postprocessing.np_monotonicity.NPMonotonicityMapping)

# Shared setupRabbit flags for all 6. `--axlim` only accepts fit variables,
# so we pass the ptll-range restriction as `--axlim` when fitvar=ptll and as
# `--presel` (the non-fit-axis equivalent) when fitvar=yll. SHARED below
# omits the ptll restriction; run_pair adds the right flavour.
SHARED=(--noi alphaS --npUnc LatticeNoConstraints --pdfUncFromCorr --realData
        -i "$HM" -o "$BASE")

# Per-config setup additions (scaleParams / noConstrainParams)
NPCS_SCALE=(--scaleParams 'scetlibNPgammaLambda2=2.62' 'scetlibNPgammaLambda4=1.12' 'scetlibNPgammaLambdaInf=3.33')
NPUNC_NC=(--noConstrainParams 'scetlibNPgamma|scetlibNPZlambda|scetlibNPZdelta_lambda')
INF5_SCALE=(--scaleParams 'scetlibNPgammaLambda2=13.1' 'scetlibNPgammaLambda4=5.60'
            'scetlibNPgammaLambdaInf=3.33'
            'chargeVgenNP0scetlibNPZlambda2=5.0'
            'chargeVgenNP0scetlibNPZdelta_lambda2=5.0'
            'chargeVgenNP0scetlibNPZlambda4=5.0')

INF5_KFAC=(lambda_2=13.1 lambda_4=5.60 Lambda_2=5.0 Delta_Lambda_2=5.0 Lambda_4=5.0)

# Run one (config, obs) pair
run_pair() {
  # $1=config_tag  $2=obs (ptll|yll)  $3=reg_strength ("" if no reg)
  # remaining args: setupRabbit per-config flags (SCALE / NC)
  # If reg used, INF5_KFAC if Inflate5x_reg5
  local cfgtag="$1"; local obs="$2"; local tau="$3"; shift 3
  local postfix="${cfgtag}_${obs}only"
  echo "============================================================"
  echo "=== $(date) BEGIN ${postfix}  setupRabbit --fitvar ${obs} ==="
  echo "============================================================"
  # ptll [0, 44 GeV] restriction: --axlim if ptll IS the fit var, else --presel
  local ptll_flag=()
  if [[ "$obs" == "ptll" ]]; then
    ptll_flag=(--axlim ptll 0j 44j)
  else
    ptll_flag=(--presel ptll 0j 44j)
  fi
  python "$SETUP" --fitvar "$obs" "${SHARED[@]}" "${ptll_flag[@]}" "$@" -p "$postfix"
  local ws="$BASE/ZMassDilepton_${obs}_${postfix}/ZMassDilepton.hdf5"
  if [[ ! -f "$ws" ]]; then
    echo "ERROR: workspace not found at $ws"
    exit 1
  fi
  local outdir="$BASE/ZMassDilepton_${obs}_${postfix}/data"
  mkdir -p "$outdir"
  echo "=== $(date) rabbit_fit on $ws (output $outdir) ==="
  if [[ -z "$tau" ]]; then
    python "$RABBIT" "$ws" -t 0 -o "$outdir" --saveHists --computeHistErrors
  elif [[ "$cfgtag" == "Inflate5x_reg5" ]]; then
    python "$RABBIT" "$ws" -t 0 -o "$outdir" --saveHists --computeHistErrors \
      --freezeParameters scetlibNPgammaLambdaInf \
      -r "${REG_CLS[@]}" "b" "${INF5_KFAC[@]}" \
      --regularizationStrength "$tau"
  else
    # unconstrained: kfactors all 1, no need to pass them
    python "$RABBIT" "$ws" -t 0 -o "$outdir" --saveHists --computeHistErrors \
      --freezeParameters scetlibNPgammaLambdaInf \
      -r "${REG_CLS[@]}" "b" \
      --regularizationStrength "$tau"
  fi
  echo "=== $(date) DONE ${postfix} ==="
}

# 1. nominal AN priors — ptll then yll
run_pair NPCS100pct      ptll ""  "${NPCS_SCALE[@]}"
run_pair NPCS100pct      yll  ""  "${NPCS_SCALE[@]}"

# 2. unconstrained τ=5 — ptll then yll
run_pair NPUnconstrained ptll "5.0" "${NPUNC_NC[@]}"
run_pair NPUnconstrained yll  "5.0" "${NPUNC_NC[@]}"

# 3. Inflate5x_reg5 — ptll then yll
run_pair Inflate5x_reg5  ptll "5.0" "${INF5_SCALE[@]}"
run_pair Inflate5x_reg5  yll  "5.0" "${INF5_SCALE[@]}"

echo "DONE_OK $(date)"
