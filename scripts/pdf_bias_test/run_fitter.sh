#!/usr/bin/env bash

# Helper to iterate fitter.sh over every combination of predefined input files
# and pseudo-data PDF sets. Populate the INPUT_FILES and PDF_SETS arrays below.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
FITTER_SCRIPT="${SCRIPT_DIR}/fitter.sh"

if [[ ! -x "$FITTER_SCRIPT" ]]; then
    echo "Cannot execute ${FITTER_SCRIPT}. Ensure the script exists and is executable." >&2
    exit 1
fi

# Default output base directory. Override by exporting OUTPUT_BASE before running.
OUTPUT_BASE=${OUTPUT_BASE:-"${SCRIPT_DIR}/outputs"}
mkdir -p "$OUTPUT_BASE"

# Common extra arguments forwarded to fitter.sh. Leave empty or extend as needed.
COMMON_ARGS=(
    # "--2D"
    # "--extra-setup" "--maxAttempts 3"
    # "--extra-fit" "--saveWorkspace"
)

# -----------------------------------------------------------------------------
# Hard-coded lists of inputs and PDF sets.
# Every combination INPUT_FILES[x] × PDF_SETS[y] will be processed.
# -----------------------------------------------------------------------------
declare -a INPUT_FILES=(
    # "/absolute/or/relative/path/to/input_hist.root"
)

declare -a PDF_SETS=(
    # "NNPDF31_nnlo_as_0118"
)

if [[ ${#INPUT_FILES[@]} -eq 0 ]]; then
    echo "No input files defined. Edit run_fitter.sh and populate INPUT_FILES." >&2
    exit 1
fi

if [[ ${#PDF_SETS[@]} -eq 0 ]]; then
    echo "No PDF sets defined. Edit run_fitter.sh and populate PDF_SETS." >&2
    exit 1
fi

missing_inputs=0
for input_file in "${INPUT_FILES[@]}"; do
    if [[ -z "$input_file" ]]; then
        echo "Encountered empty entry in INPUT_FILES. Skipping." >&2
        continue
    fi
    if [[ ! -f "$input_file" ]]; then
        echo "Input file not found: ${input_file}." >&2
        ((missing_inputs++))
    fi
done

if (( missing_inputs > 0 )); then
    echo "Aborting because some input files are missing." >&2
    exit 1
fi

for input_file in "${INPUT_FILES[@]}"; do
    [ -n "$input_file" ] || continue

    input_label="$(basename "${input_file%.*}")"

    for pdf_set in "${PDF_SETS[@]}"; do
        if [[ -z "$pdf_set" ]]; then
            echo "Skipping empty PDF set entry for input ${input_file}." >&2
            continue
        fi

        pdf_safe=${pdf_set//[^A-Za-z0-9._-]/_}
        job_output_dir="${OUTPUT_BASE}/${input_label}__${pdf_safe}"
        mkdir -p "$job_output_dir"

        cmd=("${FITTER_SCRIPT}" "$input_file" "$pdf_set" -o "$job_output_dir")
        if (( ${#COMMON_ARGS[@]} )); then
            cmd+=("${COMMON_ARGS[@]}")
        fi

        echo
        echo ">>> Running fitter:"
        echo "        input = ${input_file}"
        echo "        pdf   = ${pdf_set}"
        echo "        out   = ${job_output_dir}"
        if (( ${#COMMON_ARGS[@]} )); then
            echo "        extra = ${COMMON_ARGS[*]}"
        fi

        "${cmd[@]}"
    done
done
