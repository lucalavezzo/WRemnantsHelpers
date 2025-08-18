input_file_Z="$1"
shift
input_file_W="$1"
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

if [ -z "$input_file_Z" ] || [ -z "$input_file_W" ]; then
    echo "Input files for Z and W are required."
    exit 1
fi

if [ -z "$output_dir" ]; then
    output_dir=$(dirname $input_file_Z)
    echo "Set output directory to: $output_dir"
fi

# unfolding command
unfolding_setup_command="python $WREM_BASE/scripts/rabbit/setupRabbit.py -i $input_file_Z $input_file_W -o $output_dir --analysisMode unfolding --unfoldingLevel prefsr --poiAsNoi --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' 'eta-pt-charge' --genAxes 'ptVGen-absYVGen-helicitySig' 'absEtaGen-ptGen-qGen' --scaleNormXsecHistYields '0.05' --allowNegativeExpectation --realData --systematicType normal --unfoldSimultaneousWandZ"
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

unfolding_command="rabbit_fit.py ${unfolding_combine_file} -o ${output} --binByBinStatType normal -t -1 --doImpacts --globalImpacts --saveHists --computeHistErrors --computeHistImpacts --computeHistCov --compositeModel  -m Select 'ch0_masked' 'helicitySig:slice(0,1)' -m Select 'ch1_masked' --postfix asimov ${extra_fit}"
echo "Executing command: $unfolding_command"
unfolding_command_output=$(eval "$unfolding_command 2>&1" | tee /dev/tty)
echo

# extract the output file name, and the output directory, where we will put the fit results
unfolding_fitresult=$(echo "$unfolding_command_output" | grep -oP '(?<=Results written in file ).*')
unfolding_fitresult=$(echo "$unfolding_fitresult" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g') # sanitize the output
echo "Unfolded fit result: $unfolding_fitresult"
unfolding_output_dir=$(dirname "$unfolding_fitresult")
echo

theory_setup_command="python ${WREM_BASE}/scripts/rabbit/feedRabbitTheory.py ${unfolding_fitresult} --predGenerator 'scetlib_dyturbo' -o ${unfolding_output_dir} --systematicType log_normal --fitresultModel CompositeModel --fitW  ${extra_setup}"
echo "Executing command: $theory_setup_command"
theory_setup_command_output=$(eval "$theory_setup_command 2>&1" | tee /dev/tty)

# extract the output file name, and the output directory, where we will put the fit results
theory_file=$(echo "$theory_setup_command_output" | grep -oP '(?<=Write output file ).*')
echo $theory_file
theory_file=$(echo "$theory_file" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g') # sanitize the output
echo "Unfolded file: $theory_file"

fit_command="rabbit_fit.py ${theory_file} -o ${unfolding_output_dir} --externalCovariance --doImpacts --chisqFit --globalImpacts --saveHists --computeVariations --computeHistErrors"
echo "Executing command: $fit_command"
fit_command_output=$(eval "$fit_command 2>&1" | tee /dev/tty)
echo