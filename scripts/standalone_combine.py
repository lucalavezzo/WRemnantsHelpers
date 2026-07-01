"""Standalone combine for scetlib pkl outputs — bypasses scetlib_core import.

Mirrors combine_pkl_files / combine_jobs from scetlib-manage-condor-submit.py
but without the framework imports.

Also handles the scetlib "axis labels in file order vs data at section index"
mismatch (introduced when a conf is edited to move a section out of order):
if `--fix-alignment-shift` is passed, alignment-var pkls (filename matches
`_var_NNN.pkl` with NNN in --shift-vars range) have their data shifted
one position back (NNN → NNN-1) on the fly during read. Position NNN is
zeroed. The shift is idempotent — pkls that are already shifted are left
alone (detected by checking which position has data).
"""

import pickle, glob, os, sys, copy, re
import hist
import numpy as np

src_dir = sys.argv[1]
runcard_stem = sys.argv[2]  # e.g. "inclusive_Z_COM13_CT18Z_N3+0LL_newvals_lambda6_fine"
out_pkl = sys.argv[3]

pdfs = None
skip_missing = "--skip-missing" in sys.argv
ignore_config_diff = "--ignore-config-diff" in sys.argv
fix_alignment_shift = "--fix-alignment-shift" in sys.argv
shift_vars = set()  # filename var-numbers that need the N -> N-1 shift
# parse --pdfs <csv>
for i, a in enumerate(sys.argv):
    if a == "--pdfs" and i + 1 < len(sys.argv):
        pdfs = sys.argv[i + 1].split(",")
        pdfs = [int(p) if p.isdigit() else p for p in pdfs]
    if a == "--shift-vars" and i + 1 < len(sys.argv):
        for token in sys.argv[i + 1].split(","):
            if "-" in token:
                lo, hi = token.split("-")
                shift_vars.update(range(int(lo), int(hi) + 1))
            else:
                shift_vars.add(int(token))
if fix_alignment_shift and not shift_vars:
    # Sensible default for the CT18Z lambda6 production (alignment vars [43]–[48]).
    shift_vars = {43, 44, 45, 46, 47, 48}


_VARNUM_RE = re.compile(r"_var_(\d+)\.pkl$")


def maybe_shift_alignment_var(d, filename):
    """If filename indicates an alignment-var pkl needing the section-vs-filepos
    shift fix, move data from axis position NNN to NNN-1. Idempotent: skips if
    NNN-1 already has the data and NNN is empty.
    """
    if not fix_alignment_shift:
        return False
    m = _VARNUM_RE.search(filename)
    if m is None:
        return False
    vn = int(m.group(1))
    if vn not in shift_vars:
        return False
    h = d["hist"]
    if "vars" not in [a.name for a in h.axes]:
        return False
    vals = h.values()
    vars_var = h.variances()
    # detect state
    nz = np.abs(vals).sum(axis=tuple(range(vals.ndim - 1)))
    if vn >= len(nz):
        return False
    if nz[vn] == 0 and nz[vn - 1] > 0:
        return False  # already shifted
    if nz[vn] == 0 and nz[vn - 1] == 0:
        return False  # both empty — leave as-is
    # apply shift
    vals[..., vn - 1] = vals[..., vn]
    vals[..., vn] = 0.0
    vars_var[..., vn - 1] = vars_var[..., vn]
    vars_var[..., vn] = 0.0
    return True


pkl_files = sorted(glob.glob(os.path.join(src_dir, f"{runcard_stem}*pkl")))
print(f"Found {len(pkl_files)} pkl files in {src_dir}", flush=True)
if fix_alignment_shift:
    print(
        f"  alignment-shift fix enabled for var_NNN with NNN in {sorted(shift_vars)}",
        flush=True,
    )

comb_res = {
    "bins": None,
    "hist": None,
    "hist_err": None,
    "config": None,
    "meta_data": None,
}


def combine_pkl_files(comb, other, pdfs):
    if comb["hist"] is None:
        info = copy.deepcopy(other)
        if pdfs is not None:
            pdf_list = range(pdfs[0]) if len(pdfs) == 1 else pdfs
            axes = info["hist"].axes
            if axes.name[-1] != "vars":
                raise ValueError(
                    "Cannot combine ill-formed histogram. Expected vars axis at -1"
                )
            var_ax = hist.axis.StrCategory([f"pdf{i}" for i in pdf_list], name="vars")
            info["hist"] = hist.Hist(*axes[:-1], var_ax, info["hist"]._storage_type())
            comb = info
        else:
            return info
    combh = comb["hist"]
    otherh = other["hist"]
    pdf_set = None
    if combh.shape == otherh.shape:
        combh += otherh
    elif combh.shape[:-1] == otherh.shape[:-1]:
        var_name = list(otherh.axes["vars"])[0]
        try:
            var_idx = combh.axes["vars"].index(var_name)
        except KeyError:
            pdf_set = other["config"]["QCD"]["pdf_set"]
            var_idx = pdfs.index(pdf_set)
        combh[..., var_idx] = otherh[..., var_name].view(flow=True) + combh[
            ..., var_idx
        ].view(flow=True)
    else:
        raise ValueError(
            f"Cannot combine incompatible hists of shape {comb['hist'].shape} and {other['hist'].shape}"
        )
    pdf = None
    pdfas = None
    if "pdf_member" in comb["config"]["QCD"]:
        pdf = comb["config"]["QCD"].pop("pdf_member")
    if "alphas_mu0" in comb["config"]["QCD"]:
        pdfas = comb["config"]["QCD"].pop("alphas_mu0")
    other["config"]["QCD"].pop("pdf_member", None)
    other["config"]["QCD"].pop("alphas_mu0", None)
    if pdf_set:
        comb["config"]["QCD"]["pdf_set"] = pdf_set
    if not ignore_config_diff and comb["config"] != other["config"]:
        # Surface what differs for debugging
        for k in comb["config"]:
            if comb["config"].get(k) != other["config"].get(k):
                print(
                    f"DIFF in section [{k}]: {comb['config'].get(k)} vs {other['config'].get(k)}",
                    flush=True,
                )
        raise ValueError("Found different config files! Cannot combine.")
    if pdf is not None:
        comb["config"]["QCD"]["pdf_member"] = pdf
    if pdfas is not None:
        comb["config"]["QCD"]["alphas_mu0"] = pdfas
    return comb


n_shifted = 0
for i, fn in enumerate(pkl_files):
    if i % 100 == 0:
        print(f"  ... {i}/{len(pkl_files)}", flush=True)
    if not os.path.isfile(fn):
        if skip_missing:
            continue
        raise ValueError(f"Missing {fn}")
    with open(fn, "rb") as f:
        loaded = pickle.load(f)
    if maybe_shift_alignment_var(loaded, fn):
        n_shifted += 1
    comb_res = combine_pkl_files(comb_res, loaded, pdfs)

if fix_alignment_shift:
    print(f"Applied alignment-shift on-the-fly to {n_shifted} pkls", flush=True)

print(f"Writing combined → {out_pkl}", flush=True)
with open(out_pkl, "wb") as f:
    pickle.dump(comb_res, f)
print("done", flush=True)
print(
    f"Combined hist axes: {[a.name for a in comb_res['hist'].axes]}, shape={comb_res['hist'].shape}",
    flush=True,
)
print(f"vars axis labels: {list(comb_res['hist'].axes['vars'])}", flush=True)
