#!/usr/bin/env bash
set -eo pipefail

set +u
source /home/submit/lavezzo/alphaS/gh/WRemnants/setup.sh
set -u

HISTMAKER=/home/submit/lavezzo/alphaS/gh/WRemnants/scripts/histmakers/w_z_gen_dists.py
OUTDIR=/scratch/submit/cms/alphaS/260302_gen_massiveBottom_nlhe
TAG=nlheSel_260302
THREADS=200

python "$HISTMAKER" \
  --dataPath /scratch/submit/cms/wmass/NanoAOD/ \
  --maxFiles -1 \
  --addBottomAxis \
  -o "$OUTDIR" \
  --filterProcs Zbb_MiNNLO \
  -v 4 \
  --postfix hadronsSel_massive_${TAG} \
  -j "$THREADS"

python "$HISTMAKER" \
  --dataPath /scratch/submit/cms/wmass/NanoAOD/ \
  --maxFiles 1000 \
  --addBottomAxis \
  -o "$OUTDIR" \
  --pdf nnpdf31 \
  --filterProcs Zmumu_MiNNLO \
  -v 4 \
  --postfix hadronsSel_massless_${TAG} \
  -j "$THREADS"

MASSIVE_FILE=${OUTDIR}/w_z_gen_dists_maxFiles_m1_hadronsSel_massive_${TAG}.hdf5
MASSLESS_FILE=${OUTDIR}/w_z_gen_dists_maxFiles_1000_nnpdf31_hadronsSel_massless_${TAG}.hdf5

python /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/z_bb/plot_narf.py \
  --massive-file "$MASSIVE_FILE" \
  --massless-file "$MASSLESS_FILE" \
  --outdir /home/submit/lavezzo/public_html/alphaS/260302_z_bb/hadrons/${TAG} \
  --tag "$TAG"

python /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/z_bb/plot_narf.py \
  --massive-file "$MASSIVE_FILE" \
  --massless-file "$MASSLESS_FILE" \
  --outdir /home/submit/lavezzo/public_html/alphaS/260302_z_bb/hadrons/${TAG}_norm \
  --tag "${TAG}_norm" \
  --normalize

echo "MASSIVE_FILE=$MASSIVE_FILE"
echo "MASSLESS_FILE=$MASSLESS_FILE"
