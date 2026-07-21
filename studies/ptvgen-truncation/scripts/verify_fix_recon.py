"""Quick-verify the min=1e-6 fix (RECON half, wremnants): REAL btgrid_tf.reconstruct.

Loads verify_fix_sample.npz (I_pert, C_nu, b_bar per grid) and reconstructs sigma with the
production btgrid_tf.reconstruct (node-Simpson over the raw bT nodes + J0 kernel), applying
the franksvals NP via fz_tf -- the exact fit-time path. Compares to the DE truth per qT.

Expect: control (1e-3,2000) ~0.44 at qT=100 (reproduces the deficit); 1e-6 grids -> ~1.00.
Also reveals the n_points needed (node-Simpson resolution in the support region).

Run: wremnants container (latest) + venv + setup.sh.
"""

import numpy as np

NPZ = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ptvgen-truncation/verify_fix_sample.npz"
EFF = dict(lambda_inf=1.0, lambda2=0.4, delta_lambda2=0.0, lambda4=0.4, lambda6=0.0)
GNU = dict(lambda2_nu=0.15, lambda4_nu=0.0, lambda_inf_nu=2.0)


def main():
    import tensorflow as tf
    from wremnants.postprocessing.scetlib_np import btgrid_tf as fz_tf

    d = np.load(NPZ)
    qTs = d["qTs"]
    svals = d["svals"]
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in d["grid_names"]]

    print(
        f"{'grid':>10} {'bmin':>7} {'N':>6} | " + "  ".join(f"qT={q:.0f}" for q in qTs)
    )
    print("-" * 60)
    for name in names:
        bT = d[f"bT_{name}"]
        Ipert = d[f"Ipert_{name}"]
        Cnu = d[f"Cnu_{name}"]
        bbar = d[f"bbar_{name}"]
        np.nan_to_num(Ipert, copy=False)
        np.nan_to_num(Cnu, copy=False)
        qT_per_bin = tf.constant(qTs, tf.float64)
        Y_per_bin = tf.zeros_like(qT_per_bin)
        sigma = fz_tf.reconstruct_batch_tf(
            qT_per_bin,
            bT,
            Ipert,
            Cnu,
            bbar,
            Y_per_bin,
            EFF,
            GNU,
            np_model="tanh_2",
            np_model_nu="tanh_2",
        ).numpy()
        ratios = sigma / svals
        print(
            f"{name:>10} {bT.min():7.0e} {bT.size:6d} | "
            + "  ".join(f"{r:9.5f}" for r in ratios)
            + "   | dev%: "
            + "  ".join(f"{100*(r-1):+7.3f}" for r in ratios)
        )


if __name__ == "__main__":
    main()
