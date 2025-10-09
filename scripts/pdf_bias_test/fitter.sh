#!/bin/bash
# Setup rabbit and run the fit for the alphaS analysis at the detector level
# Using a given pdf histogram as pseudo-data

usage() {
    echo "Usage: fitter.sh <infile> <psuedo-data pdf hisotgram> -o <output_dir>"
    echo "-e <extra arguments for setupRabbit.py> -f <extra arguments for rabbit.py>"
    echo "--noSetup <skip setupRabbit.py call, carrot is infile>"
    echo "--2D <run 2D fit, ptll-yll>"
    echo "-h, --help <show this help message>"
    exit 1
}

if [ -z "$1" ]; then
    usage
fi

input_file=$1
pdf=$2
shift

do_setup=true
do_2D=false
do_impacts=false

PARSED=$(getopt -o o:e:f:h --long output:,extra-setup:,extra-fit:,noSetup,2D,help -- "$@")
if [[ $? -ne 0 ]]; then
    echo "Failed to parse arguments." >&2
    exit 1
fi
eval set -- "$PARSED"

while true; do
    case "$1" in
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
        --noSetup)
            do_setup=false
            shift
            ;;
        --2D)
            do_2D=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Unexpected option: $1" >&2
            exit 1
            ;;
    esac
done

if [ -z "$input_file" ]; then
    echo "Input file is required. Use -i to specify the input file."
    exit 1
fi

if [ -z "$pdf" ]; then
    echo "PDF set for pseudo-data is required."
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

if $do_setup; then
    echo "Setting up rabbit..."
    
    if $do_2D; then
        fitvar='ptll-yll'
    else
        fitvar='ptll-yll-cosThetaStarll_quantile-phiStarll_quantile'
    fi

    setup_commmand="python ${WREM_BASE}/scripts/rabbit/setupRabbit.py -i $input_file --fitvar $fitvar -o $output_dir --fitAlphaS --pseudoData $pdf --postfix $pdf $extra_setup"

    echo "$setup_commmand"
    setup_output=$($setup_commmand 2>&1 | tee /dev/tty)
    
    # extract the output file name, and the output directory, where we will put the fit results
    carrot=$(echo "$setup_output" | grep -oP '(?<=Write output file ).*')
    carrot=$(echo "$carrot" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g') # sanitize the output

else
    echo "Skipping setup rabbit..."
    carrot=$input_file
fi

echo "Rabbit file: $carrot"
output=$(dirname "$carrot")
echo "Output: $output"

echo
echo "Running the fit..."
fit_command="rabbit_fit.py $carrot -t -1 --computeVariations -m Project ch0 ptll --computeHistErrors --doImpacts -o $output --globalImpacts --saveHists --saveHistsPerProcess $extra_fit"
echo "$fit_command"
fit_output=$($fit_command 2>&1 | tee /dev/tty)