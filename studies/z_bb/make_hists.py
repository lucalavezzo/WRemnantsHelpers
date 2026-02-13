import argparse
import os
import subprocess
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run z_bb histmaker for massive and massless samples with a unique run tag."
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Unique run tag appended to postfixes (default: timestamp).",
    )
    parser.add_argument(
        "--outdir",
        default=None,
        help="Output directory (default: $MY_OUT_DIR/<YYMMDD>_gen_massiveBottom).",
    )
    parser.add_argument(
        "--max-files-massive",
        type=int,
        default=-1,
        help="--maxFiles for Zbb_MiNNLO (default: -1).",
    )
    parser.add_argument(
        "--max-files-massless",
        type=int,
        default=1000,
        help="--maxFiles for Zmumu_MiNNLO (default: 1000).",
    )
    parser.add_argument(
        "-j",
        "--nthreads",
        type=int,
        default=50,
        help="Number of threads passed to histmaker.",
    )
    return parser.parse_args()


def run_cmd(cmd):
    print("Executing:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    args = parse_args()
    tag = args.tag or datetime.now().strftime("%H%M%S")
    date = datetime.now().strftime("%y%m%d")

    outdir = args.outdir or f"{os.environ['MY_OUT_DIR']}/{date}_gen_massiveBottom"
    postfix_massive = f"hadronsSel_massive_{tag}"
    postfix_massless = f"hadronsSel_massless_{tag}"

    histmaker = f"{os.environ['WREM_BASE']}/scripts/histmakers/w_z_gen_dists.py"
    data_path = "/scratch/submit/cms/wmass/NanoAOD/"

    cmd_massive = [
        "python",
        histmaker,
        "--dataPath",
        data_path,
        "--maxFiles",
        str(args.max_files_massive),
        "--addBottomAxis",
        "-o",
        outdir,
        "--filterProcs",
        "Zbb_MiNNLO",
        "-v",
        "4",
        "--postfix",
        postfix_massive,
        "-j",
        str(args.nthreads),
    ]
    cmd_massless = [
        "python",
        histmaker,
        "--dataPath",
        data_path,
        "--maxFiles",
        str(args.max_files_massless),
        "--addBottomAxis",
        "-o",
        outdir,
        "--pdf",
        "nnpdf31",
        "--filterProcs",
        "Zmumu_MiNNLO",
        "-v",
        "4",
        "--postfix",
        postfix_massless,
        "-j",
        str(args.nthreads),
    ]

    run_cmd(cmd_massive)
    run_cmd(cmd_massless)

    f_massive = f"{outdir}/w_z_gen_dists_maxFiles_{args.max_files_massive if args.max_files_massive >= 0 else 'm1'}_{postfix_massive}.hdf5"
    f_massless = f"{outdir}/w_z_gen_dists_maxFiles_{args.max_files_massless}_nnpdf31_{postfix_massless}.hdf5"
    print("\nProduced files:")
    print(f"massive:  {f_massive}")
    print(f"massless: {f_massless}")


if __name__ == "__main__":
    main()
