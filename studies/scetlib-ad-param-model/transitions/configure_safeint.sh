#!/bin/bash
set -e
cmake -S /work/submit/lavezzo/alphaS/scetlib-safeint \
      -B /work/submit/lavezzo/alphaS/scetlib-safeint/build-safeint \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_COMPILER=/usr/sbin/clang \
      -DCMAKE_CXX_COMPILER=/usr/sbin/clang++ \
      -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
      -Dscetlib_enable_clad=ON \
      -DCLAD_INSTALL_DIR=/home/submit/lavezzo/alphaS/WRemnants/clad-install \
      -Dscetlib_enable_doxygen=OFF -Dscetlib_enable_mathematica=OFF \
      -Dscetlib_DATA_DIR=/home/submit/lavezzo/alphaS/WRemnants/scetlib-cms/share/scetlib
