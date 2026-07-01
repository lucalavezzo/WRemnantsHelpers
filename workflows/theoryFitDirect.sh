#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo "Usage: theoryFitDirect.sh <unfolding_fitresult> [-o|--output <output_dir>] [-e|--extra-setup <extra feedRabbitSigmaUL arguments>] [-f|--extra-fit <extra rabbit_fit arguments>] [-p|--postfix <postfix>] [-g|--generator <predGenerator>] [-n|--name <outname>] [--pdf <pdf>]"
    exit 1
fi

input_file="$1"
shift

output_dir=""
extra_setup=""
extra_fit=""
postfix=""
pred_generator="scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO"
outname="carrot"
pdf="ct18z"

while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            output_dir="$2"
            shift 2
            ;;
        -e|--extra-setup)
            extra_setup="$2"
            shift 2
            ;;
        -f|--extra-fit)
            extra_fit="$2"
            shift 2
            ;;
        -p|--postfix)
            postfix="$2"
            shift 2
            ;;
        -g|--generator)
            pred_generator="$2"
            shift 2
            ;;
        -n|--name)
            outname="$2"
            shift 2
            ;;
        --pdf)
            pdf="$2"
            shift 2
            ;;
        *)
            echo "Invalid option: $1" >&2
            exit 1
            ;;
    esac
done

if [ -z "$WREM_BASE" ]; then
    echo "WREM_BASE is not set. Please source setup.sh first."
    exit 1
fi

if [ -z "$output_dir" ]; then
    output_dir=$(dirname "$input_file")
    echo "Set output directory to: $output_dir"
fi

echo "Unfolded fit result: $input_file"
echo "Output directory: $output_dir"
echo "Postfix: $postfix"
echo "Prediction generator: $pred_generator"
echo

theory_setup_command="python ${WREM_BASE}/scripts/rabbit/feedRabbitSigmaUL.py --infile ${input_file} --predGenerator ${pred_generator} --pdfs ${pdf} -o ${output_dir} --systematicType log_normal --fitresultMapping 'Select helicitySig:0' --channelSigmaUL ch0_masked --outname ${outname} ${postfix:+--postfix ${postfix}} ${extra_setup}"
echo "Executing command: $theory_setup_command"
theory_setup_command_output=$(eval "$theory_setup_command 2>&1" | tee /dev/tty)

theory_file=$(echo "$theory_setup_command_output" | grep -oP '(?<=Write output file ).*')
theory_file=$(echo "$theory_file" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g')
echo "Direct-theory rabbit input: $theory_file"
echo

fit_command="rabbit_fit.py ${theory_file} -o ${output_dir} --doImpacts --covarianceFit --globalImpacts --saveHists --computeVariations --computeHistErrors --unblind -t 0 -m BaseMapping -m Project chSigmaUL ptVGen -m Project chSigmaUL absYVGen ${postfix:+--postfix ${postfix}} ${extra_fit}"
echo "Executing command: $fit_command"
fit_command_output=$(eval "$fit_command 2>&1" | tee /dev/tty)
echo
