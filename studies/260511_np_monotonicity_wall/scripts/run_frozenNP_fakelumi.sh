#!/bin/bash
# Diagnostic: freeze all 6 NP nuisances at AN central, float only α_S,
# add fakelumi. Tells us the pure data α_S–lumi coupling with zero NP
# absorption. If the resulting fakelumi-induced Δα_S is close to what we
# see in the nominal+fakelumi fit (~+2.30×10⁻³), the NPs aren't the source
# of the coupling — the data has an intrinsic α_S–lumi correlation. If
# it's much smaller, the NP freedom is what's letting lumi steer α_S.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
P=ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py

# All 6 NP nuisances frozen at their prior central (θ=0 → physical = AN central).
FROZEN=(
  scetlibNPgammaLambda2
  scetlibNPgammaLambda4
  scetlibNPgammaLambdaInf
  chargeVgenNP0scetlibNPZlambda2
  chargeVgenNP0scetlibNPZdelta_lambda2
  chargeVgenNP0scetlibNPZlambda4
)

run_frozen() {
  # $1=workspace-suffix
  local suffix="$1"
  local cfg="$BASE/${P}${suffix}"
  local ws="$cfg/ZMassDilepton.hdf5"
  local out="$cfg/data_frozenNP_satp"
  mkdir -p "$out"
  echo "=== $(date) frozenNP ${suffix} ==="
  python "$RABBIT" "$ws" \
    -m Project ch0 ptll -t 0 -o "$out" \
    --computeSaturatedProjectionTests \
    --saveHists --computeHistErrors \
    --freezeParameters "${FROZEN[@]}"
  echo "=== $(date) DONE ${suffix} ==="
}

# Both: NPCS100pct (no fakelumi) and NPCS100pct_fakelumi.
# Shift between them = pure data α_S–lumi coupling with NPs pinned at AN central.
run_frozen NPCS100pct
run_frozen NPCS100pct_fakelumi

echo "DONE_OK $(date)"
