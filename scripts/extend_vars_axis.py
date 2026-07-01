"""Extend vars axis of old (NVARS=36) pkls to 42 entries by zero-padding the 6 new slots."""

import pickle, glob, sys, os
import hist as hist_mod

dirpath = sys.argv[1]
NEW_LABELS = [
    "delta_lambda2-0.02",
    "delta_lambda20.02",
    "mufdown",
    "mufup",
    "mufdown-kappaFO0.5-kappaf2.",
    "mufup-kappaFO2.-kappaf0.5",
]
TARGET_NVARS = 42

count = 0
skipped = 0
errors = 0
for pkl in sorted(glob.glob(os.path.join(dirpath, "*.pkl"))):
    try:
        with open(pkl, "rb") as f:
            d = pickle.load(f)
        h = d["hist"]
        if "vars" not in [a.name for a in h.axes]:
            skipped += 1
            continue
        cur_labels = list(h.axes["vars"])
        if len(cur_labels) == TARGET_NVARS:
            skipped += 1
            continue
        if len(cur_labels) != 36:
            print(f"unexpected nvars={len(cur_labels)} for {pkl}", flush=True)
            errors += 1
            continue
        new_label_list = cur_labels + NEW_LABELS
        axes_no_vars = [a for a in h.axes if a.name != "vars"]
        new_axes = axes_no_vars + [
            hist_mod.axis.StrCategory(new_label_list, name="vars", growth=True)
        ]
        new_h = hist_mod.Hist(*new_axes, storage=h.storage_type())
        cur_view = h.view(flow=False)
        new_view = new_h.view(flow=False)
        new_view[..., : len(cur_labels)] = cur_view
        d["hist"] = new_h
        with open(pkl, "wb") as f:
            pickle.dump(d, f)
        count += 1
    except Exception as e:
        print(f"ERROR {pkl}: {e}", flush=True)
        errors += 1
print(
    f"Extended {count} pkls (skipped {skipped}, errors {errors}) in {dirpath}",
    flush=True,
)
