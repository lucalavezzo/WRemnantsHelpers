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
            extra_args=$OPTARG
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

if [ -z "$output_dir" ]; then
    echo "Output directory is required. Use -o to specify the output directory."
    exit 1
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

command="combinetf2_plot_hists.py --config $WREM_BASE'/utilities/styles/styles.py' $input_file --title CMS --subtitle Preliminary --rrange '0.90' '1.04' --legCols 1 -o $outpit_dir -m Project ch0 ptVGen --varName pdfAlphaS --varLabel '$\alpha_\mathrm{S}{\pm}1\sigma$' --yscale '1.25' --prefit"
echo "Executing command: $command"
eval $command
