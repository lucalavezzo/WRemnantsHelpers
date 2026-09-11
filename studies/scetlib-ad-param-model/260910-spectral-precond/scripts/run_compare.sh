#!/bin/bash
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export PYTHONPATH="/work/submit/lavezzo/alphaS/rabbit-blinding:$PYTHONPATH"
export PYTHONUNBUFFERED=1
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-spectral-precond
cd /home/submit/lavezzo/alphaS/WRemnants
python3 -u $T/scripts/compare_arms.py "$@"
