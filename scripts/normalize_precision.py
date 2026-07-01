import pickle, glob, sys, os

target_dir = sys.argv[1]
count = 0
skipped = 0
for pkl in sorted(glob.glob(os.path.join(target_dir, "*.pkl"))):
    with open(pkl, "rb") as f:
        d = pickle.load(f)
    changed = False
    if "config" in d:
        cfg = d["config"]
        if "Integration" in cfg:
            for k in ("target_precision_rel", "target_precision_abs"):
                if k in cfg["Integration"]:
                    cfg["Integration"].pop(k)
                    changed = True
    if changed:
        with open(pkl, "wb") as f:
            pickle.dump(d, f)
        count += 1
    else:
        skipped += 1
print(f"Normalized {count} pkl files (already-normalized: {skipped}) in {target_dir}")
