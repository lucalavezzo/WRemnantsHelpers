#!/usr/bin/env bash
set -euo pipefail

LHE_FILE="${1:-/work/submit/lavezzo/combined-pwgevents-1.lhe}"
CMSSW_BASE_DIR="${2:-/work/submit/lavezzo/CMSSW_10_6_26}"
NEVENTS="${3:-2}"

if [[ ! -f "${LHE_FILE}" ]]; then
  echo "ERROR: LHE file not found: ${LHE_FILE}"
  exit 1
fi

if [[ ! -d "${CMSSW_BASE_DIR}/src" ]]; then
  echo "ERROR: CMSSW src not found: ${CMSSW_BASE_DIR}/src"
  exit 1
fi

WORKDIR="/tmp/lhe_weight_check_$(date +%Y%m%d_%H%M%S)"
mkdir -p "${WORKDIR}"

echo "==> LHE input: ${LHE_FILE}"
echo "==> CMSSW: ${CMSSW_BASE_DIR}"
echo "==> Workdir: ${WORKDIR}"
echo "==> Events: ${NEVENTS}"

SANITIZED_LHE="${WORKDIR}/input.sanitized.lhe"
echo "==> Creating sanitized LHE copy at ${SANITIZED_LHE}"
python3 - "${LHE_FILE}" "${SANITIZED_LHE}" <<'PY'
from pathlib import Path
import re
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
txt = src.read_text(errors="ignore")
# Remove XML comments; malformed comments with '--' inside break LHESource XML parsing.
txt = re.sub(r'<!--.*?-->', '', txt, flags=re.S)
dst.write_text(txt)
print(f"Wrote {dst}")
PY

echo "==> Inspecting weights directly in LHE file"
python3 - "${SANITIZED_LHE}" <<'PY'
import re
import sys
from collections import Counter

lhe = sys.argv[1]
weight_ids = []
in_initrwgt = False
with open(lhe, "r", errors="ignore") as f:
    for line in f:
        s = line.lstrip()
        if s.startswith("#"):
            continue
        if "<initrwgt" in s:
            in_initrwgt = True
        if in_initrwgt:
            m = re.search(r'<weight[^>]*id=["\']([^"\']+)["\']', s)
            if m:
                weight_ids.append(m.group(1))
        if in_initrwgt and "</initrwgt>" in s:
            break

print(f"Found {len(weight_ids)} weights in <initrwgt> header.")
if weight_ids:
    print("First 20 weight ids:")
    for wid in weight_ids[:20]:
        print(f"  {wid}")
    dup = [k for k, v in Counter(weight_ids).items() if v > 1]
    if dup:
        print(f"Duplicate ids detected: {len(dup)}")
PY

set +u
source /cvmfs/cms.cern.ch/cmsset_default.sh
set -u
export SCRAM_ARCH="${SCRAM_ARCH:-slc7_amd64_gcc700}"
cd "${CMSSW_BASE_DIR}/src"
eval "$(scramv1 runtime -sh)"
cd "${WORKDIR}"

# EL9 hosts often miss libtinfo.so.5 needed by SLC7 CMSSW binaries.
if ! ldconfig -p 2>/dev/null | grep -q 'libtinfo\.so\.5'; then
  mkdir -p /tmp/libtinfo_compat
  if [[ -f /usr/lib64/libtinfo.so.6 ]]; then
    ln -sf /usr/lib64/libtinfo.so.6 /tmp/libtinfo_compat/libtinfo.so.5
    export LD_LIBRARY_PATH="/tmp/libtinfo_compat:${LD_LIBRARY_PATH:-}"
    echo "==> Applied libtinfo compatibility shim: /tmp/libtinfo_compat/libtinfo.so.5"
  fi
fi

echo "==> Building LHE -> MINIAODSIM cfg"
cmsDriver.py Configuration/Generator/python/Hadronizer_TuneCUETP8M1_13TeV_generic_LHE_pythia8_cff.py \
  --python_filename lhe2miniaod_cfg.py \
  --eventcontent MINIAODSIM \
  --datatier MINIAODSIM \
  --filein "file:${SANITIZED_LHE}" \
  --fileout file:miniaod_from_lhe.root \
  --conditions 106X_mcRun2_asymptotic_v17 \
  --beamspot Realistic25ns13TeV2016Collision \
  --step GEN,SIM,DIGI,L1,DIGI2RAW,HLT:@relval2016,RAW2DIGI,L1Reco,RECO,RECOSIM,PAT \
  --geometry DB:Extended \
  --era Run2_2016 \
  --mc \
  --runUnscheduled \
  -n "${NEVENTS}" \
  --no_exec

echo "==> Running cmsRun (LHE -> MINIAODSIM)"
cmsRun lhe2miniaod_cfg.py

echo "==> Building MINIAODSIM -> NANOAODSIM cfg (with nanoGenWmassCustomize)"
cmsDriver.py RECO \
  --conditions 106X_mcRun2_asymptotic_v17 \
  --datatier NANOAODSIM \
  --eventcontent NANOAODSIM \
  --era Run2_2016,run2_nanoAOD_106Xv2 \
  --customise Configuration/DataProcessing/Utils.addMonitoring,PhysicsTools/NanoAOD/nano_cff.nanoGenWmassCustomize \
  --filein file:miniaod_from_lhe.root \
  --fileout file:nano_from_lhe.root \
  --nThreads 1 \
  --python_filename miniaod2nano_cfg.py \
  --mc \
  --scenario pp \
  --step NANO \
  -n -1 \
  --no_exec

echo "==> Running cmsRun (MINIAODSIM -> NANOAODSIM)"
cmsRun miniaod2nano_cfg.py

echo "==> Checking Nano branches for LHE information"
python3 - <<'PY'
import ROOT
f = ROOT.TFile.Open("nano_from_lhe.root")
if not f or f.IsZombie():
    raise SystemExit("ERROR: failed to open nano_from_lhe.root")
t = f.Get("Events")
if not t:
    raise SystemExit("ERROR: Events tree not found")
branches = [b.GetName() for b in t.GetListOfBranches()]
lhe_branches = sorted([b for b in branches if "LHE" in b])
print(f"Events entries: {t.GetEntries()}")
print("LHE-related branches:")
for b in lhe_branches:
    print(f"  {b}")
needed = ["LHEWeight_originalXWGTUP", "LHEScaleWeight", "LHEPdfWeight"]
missing = [b for b in needed if b not in branches]
if missing:
    print("MISSING expected key branches:", ", ".join(missing))
    raise SystemExit(2)
print("All key LHE weight branches are present.")
PY

echo "==> Done. Outputs in: ${WORKDIR}"
