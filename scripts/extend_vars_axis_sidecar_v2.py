"""Extend vars axis of CT18Z lambda6 pkls from 43 → 49 vars, matching the variations.conf order.

Canonical 49-var axis order (from variations file appearance order):
  positions 0-41: original first 42 vars (pdf0 ... transition_points0.3_0.6_0.9)
  positions 42-47: NEW alignment vars [43-48 in conf file]
    42: delta_lambda2-0.02
    43: delta_lambda20.02
    44: mufdown
    45: mufup
    46: mufdown-kappaFO0.5-kappaf2.
    47: mufup-kappaFO2.-kappaf0.5
  position 48: Ext block (lambda2_nu0.0870-lambda4_nu0.0074-lambda_inf_nu1.6Ext)

For 43-var pkls, data at axis positions 0-41 stays at 0-41, data at axis position 42 (Ext) moves to 48.
Positions 42-47 are zero-padded.

For 49-var pkls (from new cluster) — just copy.
"""

import pickle, glob, sys, os, shutil
import hist as hist_mod

src_dir = sys.argv[1]
dst_dir = sys.argv[2]

NEW_LABELS_INSERT_BETWEEN = [
    "delta_lambda2-0.02",
    "delta_lambda20.02",
    "mufdown",
    "mufup",
    "mufdown-kappaFO0.5-kappaf2.",
    "mufup-kappaFO2.-kappaf0.5",
]
SRC_NVARS = 43
TARGET_NVARS = 49

os.makedirs(dst_dir, exist_ok=True)

extended = 0
copied = 0
unexpected = 0
errors = 0
for pkl in sorted(glob.glob(os.path.join(src_dir, "*.pkl"))):
    fname = os.path.basename(pkl)
    dst_pkl = os.path.join(dst_dir, fname)
    try:
        with open(pkl, "rb") as f:
            d = pickle.load(f)
        h = d["hist"]
        if "vars" not in [a.name for a in h.axes]:
            shutil.copy2(pkl, dst_pkl)
            copied += 1
            continue
        cur_labels = list(h.axes["vars"])
        if len(cur_labels) == TARGET_NVARS:
            shutil.copy2(pkl, dst_pkl)
            copied += 1
            continue
        if len(cur_labels) != SRC_NVARS:
            print(f"unexpected nvars={len(cur_labels)} for {fname}", flush=True)
            unexpected += 1
            shutil.copy2(pkl, dst_pkl)
            continue
        # Insert 6 new labels BEFORE the Ext block (the last entry at position 42)
        prefix = cur_labels[:42]  # positions 0-41
        ext = cur_labels[42:43]  # position 42 (Ext)
        new_label_list = prefix + NEW_LABELS_INSERT_BETWEEN + ext  # 42+6+1=49
        assert len(new_label_list) == TARGET_NVARS, f"len={len(new_label_list)}"
        axes_no_vars = [a for a in h.axes if a.name != "vars"]
        new_axes = axes_no_vars + [
            hist_mod.axis.StrCategory(new_label_list, name="vars", growth=True)
        ]
        new_h = hist_mod.Hist(*new_axes, storage=h.storage_type())
        cur_view = h.view(flow=False)
        new_view = new_h.view(flow=False)
        # data at axis positions 0-41 → 0-41
        new_view[..., :42] = cur_view[..., :42]
        # data at axis position 42 (old Ext) → 48 (new Ext)
        new_view[..., 48] = cur_view[..., 42]
        # positions 42-47 stay zero
        d["hist"] = new_h
        with open(dst_pkl, "wb") as f:
            pickle.dump(d, f)
        extended += 1
    except Exception as e:
        print(f"ERROR {fname}: {e}", flush=True)
        errors += 1
print(f"src={src_dir}", flush=True)
print(f"dst={dst_dir}", flush=True)
print(
    f"Extended {extended}; copied {copied}; unexpected {unexpected}; errors {errors}",
    flush=True,
)
