#!/bin/bash
# PDF-swap histmaker launcher (matched LatticeNP pair). Mirrors the 260623 baseline
# command EXACTLY except the primary PDF + primary theory-correction NP tag.
#   Usage: run_histmaker.sh <ct18z|msht20> <maxFiles> <njobs> [outSuffix]
# Runs inside the WRemnants singularity from WREM_BASE (the setup.sh tree).
set -euo pipefail

PDF="${1:?pdf: ct18z|msht20}"; MAXF="${2:?maxFiles}"; NJ="${3:?njobs}"; SUF="${4:-}"
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
OUTBASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS

case "$PDF" in
  ct18z)  PRIMARY=scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO;  PDFS=ct18z  ;;
  msht20) PRIMARY=scetlib_dyturbo_LatticeNP_MSHT20_N3p0LL_N2LO; PDFS=msht20 ;;
  *) echo "unknown PDF '$PDF'"; exit 1 ;;
esac
OUT="${OUTBASE}/260717_pdfswap_${PDF}${SUF}/"

echo "[run_histmaker] PDF=$PDF primary=$PRIMARY maxFiles=$MAXF -j=$NJ out=$OUT"

singularity exec --bind /scratch/,/work/,/home/,/ceph/ "$IMG" bash -c "
  source /opt/venv/bin/activate
  cd /home/submit/lavezzo/alphaS/WRemnantsHelpers && source setup.sh >/dev/null 2>&1
  echo WREM_BASE=\$WREM_BASE
  python \$WREM_BASE/scripts/histmakers/mz_dilepton.py \
    --axes yll ptll --csVarsHist \
    -o '$OUT' \
    --maxFiles $MAXF -j $NJ \
    --theoryCorr \
      ${PRIMARY} ${PRIMARY}_pdfas ${PRIMARY}_pdfvars \
      scetlib_dyturbo_LatticeNP_MSHT20mbrange_N3p0LL_N2LO_pdfvars \
      scetlib_dyturbo_LatticeNP_MSHT20mcrange_N3p0LL_N2LO_pdfvars \
    --pdfs ${PDFS} msht20mcrange_renorm msht20mbrange_renorm \
    --csVarsHist --unfolding --poiAsNoi \
    --unfoldingAxes ptVGen absYVGen helicitySig --unfoldingInclusive \
    --quarkMassCorr MiNNLO_Zbb
"
echo "[run_histmaker] DONE PDF=$PDF rc=$?"
