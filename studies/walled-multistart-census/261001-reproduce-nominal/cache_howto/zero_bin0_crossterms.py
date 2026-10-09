#!/usr/bin/env python3
"""Quick patch (Luca's option b): zero the fixed-order eigenvector CROSS TERMS in the qT bin
containing the nonsingular cutoff, in an EXISTING cache, without a rebuild.

Why: scetlib-cms 2dd978a's `_fo_bilin_vjet_all` does not skip nodes below `_nons_qt_cut`, so in
the bin containing the cut (production qT [0, 0.5]) the stored B_ef are artefact
(260924-bilin-nons-cut). The genuine values there are +2.7e-04..+4.9e-04 of sigma at the seed's
eigenvector displacement, so zeroing them is a small, bounded approximation.

What is zeroed, in bins with a node below the cut (qT_lo < cut), all muF slots:
  * B[d1][d2] for d1 != d2, d1, d2 >= 1 -- the off-diagonal cross terms (eigenvectors AND the
    alphaS direction). The kernel reads these at every kappa_F.
  * B[0][e], B[e][0], B[e][e] in muF slots 1 and 2 only -- the kappa_F SHIFTS of the linear and
    diagonal response. The kernel reads only these slots for them, as a difference against
    kappa_F = 1, so they matter only at kappa_F != 1 (frozen in the fits); the build polluted
    them the same way (the V+jet half entered Sup/Sdn/S0 too).
Nothing else changes: B[0][0], slot 0 of the linear/diagonal entries, the member rows, the node
grid, the muF polynomial cache, the rules. The value AT kappa_F = 1 with one eigenvector moved is
therefore bit-identical to the input cache.

The blob is edited IN PLACE at B's byte offset (found by walking the same layout
scetlib_cache.parse_fo_blob reads), so no re-emit code can reorder or drop a section.

usage: zero_bin0_crossterms.py <in cache.npz> <out fo.npy> [--cut 0.1]
"""
import argparse
import sys

import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/scetlib-cms/py")
import scetlib_cache as sc  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("cache")
ap.add_argument("out")
ap.add_argument("--cut", type=float, default=0.1)
a = ap.parse_args()

d = np.load(a.cache)
fo = d["fo"]
print(f"fo member: dtype {fo.dtype}, shape {fo.shape}, {fo.nbytes / 1e9:.3f} GB")
buf = fo.tobytes()

# ---- walk to B, mirroring parse_fo_blob field by field -------------------------------
r = sc._R(buf, "fo blob")
magic = bytes(r.raw(8))
assert magic[:7] == sc._FO_MAGIC, magic
r.raw(r.u64())  # fingerprint
sc._parse_fo_grid(r)  # node grid
n_mem = r.u64()
if n_mem:
    r.i32()
    r.f64()
    r.f64()
    r.f64()
    r.i32()
    r.raw(8 * r.u64())  # var_bins
    for _ in range(n_mem):
        r.raw(8 * r.u64())  # member deltas
nd = r.i32()
assert nd > 1, "no bilinear block in this cache"
nmuf = r.i32()
r.f64()
n_eig = r.i32()
nbb = r.u64()
bbins = np.frombuffer(bytes(r.raw(8 * nbb)), dtype="<f8").reshape(-1, 6)
nB = r.u64()
off = r.p
n_bins = len(bbins)
S = nB // (nmuf * nd * nd * n_bins)
assert S * nmuf * nd * nd * n_bins == nB, "B size does not factor"
print(
    f"bilinear block: nd {nd} (1 + {nd - 1} directions, n_eig {n_eig}), muF slots {nmuf}, "
    f"{n_bins} bins, stride {S}, B at byte {off}"
)

B = (
    np.frombuffer(buf, dtype="<f8", count=nB, offset=off)
    .reshape(nmuf, nd, nd, n_bins, S)
    .copy()
)
B0 = B.copy()

# bins with a node below the cut: qT_lo < cut (layout Q_lo,Q_hi,Y_lo,Y_hi,qT_lo,qT_hi)
sel = np.where(bbins[:, 4] < a.cut)[0]
print(
    f"bins containing qT < {a.cut}: {len(sel)} -> "
    f"qT {sorted(set(map(tuple, bbins[sel][:, 4:6])))}, |Y| rows {len(set(bbins[sel][:, 2]))}"
)
assert len(sel) > 0

off_diag = ~np.eye(nd, dtype=bool)
off_diag[0, :] = False
off_diag[:, 0] = False
for q in range(nmuf):
    for n in sel:
        blk = B[q, :, :, n, :]
        blk[off_diag] = 0.0
        if q >= 1:
            for e in range(1, nd):
                blk[0, e] = 0.0
                blk[e, 0] = 0.0
                blk[e, e] = 0.0
        B[q, :, :, n, :] = blk

# ---- self-checks ---------------------------------------------------------------------
changed = B != B0
chg_bins = np.unique(np.where(changed)[3])
assert set(chg_bins) <= set(sel), "an entry outside the selected bins changed"
assert not changed[:, 0, 0].any(), "B_00 changed"
assert not changed[0][np.eye(nd, dtype=bool)].any(), "slot-0 diagonal changed"
assert (
    not changed[0, 0, :].any() and not changed[0, :, 0].any()
), "slot-0 linear changed"
print(f"entries zeroed: {int(changed.sum())} of {B.size}; bins touched {len(chg_bins)}")
rel = np.abs(B0[:, :, :, sel, :][changed[:, :, :, sel, :]])
print(f"  |zeroed values|: median {np.median(rel):.3e}, max {rel.max():.3e}")

new = bytearray(buf)
new[off : off + 8 * nB] = B.astype("<f8").tobytes()
new = bytes(new)
assert new[:off] == buf[:off] and new[off + 8 * nB :] == buf[off + 8 * nB :]
p_old, p_new = sc.parse_fo_blob(buf), sc.parse_fo_blob(new)
for k in ("version", "fingerprint", "grid", "meta", "deltas", "poly"):
    assert p_old[k] == p_new[k], f"section {k} differs"
assert np.array_equal(p_old["var_bins"], p_new["var_bins"])
assert all(
    np.array_equal(x[0], y[0]) and np.array_equal(x[1], y[1])
    for x, y in zip(p_old["var_g"], p_new["var_g"])
)
assert np.array_equal(p_old["bilin"]["bins"], p_new["bilin"]["bins"])
print("re-parse OK; every section except bilin.B is identical")

np.save(a.out, np.frombuffer(new, dtype=fo.dtype).reshape(fo.shape))
print(f"wrote {a.out}")
