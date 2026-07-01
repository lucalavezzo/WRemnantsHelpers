#!/usr/bin/env python3
"""
Driver for the partial-LRT freeze scan.

For each group in groups.yaml, build a singularity wrapper that re-runs the
reference rabbit_fit.py command with `--freezeParameters <group regexes>` and
a unique `--postfix freeze_<group>`, then launch it in the background via
nohup.

Pattern follows AGENTS.md: write wrapper to /tmp/, source /opt/venv inside
the container, source WRemnantsHelpers/setup.sh, run rabbit_fit. Logs go to
WRemnantsHelpers/logs/<task>_<timestamp>.log; output dir comes out of
the reference --outpath plus the unique --postfix.

Usage (must be run *outside* the container; this script is the launcher):

    python3 run_freeze_groups.py [--groups groups.yaml]
                                 [--only pdf_mb,scetlibNP]
                                 [--dry-run]
                                 [--baseline /path/to/fitresults_unblindedAsGroup.hdf5]
                                 [--mode decorr|inclusive]

Prints, for each group, the wrapper path, the expected output fitresults
path, and the log path. With --dry-run nothing is launched.
"""

import argparse
import datetime as _dt
import os
import re
import shlex
import subprocess
import sys
import textwrap
from pathlib import Path

import h5py
import yaml

REPO = Path("/home/submit/lavezzo/alphaS/WRemnantsHelpers")
WUMS = Path("/home/submit/lavezzo/alphaS/main/WRemnants/wums")
RABBIT = Path("/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")

SINGULARITY = (
    "singularity run --bind /scratch/,/work/,/home/,/ceph/ "
    "/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/"
    "wmassdevrolling:latest"
)


def read_baseline_command(baseline_h5):
    """Pull the original fit command and args from meta_info."""
    sys.path.insert(0, str(WUMS))
    sys.path.insert(0, str(RABBIT))
    from wums import ioutils  # noqa: E402

    with h5py.File(baseline_h5, "r") as f:
        meta = ioutils.pickle_load_h5py(f["meta"])
    mi = meta["meta_info"]
    return mi["command"], mi["args"]


def strip_one_value_flag(tokens, flag):
    """Remove `flag value` (exactly one value after) from a token list. In place."""
    out = []
    i = 0
    while i < len(tokens):
        if tokens[i] == flag and i + 1 < len(tokens):
            i += 2
            continue
        out.append(tokens[i])
        i += 1
    return out


def strip_multi_value_flag(tokens, flag):
    """Remove `flag v1 v2 ...` (until the next token starting with `-`)."""
    out = []
    i = 0
    while i < len(tokens):
        if tokens[i] == flag:
            i += 1
            while i < len(tokens) and not tokens[i].startswith("-"):
                i += 1
            continue
        out.append(tokens[i])
        i += 1
    return out


def build_command(base_command, group_name, freeze_regexes, mode):
    """Build the rabbit_fit command for a single group refit.

    `mode` only affects the postfix and output file naming. The decorrelation
    vs inclusive distinction lives entirely in the input ZMassDilepton.hdf5
    file, which is read from the supplied baseline's meta_info — point the
    --baseline flag at the appropriate file (inclusive baseline for partial
    LRT partner fits).
    """
    tokens = shlex.split(base_command.strip())

    # The reference command may already carry a --postfix and won't carry
    # --freezeParameters; strip both for safety, then append our own.
    tokens = strip_one_value_flag(tokens, "--postfix")
    tokens = strip_multi_value_flag(tokens, "--freezeParameters")

    tokens += ["--postfix", f"freeze_{group_name}_{mode}"]
    tokens += ["--freezeParameters", *freeze_regexes]

    return " ".join(shlex.quote(t) for t in tokens)


def expected_outpath(args, group_name, mode):
    """Where rabbit_fit will write its fitresults given the patched --postfix."""
    outdir = args["outpath"]
    name = args.get("outname", "fitresults.hdf5")
    base, ext = os.path.splitext(name)
    return str(Path(outdir) / f"{base}_freeze_{group_name}_{mode}{ext}")


def write_wrapper(cmd, wrapper_path):
    body = textwrap.dedent(
        f"""\
        #!/bin/bash
        set -e   # NOT -u, see AGENTS.md
        source /opt/venv/bin/activate
        cd {REPO}
        source setup.sh > /dev/null 2>&1 || true
        echo "BEGIN $(date)"
        {cmd}
        echo "DONE_OK $(date)"
        """
    )
    Path(wrapper_path).write_text(body)
    os.chmod(wrapper_path, 0o755)


def launch(wrapper_path, log_path):
    cmd = f"nohup {SINGULARITY} {wrapper_path} > {log_path} 2>&1 &"
    subprocess.Popen(cmd, shell=True, executable="/bin/bash")


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--groups", default=str(Path(__file__).parent / "groups.yaml"))
    p.add_argument(
        "--only", default=None, help="Comma-separated subset of group names to launch."
    )
    p.add_argument(
        "--baseline",
        default="/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
        "260429_fitAlphaSRapidityDecorr/"
        "ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_"
        "fitAlphaSRapidityDecorr_renamed_LambdaScale5p0/"
        "fitresults_unblindedAsGroup.hdf5",
        help="Reference baseline fit; its meta_info supplies the command.",
    )
    p.add_argument(
        "--mode",
        default="decorr",
        choices=["decorr", "inclusive"],
        help="Cosmetic tag for postfix / output filenames. Use "
        "'decorr' when --baseline points at the decorrelated "
        "fit; 'inclusive' when it points at the inclusive "
        "(single-alphaS) fit. The fit command itself comes "
        "from the baseline's meta_info either way.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print wrappers/commands but do not launch.",
    )
    p.add_argument(
        "--sequential",
        action="store_true",
        help="Pack all selected groups into a single wrapper that "
        "runs rabbit_fit back-to-back inside one singularity "
        "instance, instead of launching one nohup per group "
        "in parallel. Avoids pthread saturation when many "
        "groups are run together.",
    )
    args = p.parse_args()

    groups = yaml.safe_load(Path(args.groups).read_text())
    only = set(args.only.split(",")) if args.only else None

    base_cmd, base_args = read_baseline_command(args.baseline)
    print(f"Reference command:\n{base_cmd}\n")

    logs_dir = REPO / "logs"
    logs_dir.mkdir(exist_ok=True)
    stamp = _dt.datetime.now().strftime("%y%m%d_%H%M%S")

    selected = [(g, r) for g, r in groups.items() if only is None or g in only]

    if args.sequential and len(selected) > 1:
        # Pack all selected groups into a single wrapper that runs each
        # rabbit_fit call back-to-back inside one singularity instance.
        body_lines = [
            "#!/bin/bash",
            "set -e",
            "source /opt/venv/bin/activate",
            f"cd {REPO}",
            "source setup.sh > /dev/null 2>&1 || true",
            f'echo "BEGIN_SEQ $(date)"',
        ]
        for gname, regexes in selected:
            cmd = build_command(base_cmd, gname, regexes, args.mode)
            body_lines += [
                f'echo "=== START {gname} $(date) ==="',
                cmd,
                f'echo "=== END {gname} $(date) ==="',
            ]
        body_lines.append('echo "DONE_SEQ_OK $(date)"')

        wrapper = f"{Path(__file__).parent}/run_freeze_seq_{stamp}.sh"
        log = str(logs_dir / f"freeze_seq_{stamp}.log")
        Path(wrapper).write_text("\n".join(body_lines) + "\n")
        os.chmod(wrapper, 0o755)

        print(f"Sequential wrapper: {wrapper}")
        print(f"Log:                {log}")
        print(f"Groups (in order):  {', '.join(g for g, _ in selected)}")
        for gname, _ in selected:
            print(f"  expected output: {expected_outpath(base_args, gname, args.mode)}")

        if args.dry_run:
            print("\n--dry-run: no jobs launched.")
        else:
            launch(wrapper, log)
            print(f"\nLaunched sequentially. Tail with: tail -F {log}")
        return

    print(f"{'group':<25} {'expected output':<100} {'wrapper':<40} {'log'}")
    for gname, regexes in selected:
        cmd = build_command(base_cmd, gname, regexes, args.mode)
        wrapper = f"{Path(__file__).parent}/run_freeze_{gname}_{stamp}.sh"
        log = str(logs_dir / f"freeze_{gname}_{stamp}.log")
        out = expected_outpath(base_args, gname, args.mode)

        write_wrapper(cmd, wrapper)
        print(f"{gname:<25} {out:<100} {wrapper:<40} {log}")

        if not args.dry_run:
            launch(wrapper, log)

    if args.dry_run:
        print("\n--dry-run: no jobs launched.")
    else:
        print(f"\nLaunched. Tail logs with: tail -F {logs_dir}/freeze_*_{stamp}.log")


if __name__ == "__main__":
    main()
