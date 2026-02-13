#!/usr/bin/env bash
set -eo pipefail
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /home/submit/lavezzo/alphaS/WRemnantsHelpers/agents/debug/container_check_setup.log 2>&1
which python
python --version
python - <<'PY'
import hist
import ROOT
print('imports_ok')
PY
python /home/submit/lavezzo/alphaS/gh/WRemnants/scripts/histmakers/mz_dilepton.py --help > /home/submit/lavezzo/alphaS/WRemnantsHelpers/agents/debug/container_check_help.log 2>&1
head -n 30 /home/submit/lavezzo/alphaS/WRemnantsHelpers/agents/debug/container_check_help.log
