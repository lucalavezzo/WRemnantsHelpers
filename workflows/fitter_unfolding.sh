input_file="$1"
shift

while getopts "u:o:e:f:" opt; do
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
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

if [ -z "$input_file" ]; then
    echo "Input file required."
    exit 1
fi

if [ -z "$output_dir" ]; then
    output_dir=$(dirname $input_file)
    echo "Set output directory to: $output_dir"
fi

# unfolding command
unfolding_setup_command="python $WREM_BASE/scripts/rabbit/setupRabbit.py -i $input_file -o $output_dir --analysisMode unfolding --poiAsNoi --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' --genAxes 'ptVGen-absYVGen-helicitySig' --scaleNormXsecHistYields '0.05' --allowNegativeExpectation --realData --systematicType normal"
echo "Executing command: $unfolding_setup_command"
unfolding_setup_command_output=$(eval "$unfolding_setup_command 2>&1" | tee /dev/tty)

# extract the output file name, and the output directory, where we will put the fit results
unfolding_combine_file=$(echo "$unfolding_setup_command_output" | grep -oP '(?<=Write output file ).*')
echo $unfolding_combine_file
unfolding_combine_file=$(echo "$unfolding_combine_file" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g') # sanitize the output
echo "Unfolded file: $unfolding_combine_file"
output=$(dirname "$unfolding_combine_file")
echo "Output: $output"
echo

unfolding_command="rabbit_fit.py ${unfolding_combine_file} -o ${output} --binByBinStatType normal -t -1 --doImpacts --globalImpacts --saveHists --computeHistErrors --computeHistImpacts --computeHistCov --compositeModel -m Select 'ch0_masked' 'helicitySig:slice(0,1)' --postfix asimov ${extra_fit}"
echo "Executing command: $unfolding_command"
unfolding_command_output=$(eval "$unfolding_command 2>&1" | tee /dev/tty)
echo