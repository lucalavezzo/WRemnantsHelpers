"""
Convenience script to generate a the PDF gen histograms for a list of PDF sets.
"""

import os
import argparse
from datetime import datetime

THEORY_PREDS = [
    "scetlib_dyturboCT18Z_pdfas",
    "scetlib_dyturboMSHT20_pdfas",
    "scetlib_dyturboN3p1LL_pdfas",
    "scetlib_dyturboN4p0LL_pdfas",
    "scetlib_nnlojetN3p1LLN3LO_pdfas",
    "scetlib_nnlojetN4p0LLN3LO_pdfas",
]


def parse_arguments():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--preds",
        nargs="+",
        help="List of theory preds to process",
        default=THEORY_PREDS,
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        default=f"{os.environ['MY_OUT_DIR']}/{datetime.now().strftime('%y%m%d')}_alphaSByHelicity/",
    )
    parser.add_argument(
        "--skim",
        action="store_true",
        help="If set, will run a skimming step to only keep the PDF histograms in the file, saving a new output file.",
    )

    return parser.parse_args()


def main():

    args = parse_arguments()

    print("Generating histograms by helicity for the following theory preds:")
    print(args.preds)
    print("Will output to directory:")
    print(args.outdir)

    for pred in args.preds:

        command = f"python {os.environ['WREM_BASE']}/scripts/histmakers/w_z_gen_dists.py --useCorrByHelicityBinning --theoryCorr {pred} -o {args.outdir} --maxFiles '-1' -j 300 --filterProcs ZmumuPostVFP WplusmunuPostVFP WminusmunuPostVFP --addHelicityAxis"
        print(f"Running command: {command}")
        os.system(command)

        if args.skim:
            skim_command = f"python {os.environ['MY_WORK_DIR']}/scripts/open_narf_h5py.py {args.outdir}/w_z_gen_dists_{pred}_maxFiles_m1.hdf5 --filterHists pdfas --outfile {args.outdir}/w_z_gen_dists_{pred}_maxFiles_m1_skimmed.hdf5"
            print(f"Running skimming command: {skim_command}")
            os.system(skim_command)

    print("All done!")


if __name__ == "__main__":
    main()
