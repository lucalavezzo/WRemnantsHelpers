#!/usr/bin/env bash
# Waits for NOLAT (pid 1792824) to finish its whole pass, checks it ended normally, then queues SATPC_NOLAT
# through the shared mem_gate (260 GB, max 2 gated jobs alive). Run detached (setsid nohup).
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ct18z-nominal-fits/261015-trustconstr-precondition
NOL=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_tc_precond_validation
LOG=$OUT/SATPC_NOLAT.log
echo "[launch] $(date +%FT%T) waiting for NOLAT pid 1792824"
while kill -0 1792824 2>/dev/null; do sleep 60; done
echo "[launch] $(date +%FT%T) NOLAT exited"
if ! grep -q "seconds total time" $NOL/NOLAT.log; then
  echo "[launch] NOLAT.log has no 'total time' line: NOLAT did not finish normally. NOT launching."; exit 1
fi
if ! python3 -c "import h5py,sys; f=h5py.File('$NOL/fitresults_NOLAT.hdf5','r'); sys.exit(0 if 'results' in f and 'mappings' in f['results'] else 1)"; then
  echo "[launch] fitresults_NOLAT.hdf5 lacks results/mappings. NOT launching."; exit 1
fi
echo "[launch] $(date +%FT%T) NOLAT final result OK; queueing in mem_gate"
exec /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh 260 $LOG -- \
  /home/submit/lavezzo/alphaS/WRemnantsHelpers/agent_setup.sh --scetlib /work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build -- bash $T/satpc_inner.sh
