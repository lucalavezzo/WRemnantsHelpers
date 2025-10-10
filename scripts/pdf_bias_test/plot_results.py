import os

import matplotlib.pyplot as plt
import numpy as np
import rabbit
import rabbit.io_tools

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
input_dir = f"{os.environ['MY_OUT_DIR']}/251009_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_pdfBiasTest_"
output_dir = f"{os.environ['MY_PLOT_DIR']}/251010_alphaS_pulls_and_impacts/"
os.makedirs(output_dir, exist_ok=True)


def main():
    results = []
    uncerts = []
    for central_pdf in central_pdfs_to_test:
        this_central_results = []
        this_central_uncerts = []
        input_file = f"{input_dir}{central_pdf}/fitresults.hdf5"

        for pseudodata_pdf in pseudodata_pdfs_to_test:
            result = f"nominal_pdf{pseudodata_pdf.upper()}_pdfVar"
            fitresult, _ = rabbit.io_tools.get_fitresult(
                input_file, result=result, meta=True
            )
            parms = fitresult["parms"].get()
            alphas = parms["pdfAlphaS"].value
            alphas_uncert = parms["pdfAlphaS"].variance**0.5
            alphas*=0.0015
            alphas_uncert*=0.0015
            this_central_results.append(alphas)
            this_central_uncerts.append(alphas_uncert)

        results.append(this_central_results)
        uncerts.append(this_central_uncerts)

    results_array = np.array(results)
    uncerts_array = np.array(uncerts)
    data_to_plot = results_array

    fig, ax = plt.subplots(
        figsize=(
            max(5.0, 1.1 * len(pseudodata_pdfs_to_test)),
            max(6.0, 1.2 * len(central_pdfs_to_test)),
        )
    )
    mesh = ax.imshow(
        data_to_plot,
        origin="lower",
        aspect="auto",
        cmap="viridis",
    )
    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_label(r"$\Delta\alpha_S$")

    y_positions = np.arange(len(central_pdfs_to_test))
    x_positions = np.arange(len(pseudodata_pdfs_to_test))

    ax.set_yticks(y_positions)
    ax.set_yticklabels([pdf.upper() for pdf in central_pdfs_to_test], rotation=45, ha="right")
    ax.set_xticks(x_positions)
    ax.set_xticklabels([pdf.upper() for pdf in pseudodata_pdfs_to_test])
    ax.set_ylabel("Central PDF")
    ax.set_xlabel("Pseudodata PDF")
    ax.set_title(r"PDF bias test")

    text_threshold = np.mean(results_array)
    for x_idx, _ in enumerate(pseudodata_pdfs_to_test):
        for y_idx, _ in enumerate(central_pdfs_to_test):
            value = results_array[y_idx, x_idx]
            uncert = uncerts_array[y_idx, x_idx]
            color = "white" if value < text_threshold else "black"
            ax.text(
                x_positions[x_idx],
                y_positions[y_idx],
                f"{value:.5f}\n$\\pm${uncert:.5f}",
                ha="center",
                va="center",
                color=color,
                fontsize=9,
            )

    ax.set_ylim(-0.5, len(central_pdfs_to_test) - 0.5)
    ax.set_xlim(-0.5, len(pseudodata_pdfs_to_test) - 0.5)

    plt.tight_layout()
    output_path = os.path.join(
        output_dir,
        "alphas_heatmap.pdf",
    )
    fig.savefig(output_path)
    fig.savefig(output_path.replace(".pdf", ".png"), dpi=100)
    print(f"Saved 2D alpha_s histogram to {output_path}")


if __name__ == "__main__":
    main()
