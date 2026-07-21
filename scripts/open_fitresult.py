import sys

sys.path.append("../../WRemnants/")
import matplotlib.pyplot as plt
import mplhep as hep
import rabbit.io_tools
import argparse
import wums.ioutils

parser = argparse.ArgumentParser(
    description="Read fit result from hdf5 file from rabbit or root file from combinetf1"
)
parser.add_argument(
    "infile",
    type=str,
    help="hdf5 file from rabbit or root file from combinetf1",
)
parser.add_argument(
    "--result",
    default=None,
    type=str,
    help="fitresults key in file (e.g. 'asimov'). Leave empty for data fit result.",
)
parser.add_argument(
    "--parms",
    nargs="+",
    default=[],
    type=str,
    help="Parms in the fitresult to print the pull of.",
)
parser.add_argument(
    "--path",
    default="",
    type=str,
    help="Open a specific, slash-separated, path inside the HDF5 file.",
)
parser.add_argument(
    "--show-meta",
    action="store_true",
    help="Print the meta info, which is suppressed by default.",
)
parser.add_argument(
    "--show-git-diff",
    action="store_true",
    help="Print the (verbose) git_diff entries in the meta info, which are "
    "suppressed by default.",
)
args = parser.parse_args()


def suppress_keys(obj, keys, _depth=0, _max_depth=12):
    """Return a copy of ``obj`` with any dict entries named in ``keys`` replaced
    by a short placeholder, recursing through nested dicts/lists.

    The fit-result meta nests ``meta_info``/``meta_info_input`` recursively
    (histmaker -> datacard -> fitresults), so verbose keys like ``git_diff``
    can appear at several depths. Heavy H5PickleProxy values are left untouched
    (not materialized).
    """
    if _depth > _max_depth or isinstance(obj, wums.ioutils.H5PickleProxy):
        return obj
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in keys:
                out[k] = (
                    f"<suppressed: {len(v)} chars>"
                    if isinstance(v, str)
                    else "<suppressed>"
                )
            else:
                out[k] = suppress_keys(v, keys, _depth + 1, _max_depth)
        return out
    if isinstance(obj, (list, tuple)):
        return type(obj)(suppress_keys(v, keys, _depth + 1, _max_depth) for v in obj)
    return obj


def fmt_scalar(v, indent):
    """Render a non-dict value. Multi-line strings become an indented block;
    H5PickleProxy values are described, not materialized."""
    cont = "    " * (indent + 1)
    if isinstance(v, wums.ioutils.H5PickleProxy):
        return "<H5PickleProxy (lazy, not loaded)>"
    if isinstance(v, str):
        s = v.strip("\n")
        if "\n" in s:
            return "\n" + "\n".join(cont + line for line in s.splitlines())
        return repr(s) if s == "" else s
    return repr(v)


def fmt_meta(obj, indent=0):
    """Recursively format a (possibly nested) metadata object as an indented,
    human-readable string. Scalar keys at each level are aligned."""
    pad = "    " * indent
    if isinstance(obj, wums.ioutils.H5PickleProxy):
        return f"{pad}<H5PickleProxy (lazy, not loaded)>"
    if isinstance(obj, dict):
        if not obj:
            return f"{pad}{{}}"
        keywidth = max(
            (len(str(k)) for k, v in obj.items() if not (isinstance(v, dict) and v)),
            default=0,
        )
        lines = []
        for k, v in obj.items():
            if isinstance(v, dict) and v:
                lines.append(f"{pad}{k}:")
                lines.append(fmt_meta(v, indent + 1))
            else:
                lines.append(f"{pad}{str(k):<{keywidth}} : {fmt_scalar(v, indent)}")
        return "\n".join(lines)
    return f"{pad}{fmt_scalar(obj, indent)}"


try:
    fitresult, meta = rabbit.io_tools.get_fitresult(
        args.infile, result=args.result, meta=True
    )
except ValueError as e:
    print(f"Error reading fit result: {e}")
    print("Try passing another value for --result.")
    sys.exit(1)

print("=" * 80)
print(f"Fit result keys : {sorted(fitresult.keys())}")
print(f"Meta data keys  : {sorted(meta.keys())}")
print("=" * 80)

if args.show_meta:

    suppress = set() if args.show_git_diff else {"git_diff"}
    for k, v in meta.items():
        print()
        print(f"### {k}")
        print(fmt_meta(suppress_keys(v, suppress), indent=1))

if args.path:
    print()
    full_path = args.path.split("/")
    h = fitresult

    print("-" * 20)
    print(f"Navigating to path: {args.path}")
    print()

    for p in full_path:
        print("-" * 20)
        print(f"At path: {p}")
        h = h[p]
        if type(h) is wums.ioutils.H5PickleProxy:
            h = h.get()

        if type(h) is dict:
            print(p, "has keys:", list(h.keys()))
            print(fmt_meta(suppress_keys(h, suppress), indent=1))
        else:
            print(f"{p}: {h}")
        print()
