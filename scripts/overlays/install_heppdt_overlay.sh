#!/usr/bin/env bash

set -euo pipefail

IMAGE_DEFAULT="/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
OVERLAY_DEFAULT="$HOME/.apptainer/overlays/wmassdevrolling_heppdt.img"
SIZE_MIB_DEFAULT=2048
PREFIX_DEFAULT="/opt/heppdt"

IMAGE="${1:-$IMAGE_DEFAULT}"
OVERLAY="${2:-$OVERLAY_DEFAULT}"
SIZE_MIB="${HEPPDT_OVERLAY_SIZE_MIB:-$SIZE_MIB_DEFAULT}"
PREFIX="${HEPPDT_PREFIX:-$PREFIX_DEFAULT}"

mkdir -p "$(dirname "$OVERLAY")"

if [[ ! -f "$OVERLAY" ]]; then
    echo "[heppdt-overlay] Creating overlay: $OVERLAY (${SIZE_MIB} MiB)"
    apptainer overlay create --fakeroot --size "$SIZE_MIB" "$OVERLAY"
else
    echo "[heppdt-overlay] Reusing existing overlay: $OVERLAY"
fi

echo "[heppdt-overlay] Building HepPDT from source into ${PREFIX}"
singularity exec --fakeroot --overlay "$OVERLAY" "$IMAGE" /bin/bash -lc "
set -euo pipefail
pacman -Sy --noconfirm --needed base-devel cmake git

if [[ -d /usr/include/HepPDT ]] && [[ -f /usr/lib/libHepPDT.so || -f /usr/lib64/libHepPDT.so ]]; then
    echo '[heppdt-overlay] HepPDT already available in base image; skipping source build.'
    exit 0
fi

SRC_BASE=/opt/src
mkdir -p \"\$SRC_BASE\"
cd \"\$SRC_BASE\"

if [[ ! -d HepPDT ]]; then
    export GIT_TERMINAL_PROMPT=0
    for url in \
        https://github.com/hep-mirrors/heppdt.git \
        https://gitlab.cern.ch/hepmc/HepPDT.git
    do
        if git clone \"\$url\" HepPDT; then
            break
        fi
    done
fi

if [[ ! -d HepPDT ]]; then
    echo 'Failed to clone HepPDT from known URLs' >&2
    exit 1
fi

cd HepPDT
if [[ -f CMakeLists.txt ]]; then
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=${PREFIX}
    cmake --build build -j\$(nproc)
    cmake --install build
elif [[ -x configure ]]; then
    ./configure --prefix=${PREFIX}
    make -j\$(nproc)
    make install
else
    echo 'Unknown HepPDT build system (no CMakeLists.txt or configure)' >&2
    exit 1
fi
"

echo "[heppdt-overlay] Verifying install"
singularity exec --overlay "${OVERLAY}:ro" "$IMAGE" /bin/bash -lc "
set -euo pipefail
if [[ -d ${PREFIX}/include/HepPDT ]] && [[ -f ${PREFIX}/lib/libHepPDT.so || -f ${PREFIX}/lib64/libHepPDT.so ]]; then
    INC_DIR=${PREFIX}/include
    LIB_HINT='${PREFIX}/lib or ${PREFIX}/lib64'
else
    test -d /usr/include/HepPDT
    test -f /usr/lib/libHepPDT.so || test -f /usr/lib64/libHepPDT.so
    INC_DIR=/usr/include
    LIB_HINT='/usr/lib or /usr/lib64'
fi

echo \"[heppdt-overlay] Include dir root: \${INC_DIR}\"
echo \"[heppdt-overlay] Library location: \${LIB_HINT}\"
find \"\${INC_DIR}/HepPDT\" -maxdepth 2 -type f | head -n 10
for root in /usr ${PREFIX}; do
    if [[ -d \"\${root}\" ]]; then
        find \"\${root}\" -maxdepth 3 -type f \\( -name 'libHepPDT.so*' -o -name 'libHepPDT.a' \\) 2>/dev/null | head -n 20
    fi
done
"

cat <<EOF
[heppdt-overlay] Done.
Use HepPDT-enabled sessions with:
  singularity run --bind /scratch/,/work/,/home/,/ceph/ --overlay ${OVERLAY}:ro ${IMAGE}
Optional env for downstream builds:
  export CMAKE_PREFIX_PATH=${PREFIX}:\${CMAKE_PREFIX_PATH:-}
  export LD_LIBRARY_PATH=${PREFIX}/lib:${PREFIX}/lib64:\${LD_LIBRARY_PATH:-}
  export PKG_CONFIG_PATH=${PREFIX}/lib/pkgconfig:${PREFIX}/lib64/pkgconfig:\${PKG_CONFIG_PATH:-}
EOF
