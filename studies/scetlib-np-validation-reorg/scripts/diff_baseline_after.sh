#!/bin/bash
# Diff the after-reorg test outputs against the baseline, ignoring lines that
# legitimately vary run-to-run (timings, absolute log paths). A clean diff ==
# the reorg is a numeric no-op for tests 1/2/3.
STUDY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$STUDY"

# Strip: "loaded in 1.2s" / "constructed in 3.4s" / "computed in ...s" durations,
# and the absolute plot-output paths (dir differs: baseline/ vs after/).
norm() { sed -E \
    -e 's/ in [0-9]+\.[0-9]+s/ in Xs/g' \
    -e 's#/(baseline|after)/#/<TAG>/#g' \
    -e 's/[0-9]{10}\.[0-9]+ +[0-9]+/<TS PID>/g' \
    -e '/absl::InitializeLog|oneDNN custom operations|cpu_feature_guard|cuda_platform|cuInit|TF_ENABLE_ONEDNN|cpu_allocator_impl|exceeds 10% of free system memory/d' \
    "$1"; }

rc=0
for t in test1_sigmagen_vs_theorycorr test23_sigma_vs_datacard; do
    if diff <(norm "baseline/$t.txt") <(norm "after/$t.txt") > "after/$t.diff" 2>&1; then
        echo "IDENTICAL (mod timing/paths): $t"
        rm -f "after/$t.diff"
    else
        echo "DIFFERS: $t  -> after/$t.diff"
        rc=1
    fi
done
exit $rc
