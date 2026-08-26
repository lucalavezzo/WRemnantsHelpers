#!/bin/bash
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/home/submit/lavezzo/alphaS/WRemnants/scetlib-cms/build-fix
source /home/submit/lavezzo/alphaS/WRemnants/scetlib-cms/setup.sh > /dev/null
export TF_NUM_INTRAOP_THREADS=4
export TF_NUM_INTEROP_THREADS=2
cd /home/submit/lavezzo/alphaS/WRemnants
exec "$@"
