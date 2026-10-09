import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260924_ptll_tension_loc"
r = io_tools.get_fitresult(f"{A}/FRZAS/fitresults_FRZAS.hdf5")
sf = r["mappings"]["Project ch0 ptll"]["saturated_fit"]
h = sf["parms"].get()
n = [str(x) for x in h.axes[0]]
v = h.values()
C = sf["cov"].get().values()
idx = [n.index(f"saturated_ch0_ptll{i}") for i in range(39)]
s = v[idx]
Cs = C[np.ix_(idx, idx)]
S = s**2
J = np.diag(2 * s)
CS = J @ Cs @ J
ref = list(range(9, 39))  # ptll > 5 GeV plateau
w = np.zeros(39)
w[ref] = 1 / len(ref)
P = S @ w
R = S / P
# jacobian of R_i = S_i/P : dR_i/dS_j = delta_ij/P - S_i w_j /P^2
JR = np.eye(39) / P - np.outer(S, w) / P**2
CR = JR @ CS @ JR.T
eR = np.sqrt(np.diag(CR))
edges = [
    0,
    1,
    1.5,
    2,
    2.5,
    3,
    3.5,
    4,
    4.5,
    5,
    5.5,
    6,
    6.5,
    7,
    7.5,
    8,
    8.5,
    9,
    9.5,
    10,
    10.5,
    11,
    11.5,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    22,
    24,
    26,
    28,
    30,
    33,
    37,
    44,
]
for i in range(39):
    print(
        f"{edges[i]:5.1f}-{edges[i+1]:5.1f}  {100*(R[i]-1):+6.2f} +- {100*eR[i]:.2f} %"
    )
print("plateau level (normalisation, not meaningful):", P)
