#!/usr/bin/env bash
set -e
TAG="${1:-bhad_diag_$(date +%y%m%d_%H%M%S)}"
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
python studies/z_bb/make_hists.py --tag "$TAG" --nthreads 8
OUTDIR="${MY_OUT_DIR}/$(date +%y%m%d)_gen_massiveBottom"
MASSIVE_FILE="${OUTDIR}/w_z_gen_dists_maxFiles_m1_hadronsSel_massive_${TAG}.hdf5"
MASSLESS_FILE="${OUTDIR}/w_z_gen_dists_maxFiles_1000_nnpdf31_hadronsSel_massless_${TAG}.hdf5"
python studies/z_bb/plot_narf.py --massive-file "$MASSIVE_FILE" --massless-file "$MASSLESS_FILE" --tag "$TAG"
echo "TAG=${TAG}"
echo "MASSIVE_FILE=${MASSIVE_FILE}"
echo "MASSLESS_FILE=${MASSLESS_FILE}"
