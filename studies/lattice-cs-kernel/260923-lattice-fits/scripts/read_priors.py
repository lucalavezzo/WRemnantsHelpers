import sys, h5py
from wums import ioutils

for f in sys.argv[1:]:
    meta = ioutils.pickle_load_h5py(h5py.File(f, "r")["meta"])
    print("==", f)
    print("command:", meta["meta_info"]["command"][-400:])
    a = meta["meta_info"]["args"]
    print(
        "earlyStopping",
        a["earlyStopping"],
        "minimizer",
        a["minimizerMethod"],
        "extPostfit",
        a["externalPostfit"],
        "freeze",
        a["freezeParameters"],
    )
    pp = meta.get("param_priors")
    print("param_priors type", type(pp))
    try:
        for k, v in (pp.items() if hasattr(pp, "items") else enumerate(pp)):
            if "lambda" in str(k) or "alpha" in str(k):
                print("   ", k, v)
    except Exception as e:
        print(pp)
