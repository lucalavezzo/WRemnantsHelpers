"""Linearised (Gauss-Newton) reconstruction of the ptll-projection test from saved covariances.

From the M1 (saturated ptll sub-fit) covariance, H1 = cov1^-1 is the Hessian of the reduced NLL
in (theta, x) with x = sqrt(s) the stored scale parameters.  Because each scale multiplies a
disjoint set of 2D bins, in s-space
    H1[s_j, s_j]   = effective data information of ptll bin j (≈ N_j; less if BB-lite inflates it)
    H1[s_j, th_k]  = ptll-projected template of parameter k (events per unit theta_k)
(both exact for Gauss-Newton at the M1 point; the exact Hessian differs at O(residual)).
Then, at M0, the score (Rao) test for s = 1 with theta profiled is
    q_lin = r^T R^-1 r,  r = data - postfit (ptll),  R = Iss - T cov0 T^T
i.e. the linear chi2 with the residual covariance "data variance minus prediction variance".

Writes lin_<cfg>.npz with: T (39 x Nparm, s-space), Iss, Vpred, R, r, names.
No alphaS value is printed or stored (only templates and covariances).
"""

import sys

import numpy as np

S = slice(47, 86)


def run(cfg, wd):
    d = np.load(f"{wd}/arrays_{cfg}.npz")
    n0 = list(d["names0"])
    n1 = list(d["names1"])
    cov1 = d["cov1"]
    H1 = np.linalg.inv(cov1)
    x = d["x1"][S]
    # theta indices in M1 ordering for each M0 parameter
    idx1 = np.array([n1.index(n) for n in n0])
    # x -> s: s = x^2, ds/dx = 2x ; H_s = H_x / (2x)^2 ; H_s,theta = H_x,theta / (2x)
    J = 1.0 / (2 * x)
    Iss = H1[S, S] * np.outer(J, J)
    T = (
        H1[S][:, idx1] * J[:, None]
    )  # (39, Nparm): d(score_s)/d theta  == - template (sign below)
    # sign: NLL = sum(nu s - n ln(nu s)) -> d2NLL/ds dtheta = sum dnu/dtheta (1 - n/(nu s) ...)
    # at GN level = + sum_i dnu_i/dtheta = + ptll template.  Keep as is.
    cov0 = d["cov0"]
    Vpred = T @ cov0 @ T.T
    data = d["h_hist_data_obs"]
    post = d["h_hist_postfit_inclusive"]
    r = data - post
    R = np.diag(np.diag(Iss)) - Vpred
    out = dict(
        T=T,
        Iss=Iss,
        Vpred=Vpred,
        R=R,
        r=r,
        data=data,
        post=post,
        names=np.array(n0),
        hvar_post=d["hvar_hist_postfit_inclusive"],
        edges=d["edges"],
        x0=d["x0"],
        x1=d["x1"][idx1],
        cov0=cov0,
        cov1_theta=cov1[np.ix_(idx1, idx1)],
        var_prefit=d["var_prefit"],
        q=d["q"],
        chi2lin=d["chi2"],
        Iss_full=Iss,
    )
    np.savez(f"{wd}/lin_{cfg}.npz", **out)
    print(cfg)
    print(
        "  Iss offdiag max rel",
        np.abs(Iss - np.diag(np.diag(Iss))).max() / np.diag(Iss).max(),
    )
    print("  Iss/N  ", np.round(np.diag(Iss) / data, 4))
    print(
        "  sqrt(diag Vpred)/hvar_post^0.5",
        np.round(np.sqrt(np.diag(Vpred) / d["hvar_hist_postfit_inclusive"]), 3),
    )
    ev = np.linalg.eigvalsh(R)
    print("  R eig min/max", ev.min(), ev.max())
    q_lin = r @ np.linalg.solve(R, r)
    q_lin_dataonly = r @ (r / data)
    q_lin_Iss = r @ (r / np.diag(Iss))
    print(
        f"  q_lin (R=Iss-Vpred) {q_lin:.2f} | r^2/N {q_lin_dataonly:.2f} | r^2/Iss {q_lin_Iss:.2f} | rabbit q {float(d['q']):.2f} lin chi2 {float(d['chi2']):.2f}"
    )


if __name__ == "__main__":
    wd = sys.argv[1]
    for cfg in sys.argv[2:] or ["LAT", "NOLAT"]:
        run(cfg, wd)
