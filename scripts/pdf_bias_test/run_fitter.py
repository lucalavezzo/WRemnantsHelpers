import os

# script parameters
central_pdfs_to_test = [
    "ct18",
    # "ct18z",
    # "nnpdf31",
    # "nnpdf40",
    # "pdf4lhc21",
    # "msht20",
    # "msht20an3lo"
]
pseudodata_pdfs_to_test = [
    "ct18",
    "ct18z",
    "nnpdf31",
    "nnpdf40",
    "pdf4lhc21",
    "msht20",
    #"msht20an3lo"
]
input_dir = f"{os.environ['MY_OUT_DIR']}/251009_histmaker_dilepton"

for pdf_central in central_pdfs_to_test:

    input_file = f"{input_dir}/mz_dilepton_{pdf_central}.hdf5"

    # for pdf_pseudodata in pseudodata_pdfs_to_test:

    #     extra_setup = f"--pseudoData nominal_pdf{pdf_pseudodata.upper()} --postfix {pdf_pseudodata} --pseudoDataIdxs 0 --pseudoDataAxes pdfVar"
    #     extra_fit = f"--pseudoData nominal_pdf{pdf_pseudodata.upper()}_pdfVar -t 0 --unblind"
    #     fit_command = f"{os.environ['MY_WORK_DIR']}/workflows/fitter.sh {input_file} -e '{extra_setup}' -f '{extra_fit}'"

    #     try:
    #         os.system(fit_command)    
    #     except Exception as e:
    #         print(f"Error running command: {fit_command}\n{e}")


    extra_setup = f"--pseudoData {" ".join(['nominal_pdf' + p.upper() for p in pseudodata_pdfs_to_test])} --postfix pdfBiasTest --pseudoDataIdxs 0 --pseudoDataAxes pdfVar"
    extra_fit = f"--pseudoData -t 0 --unblind"
    fit_command = f"{os.environ['MY_WORK_DIR']}/workflows/fitter.sh {input_file} -e '{extra_setup}' -f '{extra_fit}'"

    try:
        os.system(fit_command)    
    except Exception as e:
        print(f"Error running command: {fit_command}\n{e}")