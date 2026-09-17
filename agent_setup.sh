#!/usr/bin/env bash
# Non-interactive equivalent of `alphas` (cd here; asing) followed by
# `source setup.sh`. For agents and detached jobs, which cannot use the
# interactive aliases.
#
#   ./agent_setup.sh [--scetlib <which>] -- <cmd> [args...]
#
# --scetlib picks $SCETLIB_BUILD, which workflows/fitterAD.sh REQUIRES and does
# not set:
#     current  WRemnants/scetlib-cms/build                       (default)
#     authval  /work/.../scetlib-ad-authval-260827/scetlib_snapshot/build
#              -- the ONLY build that can read the 260827 cache (rules v8 /
#              fo v6, below the current build's kRuleVersionMin = 10)
#     pin914   /work/.../scetlib-ad-260914/scetlib-cms/build      (MR !12 v10)
#     <dir>    an explicit build directory
#
# Example (detached + logged, composing with bin/run):
#   run ./agent_setup.sh --scetlib authval -- \
#       fitterAD.sh <card> -c <cachedir> -o <outdir> -p MYFIT
# NOT `set -euo pipefail`: sourcing setup.sh returns nonzero and -e would kill
# this script before it prints anything (documented in
# knowledge/10_environment/runtime_bootstrap.md).
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# ABSOLUTE path to self: the container re-entry below runs this script again,
# and a relative $0 is not resolvable there (fails silently, rc=1).
SELF="$HERE/$(basename "${BASH_SOURCE[0]}")"
# `asing` uses the :testing tag; override with WMASS_IMAGE if you need to match
# a particular run.
IMAGE="${WMASS_IMAGE:-/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest}"
BINDS="${WMASS_BIND_PATHS:-/scratch/,/work/,/home/,/ceph/,/cvmfs/}"  # /cvmfs: LHAPDF sets live there

WHICH=current
PREPEND=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scetlib) WHICH="$2"; shift 2 ;;
    --prepend-pythonpath) PREPEND="$2"; shift 2 ;;
    --) shift; break ;;
    -h|--help) sed -n '2,20p' "$SELF"; exit 0 ;;
    *) echo "agent_setup.sh: unexpected '$1' (forgot '--'?)" >&2; exit 2 ;;
  esac
done
[[ $# -gt 0 ]] || { echo "agent_setup.sh: no command after '--'" >&2; exit 2; }

# re-enter through the container if we are not already inside one
if [[ -z "${SINGULARITY_CONTAINER:-}" && ! -d /.singularity.d ]]; then
  exec singularity run --bind "$BINDS" "$IMAGE" "$SELF" --scetlib "$WHICH" \
       ${PREPEND:+--prepend-pythonpath "$PREPEND"} -- "$@"
fi

source /opt/venv/bin/activate || true
cd "$HERE"
source setup.sh >/dev/null 2>&1 || true

case "$WHICH" in
  current) SDIR="$WREM_BASE/scetlib-cms"; SBUILD="$SDIR/build" ;;
  authval) SDIR=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot; SBUILD="$SDIR/build" ;;
  pin914)  SDIR=/work/submit/lavezzo/alphaS/scetlib-ad-260914/scetlib-cms; SBUILD="$SDIR/build" ;;
  *)       SBUILD="$WHICH"; SDIR="$(dirname "$WHICH")" ;;
esac
[[ -d "$SBUILD" ]] || { echo "agent_setup.sh: no such SCETlib build: $SBUILD" >&2; exit 2; }
export SCETLIB_BUILD="$SBUILD"
[[ -f "$SDIR/setup.sh" ]] && source "$SDIR/setup.sh" >/dev/null 2>&1 || true

# Prepended LAST, deliberately: setup.sh and the SCETlib setup.sh both PREPEND
# to PYTHONPATH, so anything exported before them loses. This is how a patched
# module (e.g. the scetlib_tf.py carrying the hvp zero-seed fix) is made to win
# over the copy shipped in the SCETlib build.
if [[ -n "$PREPEND" ]]; then
  export PYTHONPATH="$PREPEND:$PYTHONPATH"
  echo "[agent_setup] PYTHONPATH prepended: $PREPEND"
fi
echo "[agent_setup] WREM_BASE=$WREM_BASE  SCETLIB_BUILD=$SCETLIB_BUILD  rabbit=$(git -C "$WREM_BASE/rabbit" rev-parse --short HEAD 2>/dev/null)"
exec "$@"
