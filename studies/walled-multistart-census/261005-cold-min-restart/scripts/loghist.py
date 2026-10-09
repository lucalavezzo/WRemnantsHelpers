"""Parse the MAIN-fit minimiser history out of a rabbit_fit.py log (fitterAD / run_fit.sh style).

The main fit is the first block of "Iteration N: loss X [dt=..s elapsed=..s]" lines, ended by the first scipy
result dump ("message: ..."). Later blocks (saturated projection fits in the reference logs) are ignored.
A restart (--earlyStopping stall -> "restarting (#k)") starts a new callback whose iteration counter restarts at 0;
those are concatenated and flagged.

Nothing here is blinded-sensitive: the loss (NLL) is not blinded.
"""

import re

import numpy as np

IT_RE = re.compile(
    r"Iteration (\d+): loss ([-+0-9.eEinfa]+)\s+\[dt=([0-9.]+)s elapsed=([0-9.]+)s\]"
)
RES_KEYS = ("message", "success", "status", "fun", "nit", "nfev", "njev", "nhev")


def parse(path):
    txt = open(path, errors="replace").read().splitlines()
    it, loss, dt, el, restart_at = [], [], [], [], []
    res = {}
    timing = {}
    edm = None
    in_res = False
    done_main = False
    armed = None
    wall_info = None
    warm = None
    offset_el = 0.0
    for line in txt:
        clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
        if "[NPDampingWall] armed" in clean and armed is None:
            armed = clean.strip()
        if "[NPDampingWall] forms" in clean and wall_info is None:
            wall_info = clean.strip()
        if (
            ("WARM" in clean or "externalPostfit" in clean.split("rabbit_fit.py")[-1])
            and warm is None
            and "Loading" in clean
        ):
            warm = clean.strip()
        if done_main:
            m = re.search(
                r"\[timing\] (fitter\.minimize\(\)|loss_val_grad_hess\(\) \(postfit cov\)): ([0-9.]+) s",
                clean,
            )
            if m and m.group(1) not in timing:
                timing[m.group(1)] = float(m.group(2))
            m = re.search(r"edmval: ([-+0-9.eE]+)", clean)
            if m and edm is None:
                edm = float(m.group(1))
            continue
        if "restarting (#" in clean:
            restart_at.append(len(loss))
            offset_el = el[-1] if el else 0.0
        m = IT_RE.search(clean)
        if m and not in_res:
            it.append(int(m.group(1)))
            loss.append(float(m.group(2)))
            dt.append(float(m.group(3)))
            el.append(float(m.group(4)) + offset_el)
            continue
        if "message:" in clean:
            in_res = True
            res["message"] = clean.split("message:", 1)[1].strip()
            continue
        if in_res:
            s = clean.strip()
            k = s.split(":", 1)[0].strip()
            if k in RES_KEYS:
                v = s.split(":", 1)[1].strip()
                res[k] = v.replace("[0m", "")
                if k == "nhev":
                    in_res = False
                    done_main = True
    loss = np.array(loss)
    dt = np.array(dt)
    el = np.array(el)
    out = dict(
        n_iter=len(loss),
        loss=loss,
        dt=dt,
        elapsed=el,
        restarts=restart_at,
        result=res,
        timing=timing,
        edm_log=edm,
        armed=armed,
        wall_info=wall_info,
    )
    out.update(metrics(loss, dt))
    return out


def metrics(loss, dt, plateau_tol=1e-4):
    if len(loss) == 0:
        return {}
    d = np.diff(loss)
    rejected = (
        d == 0.0
    )  # scipy trust region keeps x on a rejected step: the callback sees the same loss
    increased = d > 0.0
    # longest run of consecutive rejected steps (each shrinks the trust radius by 4x in scipy)
    run = best = 0
    for r in rejected:
        run = run + 1 if r else 0
        best = max(best, run)
    # plateau: accepted steps that gain less than plateau_tol
    small = (d < 0) & (-d < plateau_tol)
    prun = pbest = 0
    for s in small | rejected:
        prun = prun + 1 if s else 0
        pbest = max(pbest, prun)
    return dict(
        n_rejected=int(rejected.sum()),
        longest_rejected_run=int(best),
        n_increase=int(increased.sum()),
        max_increase=float(d[increased].max()) if increased.any() else 0.0,
        n_small_steps=int(small.sum()),
        longest_plateau=int(pbest),
        dt_median=float(np.median(dt)),
        dt_max=float(dt.max()),
        total_elapsed=float(dt.sum()),
        loss_first=float(loss[0]),
        loss_last=float(loss[-1]),
    )
