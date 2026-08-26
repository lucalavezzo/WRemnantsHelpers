#!/bin/bash
# Container entry for the 62-member PDF cache build.
# Same as the study's incontainer.sh but with SCETlib pinned to a SNAPSHOT of
# /work/submit/lavezzo/alphaS/scetlib-nak (eb60a04 = bb2e7cb + 92f1299 muF
# member-coordinate fix + 83cecb2 settable knot spacing (default 2, inert)
# + 3a8db11 the _rule_is_matched nonsingular double-count fix + rule_cvals).
# Snapshotted so a concurrent rebuild in the shared worktree cannot swap the
# .so or py/ out from under an 8 h job.
set -e
source /opt/venv/bin/activate
source "${WREM_BASE:-/home/submit/lavezzo/alphaS/WRemnants}/setup.sh" > /dev/null
SNAP=/home/submit/lavezzo/.claude/jobs/140d052c/tmp/pdf62/scetlib_snapshot
export SCETLIB_SRC="$SNAP"
export SCETLIB_BUILD="$SNAP/build"
export PYTHONPATH="$SNAP/build/lib:$SNAP/py:$SNAP/prod/scetlib_run${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$SNAP/build/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PATH="$SNAP/build/bin${PATH:+:$PATH}"
# TensorFlow is pulled in transitively by the wremnants imports and is NEVER
# used by the builder (prepare_cache_for_card imports only numpy/h5py plus the
# scetlib_ad backend). Left alone it opens ONE tf_Compute thread PER CORE -- 768
# on this node, measured, ~42% of the process's 1808 OS threads -- against a
# 32768-threads-per-user ceiling that is the binding constraint tonight.
export TF_NUM_INTRAOP_THREADS=32
export TF_NUM_INTEROP_THREADS=4
export TF_CPP_MIN_LOG_LEVEL=2
ulimit -s unlimited 2>/dev/null || true
cd "${WREM_BASE:-/home/submit/lavezzo/alphaS/WRemnants}"
exec "$@"
