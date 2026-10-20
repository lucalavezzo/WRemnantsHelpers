"""Physical NP lambda values and active faces for a list of fitresults (container; uses np_function_plots.read_ad_fitresult).
Prints only NP lambdas (alphaS filtered out)."""

import sys, re
from wremnants.postprocessing.scetlib_ad import np_function_plots as nfp

for spec in sys.argv[1:]:
    tag, path = spec.split("=", 1)
    pre, post, toys, faces = nfp.read_ad_fitresult(path, n_toys=0)
    lam = (
        {k: v for k, v in post.lam.items() if "lambda" in k}
        if hasattr(post, "lam")
        else None
    )
    print(f"LAMBDAS {tag}: {lam if lam is not None else post}  FACES {list(faces)}")
