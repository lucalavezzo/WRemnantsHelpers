#!/usr/bin/env python3
"""Run rabbit_fit.py with in-process memory phase markers -- WITHOUT editing any checkout.

usage: python3 memprobe.py <rabbit_fit.py> <args...>

Wraps (monkeypatches, this process only) the phase entry points and prints one line
    [memmark] t=<s since start> unix=<epoch> phase=<name> rss= hwm= anon= file= thr= malloc_inuse= malloc_free= malloc_mmap= dt=
at each boundary. VmHWM is RESET (echo 5 > /proc/self/clear_refs) after every mark, so the hwm printed
at an "end" mark is the peak WITHIN that phase. glibc mallinfo2 sums every arena: inuse = uordblks+hblkhd,
free = fordblks (freed-but-retained heap), mmap = hblkhd (allocations served by mmap, >= M_MMAP_THRESHOLD).
"""
import ctypes, functools, os, runpy, sys, time

T0 = time.time()
_libc = ctypes.CDLL("libc.so.6")


class _MI2(ctypes.Structure):
    _fields_ = [
        (n, ctypes.c_size_t)
        for n in (
            "arena",
            "ordblks",
            "smblks",
            "hblks",
            "hblkhd",
            "usmblks",
            "fsmblks",
            "uordblks",
            "fordblks",
            "keepcost",
        )
    ]


_libc.mallinfo2.restype = _MI2


def _status():
    d = {}
    with open("/proc/self/status") as f:
        for line in f:
            k, _, v = line.partition(":")
            if k in ("VmRSS", "VmHWM", "RssAnon", "RssFile", "Threads"):
                d[k] = int(v.split()[0])
    return d


_tf_ok = [None]


def _tfmem():
    if _tf_ok[0] is False:
        return ""
    try:
        import tensorflow as tf

        m = tf.config.experimental.get_memory_info("CPU:0")
        _tf_ok[0] = True
        return f" tf_cur={m['current']/1e9:.3f} tf_peak={m['peak']/1e9:.3f}"
    except Exception as e:
        if _tf_ok[0] is None:
            print(
                f"[memmark] tf.config.experimental.get_memory_info('CPU:0') unavailable: {type(e).__name__}: {str(e)[:120]}",
                flush=True,
            )
        _tf_ok[0] = False
        return ""


def mark(phase, dt=None):
    s = _status()
    mi = _libc.mallinfo2()
    g = 1 / 1048576
    line = (
        f"[memmark] t={time.time()-T0:.1f} unix={time.time():.0f} phase={phase} "
        f"rss={s['VmRSS']*g:.2f} hwm={s['VmHWM']*g:.2f} anon={s['RssAnon']*g:.2f} file={s['RssFile']*g:.2f} "
        f"thr={s['Threads']} malloc_inuse={(mi.uordblks+mi.hblkhd)/2**30:.2f} "
        f"malloc_free={mi.fordblks/2**30:.2f} malloc_mmap={mi.hblkhd/2**30:.2f}"
        + (f" dt={dt:.1f}" if dt is not None else "")
        + _tfmem()
        + " [GiB]"
    )
    print(line, flush=True)
    try:
        with open("/proc/self/clear_refs", "w") as f:
            f.write("5")
    except OSError as e:
        print(f"[memmark] cannot reset VmHWM: {e}", flush=True)


_counts = {}


def wrap(obj, attr, name, every=1, maxn=None):
    fn = getattr(obj, attr)

    @functools.wraps(fn)
    def w(*a, **k):
        n = _counts.get(name, 0)
        _counts[name] = n + 1
        loud = (n < 3) or (n % every == 0)
        if maxn is not None and n >= maxn:
            loud = False
        if loud:
            mark(f"{name}#{n}:begin")
        t = time.time()
        r = fn(*a, **k)
        if loud:
            mark(f"{name}#{n}:end", time.time() - t)
        return r

    setattr(obj, attr, w)


def install():
    from rabbit import inputdata, fitter

    wrap(inputdata.FitInputData, "__init__", "datacard_read")
    wrap(fitter.Fitter, "__init__", "fitter_init")
    for m in ("loss_val_grad_hess", "loss_val_grad", "minimize", "load_fitresult"):
        if hasattr(fitter.Fitter, m):
            wrap(fitter.Fitter, m, f"Fitter.{m}")
    from wremnants.postprocessing.scetlib_ad import xsec_backend, param_model

    wrap(xsec_backend, "configure", "scetlib_configure")
    wrap(xsec_backend, "_load_with_raw_rules", "cache_load_raw_rules")
    wrap(xsec_backend.ScetlibADXsec, "__init__", "ScetlibADXsec_init")
    wrap(param_model.SCETlibADParamModel, "__init__", "model_build")
    wrap(param_model.SCETlibADParamModel, "_build_scale_envelope", "scale_envelope")
    import scetlib_tf

    C = scetlib_tf.ScetlibCachedXsecTF
    for m in ("values_and_jacobian", "values_jacobian_hessian", "hessian", "hvp"):
        wrap(C, m, f"sl.{m}", every=10)


if __name__ == "__main__":
    script = sys.argv[1]
    sys.argv = sys.argv[1:]
    mark("start")
    install()
    mark("instrumented")
    try:
        runpy.run_path(script, run_name="__main__")
    finally:
        mark("exit")
