# Setup combine and run the fit for the alphaS analysis

while getopts "i:o:e:" opt; do
    case $opt in
        i)
            input_file=$OPTARG
            ;;
        o)
            output_dir=$OPTARG
            ;;
        e)
            extra_setup=$OPTARG
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

# if no output dir is given, use the input file's directory
if [ -z "$output_dir" ]; then
    output_dir=$(dirname "$input_file")
else:
    output_dir=$(dirname "$input_file")
fi
# if the output dir doesn't exist, create it
if [ ! -d "$output_dir" ]; then
    mkdir -p "$output_dir"
fi
echo "Output directory: $output_dir" # setupCombine will create subdir in here

echo "Setting up combine..."
setup_output=$(python ${WREM_BASE}/scripts/combine/setupCombine.py -i $input_file --fitvar 'ptll-yll' --realData -o $output_dir --fitAlphaS --verbose 4 $extra_setup 2>&1 | tee /dev/tty)

combine_file=$(echo "$setup_output" | grep -oP '(?<=Write output file ).*')
echo "Combine file: $combine_file"
output=$(dirname "$combine_file")
echo "Output: $output"

wait 5
echo
echo "Running the fit..."
command="combinetf2_fit.py $combine_file -t '-1' --computeVariations -m Project ch0 ptll --computeHistErrors --doImpacts -o $output --globalImpacts --saveHists --saveHistsPerProcess --verbose 4"
echo "Executing command: $command"
eval $command
