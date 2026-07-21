#!/bin/bash
# Overnight FULL fixed-lambda4 MSHT20 SCETlib production (Z), rel 1e-3, fixed build.
# Produces the raw per-var / per-member pkls for:
#   1. resummed  : 56 NP variations           (variations_lattice_allvars.conf)
#   2. pdfas      : 3 alpha_s members (0,2,5)  (MSHT20nnlo_as_smallrange)
#   3. pdfvars    : 65 PDF members  (0..64)    (MSHT20nnlo_as118)
# Combines are done SEPARATELY (supervised) afterward — this just does the heavy runs.
# Essentials (resummed + pdfas) run first so they finish even if pdfvars spills past morning.
# Launch DETACHED (setsid nohup) so it survives disconnects.

THREADS=320
REPO=/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix
BASE=/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib
FINE="$BASE/com13_msht20_newnps_n3+0ll_lattice_lambda4bugfix_fine/inclusive_Z_COM13_MSHT20_N3+0LL_lattice_fine.ini"
PDV="$BASE/com13_msht20_newnps_n3+0ll_lattice_lambda4bugfix_fine_pdfvars/inclusive_Z_COM13_MSHT20_N3+0LL_lattice_fine_pdfvars.ini"
PAS="$BASE/com13_msht20_newnps_n3+0ll_lattice_lambda4bugfix_fine_pdfvars/inclusive_Z_COM13_MSHT20_N3+0LL_lattice_fine_pdfas.ini"
LOG=/tmp/msht20_overnight.progress
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:v15

: > "$LOG"
singularity exec --bind /work,/scratch,/ceph,/cvmfs,/home "$IMG" /bin/bash -lc '
  REPO="$1"; THREADS="$2"; FINE="$3"; PDV="$4"; PAS="$5"; LOG="$6"
  source /opt/env.sh
  export PYTHONPATH="${REPO}/build/lib:${PYTHONPATH:-}"
  export LD_LIBRARY_PATH="${REPO}/build/lib:${LD_LIBRARY_PATH:-}"
  export LHAPDF_DATA_PATH="/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:/usr/share/lhapdf/LHAPDF"
  RUNQT="${REPO}/prod/scetlib_run/scetlib-run-qT.py"
  log(){ echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $*" >> "$LOG"; }

  log "START overnight production (threads=$THREADS)"

  log "STAGE 1/3: resummed (56 NP vars, 11480 bins)"
  t0=$(date +%s)
  python3 "$RUNQT" "$THREADS" 1 "$FINE" --start-bin 0 --stop-bin 11480 --pdf-member 0 \
    && log "  resummed DONE ($(( ($(date +%s)-t0)/60 )) min)" || log "  resummed FAILED"

  log "STAGE 2/3: pdfas (members 0 2 5)"
  for m in 0 2 5; do
    t0=$(date +%s)
    python3 "$RUNQT" "$THREADS" 1 "$PAS" --start-bin 0 --stop-bin 11480 --pdf-member $m \
      && log "  pdfas m=$m DONE ($(( ($(date +%s)-t0)/60 )) min)" || log "  pdfas m=$m FAILED"
  done

  log "STAGE 3/3: pdfvars (members 0..64)"
  for m in $(seq 0 64); do
    t0=$(date +%s)
    python3 "$RUNQT" "$THREADS" 1 "$PDV" --start-bin 0 --stop-bin 11480 --pdf-member $m \
      && log "  pdfvars m=$m DONE ($(( ($(date +%s)-t0)/60 )) min)" || log "  pdfvars m=$m FAILED"
  done

  log "ALL DONE"
' bash "$REPO" "$THREADS" "$FINE" "$PDV" "$PAS" "$LOG"
