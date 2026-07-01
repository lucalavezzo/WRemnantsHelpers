#!/usr/bin/env bash
set -eo pipefail

TAG="${1:-lepflv_$(date +%y%m%d_%H%M%S)}"
MAX_FILES="${2:-20}"
NTHREADS="${3:-8}"

cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh

OUTDIR="${MY_OUT_DIR}/$(date +%y%m%d)_gen_massiveBottom"
HISTMAKER="${WREM_BASE}/scripts/histmakers/w_z_gen_dists.py"

echo "[run] tag=${TAG} maxFiles=${MAX_FILES} nthreads=${NTHREADS}"
echo "[run] outdir=${OUTDIR}"

python "${HISTMAKER}" \
  --dataPath /scratch/submit/cms/wmass/NanoAOD/ \
  --maxFiles "${MAX_FILES}" \
  --addBottomAxis \
  -o "${OUTDIR}" \
  --filterProcs Zbb_MiNNLO \
  -v 4 \
  --postfix "hadronsSel_massive_${TAG}" \
  -j "${NTHREADS}"

OUTFILE="${OUTDIR}/w_z_gen_dists_maxFiles_${MAX_FILES}_hadronsSel_massive_${TAG}.hdf5"
echo "[run] hist output: ${OUTFILE}"

python studies/z_bb/check_massive_z_lepton_flavor.py \
  --dataPath /scratch/submit/cms/wmass/NanoAOD/ \
  --maxFiles "${MAX_FILES}" \
  --filterProc Zbb_MiNNLO
