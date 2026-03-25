#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo "Usage: theoryFitDirect.sh <unfolding_fitresult> -o <output_dir> -e <extra feedRabbitSigmaUL arguments> -f <extra rabbit_fit arguments> -p <postfix> -g <predGenerator>"
    exit 1
fi

input_file="$1"
shift

output_dir=""
extra_setup=""
extra_fit=""
postfix="direct_sigmaul"
pred_generator="scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO"
outname="direct_sigmaul_carrot"

while getopts "o:e:f:p:g:n:" opt; do
    case $opt in
        o)
            output_dir=$OPTARG
            ;;
        e)
            extra_setup=$OPTARG
            ;;
        f)
            extra_fit=$OPTARG
            ;;
        p)
            postfix=$OPTARG
            ;;
        g)
            pred_generator=$OPTARG
            ;;
        n)
            outname=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
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

theory_setup_command="python ${WREM_BASE}/scripts/rabbit/feedRabbitSigmaUL.py --infile ${input_file} --predGenerator ${pred_generator} -o ${output_dir} --systematicType log_normal --fitresultMapping 'Select helicitySig:0' --channelSigmaUL ch0_masked --outname ${outname} --postfix ${postfix} ${extra_setup}"
echo "Executing command: $theory_setup_command"
theory_setup_command_output=$(eval "$theory_setup_command 2>&1" | tee /dev/tty)

theory_file=$(echo "$theory_setup_command_output" | grep -oP '(?<=Write output file ).*')
theory_file=$(echo "$theory_file" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g')
echo "Direct-theory rabbit input: $theory_file"
echo

fit_command="rabbit_fit.py ${theory_file} -o ${output_dir} --doImpacts --covarianceFit --globalImpacts --saveHists --computeVariations --computeHistErrors --postfix ${postfix} ${extra_fit}"
echo "Executing command: $fit_command"
fit_command_output=$(eval "$fit_command 2>&1" | tee /dev/tty)
echo
