#!/bin/bash

# Setup combine and run the fit for the alphaS analysis (4D, detector-level)

if [ -z "$1" ]; then
    echo "Usage: fitter.sh <infile> -o <output_dir> -e <extra arguments for setupRabbit.py> -f <extra arguments for rabbit.py"
    exit 1
fi

input_file=$1
shift

while getopts "o:e:f:noSetup" opt; do
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
        noSetup)
            no_setup=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

if [ -z "$input_file" ]; then
    echo "Input file is required. Use -i to specify the input file."
    exit 1
fi

# check if WREM_BASE is set
if [ -z "$WREM_BASE" ]; then
    echo "WREM_BASE is not set. Please source the setup.sh in WRemnants."
    exit 1
fi
# if no output dir is given, use the input file's directory
if [ -z "$output_dir" ]; then
    output_dir=$(dirname "$input_file")
fi
# if the output dir doesn't exist, create it
if [ ! -d "$output_dir" ]; then
    mkdir -p "$output_dir"
fi
echo "Output directory: $output_dir" # setupCombine will create subdir in here

if [ ! "$no_setup" ]; then
    echo "Setting up rabbit..."
    setup_output=$(python ${WREM_BASE}/scripts/rabbit/setupRabbit.py -i $input_file --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' -o $output_dir --fitAlphaS $extra_setup 2>&1 | tee /dev/tty)
else
    echo "Skipping setup rabbit..."
fi

# extract the output file name, and the output directory, where we will put the fit results
carrot=$(echo "$setup_output" | grep -oP '(?<=Write output file ).*')
carrot=$(echo "$carrot" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g') # sanitize the output
echo "Rabbit file: $carrot"
output=$(dirname "$carrot")
echo "Output: $output"

echo
echo "Running the fit..."
command="rabbit_fit.py $carrot -t '-1' --computeVariations -m Project ch0 ptll --computeHistErrors --doImpacts -o $output --globalImpacts --saveHists --saveHistsPerProcess $extra_fit"
echo "$command"
eval $command