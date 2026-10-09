#!/usr/bin/env bash
# Configure + build the gamma-nu-points SCETlib worktree in its OWN build dir.
# Never touches $WREM_BASE/scetlib-cms/build (the build the running fits use).
# Run inside the container: agent_setup.sh -- bash build_scetlib.sh [make targets]
set -e
S=/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms
B=$S/build
if [[ ! -f $B/CMakeCache.txt ]]; then
  cmake -S $S -B $B -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/sbin/clang++ -DCMAKE_C_COMPILER=/usr/sbin/clang \
    -Dscetlib_enable_clad=ON -DCLAD_INSTALL_DIR=$WREM_BASE/clad-install -Dscetlib_enable_python=ON \
    -Dscetlib_enable_lhapdf=ON -Dscetlib_enable_testing=ON -Dxmath_enable_testing=OFF \
    -Dscetlib_DATA_DIR=$WREM_BASE/scetlib-cms/share/scetlib -DPYTHON_EXECUTABLE=/opt/venv/bin/python -DCMAKE_POLICY_VERSION_MINIMUM=3.5
fi
nice -n 10 cmake --build $B -j ${JOBS:-32} ${@:+--target $@}
echo "BUILD OK $(date -Is) $(git -C $S rev-parse --short HEAD) dirty=$(git -C $S status --porcelain --untracked-files=no | wc -l)"
