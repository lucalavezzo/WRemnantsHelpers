#!/bin/bash
# Container entry for the FIVE-KNOT muF stencil arm.
# Own worktree + own build dir; build-fix / build-knots / build-trans / build-nak
# belong to other sessions and are not touched.
set -e
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-4}
export MKL_NUM_THREADS=${MKL_NUM_THREADS:-4}
export OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-4}
export NUMEXPR_NUM_THREADS=${NUMEXPR_NUM_THREADS:-4}
export TF_NUM_INTRAOP_THREADS=${TF_NUM_INTRAOP_THREADS:-4}
export TF_NUM_INTEROP_THREADS=1
export TF_CPP_MIN_LOG_LEVEL=3
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-5knot/build-5knot
source /work/submit/lavezzo/alphaS/scetlib-5knot/setup.sh > /dev/null
cd /home/submit/lavezzo/alphaS/WRemnants
exec "$@"
