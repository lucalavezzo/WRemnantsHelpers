import os

pdfs_to_test = [
    "ct18",
    "ct18z",
    "nnpdf31",
    "nnpdf40",
    "pdf4lhc21",
    "msht20",
    "herapdf20",
]

pdfs_for_uncs = [
    "msht20mcrange_renorm",
    "msht20mbrange_renorm",
]

extra_pdfs = ["nnpdf30", "atlasWZj20", "herapdf20ext", "msht20an3lo"]

all_pdfs = pdfs_to_test + pdfs_for_uncs + extra_pdfs
for i, central_pdf in enumerate(pdfs_to_test):

    # TEST only run msht20 and msht20an3lo
    if central_pdf not in ["msht20", "msht20an3lo"]:
        continue

    command_extra = ""
    if central_pdf == "msht20":
        command_extra = " --theoryCorr scetlib_dyturbo scetlib_dyturboMSHT20Vars scetlib_dyturboMSHT20_pdfas scetlib_dyturboCT18Z_pdfas"
    elif central_pdf == "msht20an3lo":
        command_extra = " --theoryCorr scetlib_dyturbo scetlib_dyturboMSHT20an3loVars scetlib_dyturboMSHT20an3lo_pdfas scetlib_dyturboCT18Z_pdfas"

    other_pdfs = [pdf for pdf in all_pdfs if pdf != central_pdf]

    command = f"{os.environ['MY_WORK_DIR']}/workflows/histmaker.sh -e ' --filterProcs ZmumuPostVFP dataPostVFP -j 450 --pdfs {central_pdf} {' '.join(other_pdfs)} --postfix {central_pdf} {command_extra}' "
    try:
        os.system(command)
    except Exception as e:
        print(f"Error running command: {command}\n{e}")
