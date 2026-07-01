"""Fix the axis-position vs. axis-label mismatch in alignment-var pkls from
cluster 2746278 (CT18Z lambda6 production).

Root cause: scetlib-run-qT.py builds the vars axis labels in file appearance
order, but places data at axis index equal to the conf section number.
For the CT18Z lambda6 conf the Ext block [42] was moved to the END of the file
(after sections [43]–[48]), so axis label order is [..., 41, 43, 44, 45, 46, 47,
48, 42] (positions 42–48) while data from `_var_NNN.pkl` lands at axis index NNN
(=43..48 for the alignment variations).

Result in untouched new-cluster pkls: data is shifted by ONE relative to its
label (delta_lambda2-0.02 data lives at label "delta_lambda20.02", etc.) and
position 42 (labelled "delta_lambda2-0.02") is empty.

This script processes a single new-cluster pkl (one whose filename has
var_043..var_048) and shifts data positions 43–48 -> 42–47 inside its hist,
clearing position 48 afterwards. Labels are untouched (they were already in
the correct file-order positions). After this, label and data agree.

OLD-cluster pkls (var_000..var_042) are NOT modified — they were correctly
filled at their section numbers when the file order matched section order.

Usage:
    python fix_alignment_var_shift.py <pkl_dir>

The script auto-selects only pkls with var_NNN where NNN in {43,44,45,46,47,48}.
"""

import pickle, glob, sys, os, re
import numpy as np

SRC_DIR = sys.argv[1]
ALIGNMENT_VARS = {43, 44, 45, 46, 47, 48}
NVARS_EXPECTED = 49

# label sanity: positions 42-48 should be these (file-order)
EXPECTED_LABELS_42_48 = [
    "delta_lambda2-0.02",
    "delta_lambda20.02",
    "mufdown",
    "mufup",
    "mufdown-kappaFO0.5-kappaf2.",
    "mufup-kappaFO2.-kappaf0.5",
    "lambda2_nu0.0870-lambda4_nu0.0074-lambda_inf_nu1.6Ext",
]


def varnum_from_filename(path):
    m = re.search(r"_var_(\d+)\.pkl$", path)
    return int(m.group(1)) if m else None


fixed = 0
skipped = 0
unexpected = 0
already_fixed = 0
for pkl in sorted(glob.glob(os.path.join(SRC_DIR, "*.pkl"))):
    vn = varnum_from_filename(pkl)
    if vn is None or vn not in ALIGNMENT_VARS:
        skipped += 1
        continue
    try:
        with open(pkl, "rb") as f:
            d = pickle.load(f)
        h = d["hist"]
        labels = list(h.axes["vars"])
        if len(labels) != NVARS_EXPECTED:
            print(
                f"unexpected nvars={len(labels)} for {os.path.basename(pkl)}",
                flush=True,
            )
            unexpected += 1
            continue
        # sanity check the label order
        if labels[42:49] != EXPECTED_LABELS_42_48:
            print(
                f"label mismatch at 42-48 for {os.path.basename(pkl)}: {labels[42:49]}",
                flush=True,
            )
            unexpected += 1
            continue
        vals = h.values()  # (Q, Y, qT, charge, vars) for CT18Z (5 axes)
        vars_var = h.variances()
        # Detect whether already fixed: if position NN-1 has data and position NN does not, it's already fixed
        nz_pre = np.abs(vals).sum(
            axis=tuple(range(vals.ndim - 1))
        )  # sum over all non-vars axes
        # Expected pre-fix state: only position vn has data, position vn-1 is zero
        # Expected post-fix state: only position vn-1 has data, position vn is zero
        if nz_pre[vn] == 0 and nz_pre[vn - 1] > 0:
            already_fixed += 1
            continue
        if nz_pre[vn] == 0 and nz_pre[vn - 1] == 0:
            print(
                f"both pos {vn-1} and {vn} are zero in {os.path.basename(pkl)}: unexpected",
                flush=True,
            )
            unexpected += 1
            continue
        # Perform the shift: position vn data -> position vn-1, then zero position vn
        # Using direct numpy slice assignment on the underlying arrays
        vals[..., vn - 1] = vals[..., vn]
        vals[..., vn] = 0.0
        vars_var[..., vn - 1] = vars_var[..., vn]
        vars_var[..., vn] = 0.0
        # The hist h's underlying numpy arrays were modified in place via the .values()/.variances() views
        d["hist"] = h
        with open(pkl, "wb") as f:
            pickle.dump(d, f)
        fixed += 1
    except Exception as e:
        print(f"ERROR processing {os.path.basename(pkl)}: {e}", flush=True)
        unexpected += 1

print(f"Fixed {fixed} alignment-var pkls (shifted pos N->N-1)", flush=True)
print(
    f"Already fixed: {already_fixed}; skipped (not alignment): {skipped}; unexpected: {unexpected}"
)
