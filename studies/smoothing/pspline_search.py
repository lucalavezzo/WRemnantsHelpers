import os
import itertools
import lz4.frame
import pickle
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

lambda_values = [0.00001, 0.0001, 0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000, 10000]
knots_per_axis = itertools.product(
    [3, 5, 7, 10, 15, 20, 25, 30], [3, 5, 7, 10, 15]  # ptVgen knots  # absYVgen knots
)
degrees = [3]

# hyperparameter permutations
hp_perms = itertools.product(lambda_values, knots_per_axis, degrees)
hp_perms = list(hp_perms)

print(len(hp_perms))

# Thread-safe printing
print_lock = threading.Lock()


def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)


def process_hp_perm(hp_perm):
    """Process a single hyperparameter permutation"""
    safe_print(hp_perm)

    lam = hp_perm[0]
    knots = " ".join([str(x) for x in hp_perm[1]])
    _knots = "_".join([str(x) for x in hp_perm[1]])
    postfix = f"lam_{lam}_knots_{_knots}"

    command = f"python scripts/smoothing/pspline.py $WREM_BASE/wremnants-data/data/angularCoefficients/w_z_gen_dists_maxFiles_m1_pdfsByHelicity.hdf5  --select 'pdfVar pdf0CT18Z'  --hist nominal_gen_pdfCT18Z --refHist nominal_gen_pdf_uncorr --refHistSelect ''  --axes ptVgen absYVgen -o $MY_PLOT_DIR/250829_debug/ --ylim 0.9 1.1 -l {lam} -k {knots} --rrange 0.9 1.1 --postfix {postfix} --forceName"

    safe_print(command)

    # Execute the command
    os.system(command)

    try:
        # Read the output
        with lz4.frame.open(f"pspline/{postfix}/hist.pkl.lz4") as f:
            input_data = pickle.load(f)
            h_unroll = input_data["output"]["h_unroll"]
            h_pred_unroll = input_data["output"]["h_pred_unroll"]
            rms = (
                np.sum((h_unroll.values() - h_pred_unroll.values()) ** 2)
                / len(h_pred_unroll.values())
            ) ** 0.5

        return (hp_perm, rms)

    except Exception as e:
        safe_print(f"Error processing {hp_perm}: {e}")
        return (hp_perm, None)


# Main execution with multithreading
results = []
max_workers = 20  # Adjust based on your system capabilities

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # Submit all tasks
    future_to_hp_perm = {
        executor.submit(process_hp_perm, hp_perm): hp_perm for hp_perm in hp_perms
    }

    # Collect results as they complete
    for future in as_completed(future_to_hp_perm):
        hp_perm = future_to_hp_perm[future]
        try:
            result = future.result()
            if result[1] is not None:  # Only append successful results
                results.append(result)
        except Exception as exc:
            safe_print(f"HP permutation {hp_perm} generated an exception: {exc}")


now = datetime.now().strftime("%y%m%d_%H%M")
with open(f"pspline_search_{now}.pkl", "wb") as f:
    pickle.dump(results, f)
