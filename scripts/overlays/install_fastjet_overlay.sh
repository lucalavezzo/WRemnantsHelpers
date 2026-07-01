#!/usr/bin/env bash

set -euo pipefail

IMAGE_DEFAULT="/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
OVERLAY_DEFAULT="$HOME/.apptainer/overlays/wmassdevrolling_fastjet.img"
SIZE_MIB_DEFAULT=1024

IMAGE="${1:-$IMAGE_DEFAULT}"
OVERLAY="${2:-$OVERLAY_DEFAULT}"
SIZE_MIB="${FASTJET_OVERLAY_SIZE_MIB:-$SIZE_MIB_DEFAULT}"

mkdir -p "$(dirname "$OVERLAY")"

if [[ ! -f "$OVERLAY" ]]; then
    echo "[fastjet-overlay] Creating overlay: $OVERLAY (${SIZE_MIB} MiB)"
    apptainer overlay create --fakeroot --size "$SIZE_MIB" "$OVERLAY"
else
    echo "[fastjet-overlay] Reusing existing overlay: $OVERLAY"
fi

echo "[fastjet-overlay] Installing FastJet with pacman into overlay"
singularity exec --fakeroot --overlay "$OVERLAY" "$IMAGE" /bin/bash -lc \
    "pacman -Sy --noconfirm --needed fastjet"

echo "[fastjet-overlay] Verifying FastJet"
singularity exec --overlay "${OVERLAY}:ro" "$IMAGE" /bin/bash -lc \
    "command -v fastjet-config && fastjet-config --version"

cat <<EOF
[fastjet-overlay] Done.
Use FastJet-enabled container sessions with:
  singularity run --bind /scratch/,/work/,/home/,/ceph/ --overlay ${OVERLAY}:ro ${IMAGE}
EOF
