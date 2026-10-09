import sys, numpy as np
from rabbit import io_tools

r = io_tools.get_fitresult(sys.argv[1])
sf = r["mappings"]["Project ch0 ptll"]["saturated_fit"]
for lab, h, c in [
    ("main", r["parms"].get(), r["cov"].get()),
    ("sat", sf["parms"].get(), sf["cov"].get()),
]:
    names = [str(n) for n in h.axes[0]]
    i = names.index("alphaS")
    C = c.values()
    print(
        lab,
        "sigma_theta(alphaS)=",
        np.sqrt(C[i, i]),
        " sigma_as[1e-3]=",
        2 * np.sqrt(C[i, i]),
    )
    for n in ["lambda2", "lambda2_nu", "lumi"]:
        j = names.index(n)
        print("   ", n, h.values()[j], np.sqrt(C[j, j]))
