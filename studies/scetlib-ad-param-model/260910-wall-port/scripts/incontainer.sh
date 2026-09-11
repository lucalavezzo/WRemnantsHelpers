#!/bin/bash
# Container entry for 260910-wall-port.  A verbatim copy of the harness the
# blinding task used (../260910-blinding/scripts/incontainer.sh), with only the
# $D that supplies the fixed model file left pointing at 260908-fit-770 -- that
# directory holds the frozen lib/scetlib_tf.py and nothing here changes it.
#
# LIBRARY: the frozen VALIDATED snapshot
#   /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot
#   SCETlib b66f8de, libscet-qT.so md5 71b5e68a0cfed89326ff4ed521d37300.
# Same library as 260908-fit-770 / 260910-blinding, so every number here is
# directly comparable to the unwalled DATABLIND fit this task is measured
# against.
#
# RABBIT: the additive-POI-blinding worktree (0f64bbb).  The hard assertion
# below is not hygiene: a rabbit without that commit reads blind_additive via
# getattr(..., False) and silently runs the OLD multiplicative blinding.
set -e
D=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-fit-770
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/build
source /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/setup.sh > /dev/null
export RABBIT_BLINDING_WORKTREE=/work/submit/lavezzo/alphaS/rabbit-blinding
export PYTHONPATH="$RABBIT_BLINDING_WORKTREE:$D/lib:$PYTHONPATH"
export PYTHONDONTWRITEBYTECODE=1
# UNBUFFERED, or a piped log arrives in 8 KB chunks and a healthy job looks hung.
export PYTHONUNBUFFERED=1
cd /home/submit/lavezzo/alphaS/WRemnants
python3 -c "
import scetlib_tf,inspect,hashlib,os
p=inspect.getsourcefile(scetlib_tf); src=open(p,'rb').read()
print('[env] scetlib_tf', p, 'md5', hashlib.md5(src).hexdigest())
print('[env] zero-skip present (FIXED model):', b'if not vv.any():' in src)
lib=os.environ['SCETLIB_BUILD']+'/lib/libscet-qT.so'
print('[env] libscet-qT.so md5', hashlib.md5(open(lib,'rb').read()).hexdigest())
"
echo "[env] rabbit worktree $RABBIT_BLINDING_WORKTREE @ $(git -C $RABBIT_BLINDING_WORKTREE rev-parse --short HEAD 2>/dev/null) ($(git -C $RABBIT_BLINDING_WORKTREE rev-parse --abbrev-ref HEAD 2>/dev/null))"
python3 -c "
import inspect, sys
from rabbit import fitter
src = inspect.getsource(fitter)
has_add = '_blinding_offsets_poi_add' in src
has_frame = 'off_old' in src
print(f'[env] rabbit.fitter from: {inspect.getsourcefile(fitter)}')
print(f'[env] additive POI blinding present : {has_add}')
print(f'[env] physical-start frame shift    : {has_frame}')
if not (has_add and has_frame):
    print('[env] FATAL: this rabbit does NOT carry the blinding change; refusing '
          'to run a fit that would silently test the old multiplicative path.')
    sys.exit(1)
"
echo "[env] WRemnants @ $(git -C /home/submit/lavezzo/alphaS/WRemnants rev-parse --short HEAD) ($(git -C /home/submit/lavezzo/alphaS/WRemnants rev-parse --abbrev-ref HEAD))"
exec "$@"
