# Setup combine and run the fit for the alphaS analysis

if [ -z "$1" ]; then
    echo "Usage: plotAlphaSVariations.sh input_file -o output_dir -e extra_args"
    exit 1
fi

input_file="$1"
shift

while getopts "o:e:" opt; do
    case $opt in
        o)
            output_dir=$OPTARG
            ;;
        e)
            extra_args=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

if [ -z "$output_dir" ]; then
    output_dir="./"
fi

# Check if $MY_PLOT_DIR is already in the $output_dir
if [[ ! "$output_dir" == *"$MY_PLOT_DIR"* ]]; then
    output_dir="$MY_PLOT_DIR/$output_dir"
fi
# if the output dir doesn't exist, create it
if [ ! -d "$output_dir" ]; then
    mkdir -p "$output_dir"
fi

# check if WREM_BASE is set
if [ -z "$WREM_BASE" ]; then
    echo "WREM_BASE is not set. Please source the setup.sh."
    exit 1
fi

echo "Output directory: $output_dir" 

command="rabbit_plot_hists.py --config $WREM_BASE'/utilities/styles/styles.py' $input_file --title CMS --subtitle Preliminary --rrange '0.98' '1.02' --legCols 1 -o $output_dir -m Project ch0 ptll --varName pdfAlphaS --varLabel '$\alpha_\mathrm{S}{\pm}1\sigma$' --yscale '1.25' ${extra_args}"
echo "Executing command: $command"
eval $command
