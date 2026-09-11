#!/bin/bash
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export PYTHONUNBUFFERED=1 PYTHONPATH="/work/submit/lavezzo/alphaS/rabbit-blinding:$PYTHONPATH"
python3 -u /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-blinding/scripts/check_minimum.py "$@"
echo MINCHECK_DONE
