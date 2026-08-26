#!/bin/bash
# Same as incontainer_nak.sh but with every thread pool pinned small: the node's
# 32768-threads-per-user ceiling is ~99% consumed by other sessions and SCETlib
# aborts with "pthread_create has failed" the moment it is hit.
set -e
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export NUMEXPR_NUM_THREADS=2
export TF_NUM_INTRAOP_THREADS=2
export TF_NUM_INTEROP_THREADS=1
export XLA_FLAGS="--xla_force_host_platform_device_count=1"
export TF_CPP_MIN_LOG_LEVEL=3
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-nak/build-nak
source /work/submit/lavezzo/alphaS/scetlib-nak/setup.sh > /dev/null
cd /home/submit/lavezzo/alphaS/WRemnants
exec "$@"
