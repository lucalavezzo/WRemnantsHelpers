#!/usr/bin/env bash
# Build the option-B prototype against the CURRENT scetlib build (read-only use of the checkout).
# Run inside the container:  WRemnantsHelpers/agent_setup.sh --scetlib current -- bash <this>
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
S=${SCETLIB_DIR:-$WREM_BASE/scetlib-cms}
CLAD=$WREM_BASE/clad-install
INC="-I$S/build/include -I$S/include -I$S/xmath/include"
FL="-O2 -std=c++14 -fPIC"
cd "$HERE"
clang++ $FL $INC -I$CLAD/include -fplugin=$CLAD/lib/clad.so -c gz_clad.cpp -o gz_clad.o
clang++ $FL $INC -c gz_proto.cpp -o gz_proto.o
clang++ gz_proto.o gz_clad.o -L$S/build/lib -Wl,-rpath,$S/build/lib \
   -lscet-qT -lscet-beamfunc -lscet-hardfunc -lscetlib-core-lib -lxmath -lscet-external -lgsl -lgslcblas -o gz_proto
echo built "$HERE/gz_proto"
