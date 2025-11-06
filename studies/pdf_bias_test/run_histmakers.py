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

    if central_pdf != "herapdf20":
        continue

    other_pdfs = [pdf for pdf in all_pdfs if pdf != central_pdf]

    command = f"{os.environ['MY_WORK_DIR']}/workflows/histmaker.sh -e ' --filterProcs ZmumuPostVFP dataPostVFP -j 300 --pdfs {central_pdf} {' '.join(other_pdfs)} --postfix {central_pdf}' "
    try:
        os.system(command)
    except Exception as e:
        print(f"Error running command: {command}\n{e}")
