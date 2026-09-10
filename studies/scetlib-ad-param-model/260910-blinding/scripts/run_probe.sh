#!/bin/bash
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-blinding
cd /home/submit/lavezzo/alphaS/WRemnants/rabbit
python3 -u "$T/scripts/probe_hess.py" "$T/logs/test_tensor.hdf5"
echo "PROBE_DONE"
