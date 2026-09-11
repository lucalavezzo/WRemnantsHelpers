#!/bin/bash
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export PYTHONUNBUFFERED=1 PYTHONPATH="/work/submit/lavezzo/alphaS/rabbit-blinding:$PYTHONPATH"
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-blinding
python3 -u $T/scripts/compare_wall.py "$1" "$2"
echo COMPARE_DONE
