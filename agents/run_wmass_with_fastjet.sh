#!/usr/bin/env bash

set -euo pipefail

IMAGE="${WMASS_IMAGE:-/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest}"
OVERLAY="${WREM_FASTJET_OVERLAY:-$HOME/.apptainer/overlays/wmassdevrolling_fastjet.img}"
BIND_PATHS="${WMASS_BIND_PATHS:-/scratch/,/work/,/home/,/ceph/}"

if [[ ! -f "$OVERLAY" ]]; then
    echo "FastJet overlay not found: $OVERLAY"
    echo "Create it first with: agents/install_fastjet_overlay.sh"
    exit 1
fi

exec singularity run --bind "$BIND_PATHS" --overlay "${OVERLAY}:ro" "$IMAGE" "$@"
