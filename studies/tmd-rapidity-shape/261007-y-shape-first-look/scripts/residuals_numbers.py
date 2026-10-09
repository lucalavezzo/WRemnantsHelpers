import numpy as np
from rabbit import io_tools

fr = io_tools.get_fitresult(
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_y_shape_first_look/fitresults_YNOWALL8.hdf5"
)
ch = fr["mappings"]["BaseMapping"]["channels"]["ch0"]
d = ch["hist_data_obs"].get()
p = ch["hist_postfit_inclusive"].get()
p0 = ch["hist_prefit_inclusive"].get()
D = d.values()
V = d.variances()
P = p.values()
pt = d.axes[0].edges
y = d.axes[1].edges
r = (D - P) / np.sqrt(V)
print("total chi2 (data stat only)", (r**2).sum(), r.size)
yc = 0.5 * (y[1:] + y[:-1])
ay = np.abs(yc)
groups = [(0, 0.5), (0.5, 1.1), (1.1, 1.5), (1.5, 1.8), (1.8, 2.5)]
wins = [(0, 4), (4, 10), (10, 20), (20, 44)]
print("rel (data-post)/post in %, folded |yll|, ptll windows", wins)
for a, b in groups:
    sel = (ay > a) & (ay < b)
    row = []
    for w0, w1 in wins:
        sp = (pt[:-1] >= w0) & (pt[1:] <= w1)
        dd = D[np.ix_(sp, sel)].sum()
        pp = P[np.ix_(sp, sel)].sum()
        vv = V[np.ix_(sp, sel)].sum()
        row.append(f"{100*(dd/pp-1):+.2f}±{100*np.sqrt(vv)/pp:.2f}")
    chi = (r[:, sel] ** 2).sum()
    print(f"|y| {a}-{b}: ", "  ".join(row), f" chi2 {chi:.1f}/{sel.sum()*len(pt[:-1])}")
# forward-backward symmetry check
print("chi2 by yll bin:", np.round((r**2).sum(axis=0), 1))
