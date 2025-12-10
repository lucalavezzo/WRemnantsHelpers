# Perform the unfolding with all the helicity xsecs in pt-eta-charge
# The fit for mW is performed using the same MC events

if [ -z "$1" ]; then
    echo "Usage: unfoldingMW.sh <input_file> -o <output_dir> -e <extra setupRabbit arguments> -f <extra rabbit_fit arguments>"
    exit 1
fi

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

if [ -z "$output_dir" ]; then
    output_dir=$(dirname $input_file)
    echo "Set output directory to: $output_dir"
fi

# unfolding command
unfolding_setup_command="python $WREM_BASE/scripts/rabbit/setupRabbit.py -i $input_file -o $output_dir --analysisMode unfolding --poiAsNoi --fitvar 'eta-pt-charge' --genAxes 'absEtaGen-ptGen-qGen' --scaleNormXsecHistYields '0.05' --allowNegativeExpectation --realData --systematicType 'normal'"
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


unfolding_command="rabbit_fit.py ${unfolding_combine_file} -o ${output} --binByBinStatType 'normal-multiplicative' -t -1 --doImpacts --globalImpacts --saveHists --computeHistErrors --computeHistImpacts --computeHistCov -m Select 'ch0_masked' --postfix asimov ${extra_fit}"
echo "Executing command: $unfolding_command"
unfolding_command_output=$(eval "$unfolding_command 2>&1" | tee /dev/tty)
echo

# extract the output file name, and the output directory, where we will put the fit results
unfolding_fitresult=$(echo "$unfolding_command_output" | grep -oP '(?<=Results written in file ).*')
unfolding_fitresult=$(echo "$unfolding_fitresult" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g') # sanitize the output
echo "Unfolded fit result: $unfolding_fitresult"
output=$(dirname "$unfolding_fitresult")
echo "Output: $output"
echo

setup_command="python $WREM_BASE/scripts/rabbit/setupRabbit.py -i $input_file -o ${output} --fitresult ${unfolding_fitresult} 'Select' 'ch0_masked' --fitvar 'absEtaGen-ptGen-qGen' --postfix theoryfit --baseName prefsr"
echo "Executing command: $setup_command"
setup_command_output=$(eval "$setup_command 2>&1" | tee /dev/tty)
echo

# extract the output file name, and the output directory, where we will put the fit results
combine_file=$(echo "$setup_command_output" | grep -oP '(?<=Write output file ).*')
combine_file=$(echo "$combine_file" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g') # sanitize the output
echo "Combine file: $combine_file"
output=$(dirname "$combine_file")
echo "Output: $output"
echo

combine_command="rabbit_fit.py ${combine_file} -o ${output} --doImpacts --globalImpacts --saveHists --computeHistErrors --computeVariations --chisqFit --externalCovariance -t -1 -m Basemodel ${extra_fit}"
echo "Executing command: $combine_command"
combine_command_output=$(eval "$combine_command 2>&1" | tee /dev/tty)
echo