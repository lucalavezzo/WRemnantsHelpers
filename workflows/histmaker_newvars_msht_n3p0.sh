# Run mz_dilepton histmaker with NewVars_MSHT20aN3LO_N3p0LL trio (analogous to ct18z_lambda6).
while getopts "p:e:" opt; do
    case $opt in
        p) postfix=$OPTARG ;;
        e) extra_args=$OPTARG ;;
        \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
    esac
done
if [ -z "$WREM_BASE" ]; then echo "WREM_BASE not set"; exit 1; fi
if [ -z "$MY_OUT_DIR" ]; then echo "MY_OUT_DIR not set"; exit 1; fi

current_date=$(date +"%y%m%d")
output_dir="${MY_OUT_DIR}/${current_date}_histmaker_dilepton_NewVars_MSHT20aN3LO_N3p0LL/"
if [ -n "$postfix" ]; then postfix="--postfix ${postfix}"; else postfix=""; fi
mkdir -p $output_dir
echo "Output directory: $output_dir"

command="python ${WREM_BASE}/scripts/histmakers/mz_dilepton.py --dataPath /scratch/submit/cms/wmass/NanoAOD/ -o $output_dir --maxFiles -1 --axes ptll yll --csVarsHist --forceDefaultName --theoryCorr 'scetlib_dyturbo_NewVars_MSHT20aN3LO_N3p0LL_N2LO' 'scetlib_dyturbo_NewVars_MSHT20aN3LO_N3p0LL_N2LO_pdfvars' 'scetlib_dyturbo_NewVars_MSHT20aN3LO_N3p0LL_N2LO_pdfas' 'scetlib_dyturbo_LatticeNP_MSHT20mbrange_N3p0LL_N2LO_pdfvars' 'scetlib_dyturbo_LatticeNP_MSHT20mcrange_N3p0LL_N2LO_pdfvars' --quarkMassCorr MiNNLO_Zbb ${extra_args} ${postfix}"
echo "Executing command: $command"
eval $command
