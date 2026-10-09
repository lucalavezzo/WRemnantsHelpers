#!/usr/bin/env bash
set -e
S=/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
clang++ -O2 -std=c++14 -I$S/build/include -I$S/include -I$S/xmath/include gz_class.cpp -L$S/build/lib -Wl,-rpath,$S/build/lib \
   -lscet-qT -lscet-beamfunc -lscet-hardfunc -lscetlib-core-lib -lxmath -lscet-external -lgsl -lgslcblas -o gz_class
echo built
