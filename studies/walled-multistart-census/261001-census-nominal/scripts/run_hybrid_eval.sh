#!/usr/bin/env bash
# CENS03 diagnosis (orchestrator, 2026-10-01): NLL at (CENS03R param-model params + NOMSTIFF nuisances) and at the CENS03R snapshot.
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/walled-multistart-census/261001-census-nominal
O=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261001_census_nominal/seeds/hybrid
REF=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5
export PYTHONUNBUFFERED=1
"$H/agent_setup.sh" --scetlib current -- python3 $T/scripts/step0_eval.py --ref $REF --seeds $O/hybrid_pm03_nuisNOM.hdf5 $O/snap03R.hdf5 --out $T/cens03_hybrid_eval.json 2>&1
echo "[run] $(date -Is) exit=$?"
