import os
import argparse

preds = {
    "scetlib_dyturbo": {
        "alphaS": "scetlib_dyturboCT18Z_pdfas",
        "pdf": "ct18z",
    },
    "scetlib_dyturboMSHT20": {
        "alphaS": "scetlib_dyturboMSHT20_pdfas",
        "pdf": "msht20",
    },
    "scetlib_dyturboMSHT20an3lo": {
        "alphaS": "scetlib_dyturboMSHT20an3lo_pdfas",
        "pdf": "msht20an3lo",
    },
    "scetlib_dyturboN3p0LL_LatticeNP": {
        "alphaS": "scetlib_dyturboN3p0LL_LatticeNP_pdfas",
        "pdf": "ct18z",
    },
    "scetlib_dyturboN3p1LL": {
        "alphaS": "scetlib_dyturboN3p1LL_pdfas",
        "pdf": "ct18z",
    },
    "scetlib_dyturboN4p0LL": {
        "alphaS": "scetlib_dyturboN4p0LL_pdfas",
        "pdf": "ct18z",
    },
    "scetlib_nnlojetN3p1LLN3LO": {
        "alphaS": "scetlib_nnlojetN3p1LLN3LO_pdfas",
        "pdf": "msht20an3lo",
    },
    "scetlib_nnlojetN4p0LLN3LO": {
        "alphaS": "scetlib_nnlojetN4p0LLN3LO_pdfas",
        "pdf": "msht20an3lo",
    },
}

parser = argparse.ArgumentParser()
parser.add_argument(
    "--central-preds",
    nargs="+",
    default=list(preds.keys()),
    help="Prediction set names to use as central inputs. (default: %(default)s)",
)
args = parser.parse_args()

for i, central_pred in enumerate(args.central_preds):

    other_preds = [pred for pred in list(preds.keys()) if pred != central_pred]

    command = f"{os.environ['MY_WORK_DIR']}/workflows/histmaker.sh -e ' --filterProcs ZmumuPostVFP dataPostVFP -j 450 --theoryCorr {central_pred} {preds[central_pred]['alphaS']} {' '.join(other_preds)} --pdf {preds[central_pred]["pdf"]} --postfix {central_pred}' "
    try:
        os.system(command)
    except Exception as e:
        print(f"Error running command: {command}\n{e}")
