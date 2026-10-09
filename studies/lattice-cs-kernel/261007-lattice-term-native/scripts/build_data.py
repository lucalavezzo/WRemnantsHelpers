"""Build the DATA-ONLY ASWZ lattice inputs for the native lattice term (no theory tables).

Reads the six author files (arXiv:2402.06725, per-ensemble L32/L48/L64 values + covariances) directly and writes
WRemnants/wremnants/postprocessing/scetlib_ad/data/lattice_aswz_data.{npz,json}. Cross-checks every array bitwise
against the phase-3 inputs file (lattice_aswz_inputs.npz, built by 261006-lattice-chi2-in-fit/scripts/build_inputs.py).
"""

import hashlib
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(STUDY, "260923-lattice-data-refit", "data", "CS_lattice_results")
WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
OUTDIR = os.path.join(WREM, "wremnants", "postprocessing", "scetlib_ad", "data")
OLD = os.path.join(OUTDIR, "lattice_aswz_inputs.npz")
ENS = (("L32", 0.15), ("L48", 0.12), ("L64", 0.09))  # README: lattice spacings
HBARC = 0.1973269804  # GeV fm (PDG)

b, a, y, ens, blocks, md5 = [], [], [], [], [], {}
for k, (name, spacing) in enumerate(ENS):
    f = os.path.join(SRC, f"CS_Pz_x_ave_{name}.csv")
    fc = os.path.join(SRC, f"CS_Pz_x_ave_{name}_covariance.csv")
    for p in (f, fc):
        md5[os.path.basename(p)] = hashlib.md5(open(p, "rb").read()).hexdigest()
    d = np.loadtxt(f, delimiter=",", ndmin=2)
    c = np.loadtxt(fc, delimiter=",", ndmin=2)
    assert c.shape == (len(d), len(d))
    b += list(d[:, 0])
    y += list(d[:, 1])
    a += [spacing] * len(d)
    ens += [k] * len(d)
    blocks.append(c)
md5["README"] = hashlib.md5(open(os.path.join(SRC, "README"), "rb").read()).hexdigest()
n = len(b)
cov = np.zeros((n, n))
i0 = 0
for c in blocks:
    cov[i0 : i0 + len(c), i0 : i0 + len(c)] = c
    i0 += len(c)
out = dict(
    b_fm=np.array(b),
    a_fm=np.array(a),
    y=np.array(y),
    ens=np.array(ens, dtype=np.int64),
    cov_stat=cov,
    fm_to_gevinv=np.float64(1.0 / HBARC),
    mu_gev=np.float64(2.0),
)

old = np.load(OLD)
check = {
    k: bool(np.array_equal(out[k], old[k]))
    for k in ("b_fm", "a_fm", "y", "ens", "cov_stat")
}
check["fm_to_gevinv_rel"] = float(abs(out["fm_to_gevinv"] / old["fm_to_gevinv"] - 1))
print("bitwise vs the phase-3 inputs file:", check)
if not all(v for k, v in check.items() if k != "fm_to_gevinv_rel"):
    raise SystemExit("MISMATCH vs the phase-3 inputs file")
# keep the phase-3 constant bit for bit, so the two terms see the same b_T in GeV^-1
out["fm_to_gevinv"] = np.float64(old["fm_to_gevinv"])

np.savez(os.path.join(OUTDIR, "lattice_aswz_data.npz"), **out)
meta = dict(
    what="ASWZ lattice Collins-Soper kernel gamma_q(b_T, mu) per ensemble: DATA ONLY (no theory tables). The "
    "perturbative + NP kernel at these points is computed by SCETlib at every fit step "
    "(lattice_cs_term.py, DrellYan.gamma_nu_points).",
    source="Avkhadiev, Shanahan, Wagman, Zhao, arXiv:2402.06725 (PRL 132 (2024) 231901); author files "
    "CS_Pz_x_ave_{L32,L48,L64}[_covariance].csv + README",
    md5=md5,
    scheme="MSbar, mu = 2 GeV, n_f = 4 lattice (2+1+1 HISQ); uNNLL + LRR matching; gamma_q == SCETlib gamma_zeta "
    "= gamma_nu / 2 (260923-conventions-map)",
    mu_gev=2.0,
    ensembles={
        name: dict(a_fm=sp, n=int(sum(1 for e in ens if e == k)))
        for k, (name, sp) in enumerate(ENS)
    },
    lattice_spacings_source="author README (L32 0.15 fm, L48 0.12 fm, L64 0.09 fm)",
    covariance="block-diagonal across ensembles (no cross-ensemble correlation; author-confirmed adequate "
    "2026-09-29)",
    fm_to_gevinv="1 / hbar c, hbar c = 0.1973269804 GeV fm (kept bit-identical to the phase-3 inputs file)",
    n=n,
    built_by="WRemnantsHelpers studies/lattice-cs-kernel/261007-lattice-term-native/scripts/build_data.py",
    crosscheck_vs_phase3_inputs=check,
)
json.dump(meta, open(os.path.join(OUTDIR, "lattice_aswz_data.json"), "w"), indent=1)
print("wrote", os.path.join(OUTDIR, "lattice_aswz_data.npz"))
