# pulls and impacts for the alphaS analysis

while getopts "i:o:e:" opt; do
    case $opt in
        i)
            input_file=$OPTARG
            ;;
        o)
            output_dir=$OPTARG
            ;;
        e)
            extra=$OPTARG
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

if [ -n "$output_dir" ]; then
    echo "Output directory: $output_dir"
else
    current_date=$(date +"%H-%M_%d-%m-%Y")
    output_dir=~/public_html/alphaS/$current_date/
    echo "Output directory: $output_dir"
fi
mkdir -p $output_dir

command="combinetf2_plot_pulls_and_impacts.py $input_file --config '${WREM_BASE}/utilities/styles/styles.py' --scaleImpacts 1.5 --showNumbers --oneSidedImpacts --grouping max -o $output_dir --otherExtensions pdf png -n 50 --impactTitle '\$\alpha_\mathrm{S} in 10^{-3}\$' --title CMS --subtitle Preliminary ${extra}"

echo "Executing command: $command"
eval $command