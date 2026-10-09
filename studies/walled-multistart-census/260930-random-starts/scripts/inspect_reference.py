import numpy as np, sys
from rabbit import io_tools
from wremnants.postprocessing.scetlib_ad import np_damping_wall as W
from wremnants.postprocessing.scetlib_ad import params as P
from wremnants.postprocessing.scetlib_ad import response as R

for p in sys.argv[1:]:
    fr, meta = io_tools.get_fitresult(p, meta=True)
    h = fr["parms"].get()
    names = np.array(h.axes["parms"]).astype(str)
    hp = fr["parms_prefit"].get()
    namesp = np.array(hp.axes["parms"]).astype(str)
    print(p.split("/")[-1], len(names), (names == namesp).all())
    print(
        " pois",
        meta.get("pois"),
        " nois",
        meta.get("nois")[:5] if meta.get("nois") is not None else None,
        "priors",
        meta.get("param_priors"),
    )
    cov = fr["cov"].get().values()
    print(" cov shape", cov.shape, "sym", np.abs(cov - cov.T).max())
    entry = R.corr_config_from_meta(meta)
    cfg = entry["config"]
    f1, f2 = W.forms_from_corr_config(cfg)
    print(" forms", f1, f2, entry.get("tag"))
    lam = tuple(dict.fromkeys(W._TMD_LAMBDAS[f1] + W._CS_LAMBDAS[f2]))
    x = h.values()
    x0 = hp.values()
    for n in lam:
        sp = W.physical_spec(cfg, n)
        infit = n in names
        print(
            f"  {n:15s} infit={infit} spec={sp} anchor={P.corr_anchor_value(cfg,n)}",
            end="",
        )
        if infit:
            i = list(names).index(n)
            print(
                f" theta={x[i]:+.5f} prefit={x0[i]:+.5f} phys={W.physical_from_theta(sp,x[i]):.5f} sig={np.sqrt(cov[i,i]):.4f}"
            )
        else:
            print()
    # prefit nonzero entries (excluding alphaS)
    nz = [(n, v) for n, v in zip(names, x0) if v != 0 and n != "alphaS"]
    print(" prefit nonzero (excl alphaS):", len(nz), nz[:10])
    npn = [n for n in lam if n in names]
    mask = np.array([n not in npn and n != "alphaS" for n in names])
    C = cov[np.ix_(mask, mask)]
    ev = np.linalg.eigvalsh(C)
    print(" nonNP block", mask.sum(), "eig min/max", ev.min(), ev.max())
    try:
        np.linalg.cholesky(C)
        print(" cholesky OK")
    except Exception as e:
        print(" cholesky FAIL", e)
    d = np.sqrt(np.diag(cov))
    print(" zero-var params:", names[d == 0][:10], "nan:", np.isnan(cov).sum())
