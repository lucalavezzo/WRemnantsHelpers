input_file='/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//250714_unfolding_w_z_prefsr/Combination_ZMassDileptonWMass_EWFreePreFSR/Combination.hdf5'
fit_outdir="${MY_OUT_DIR}/250714_unfolding_w_z_prefsr/Combination_ZMassDileptonWMass_EWFreePreFSR/"

configs=(
    "-m Select 'ch0_masked' 'helicitySig:slice(0,1)' -m Select 'ch1_masked' --postfix 'sigmaUL_W'"
    "-m Select 'ch0_masked' 'helicitySig:slice(0,1)' --postfix 'sigmaUL'" 
    "-m Select 'ch1_masked' --postfix 'W'" 
)
fit_configs=(
    "--fitW"
    ""
    "--fitW --noFitSigmaUL"
)

noi_configs=(
    "--constrainMW"
    "--constrainAlphaS"
    ""
)
noi_outputs=(
    "alphaS"
    "mW"
    "alphaS_mW"
)

for i in "${!configs[@]}"; do

    cfg="${configs[$i]}"
    
    echo "rabbit_fit.py $input_file -t '-1' -o $fit_outdir --saveHists --computeHistErrors --computeHistImpacts --compositeModel --computeHistCov  $cfg"
    eval "rabbit_fit.py $input_file -t '-1' -o $fit_outdir --saveHists --computeHistErrors --computeHistImpacts --compositeModel --computeHistCov  $cfg"
    postfix=$(echo "$cfg" | grep -oP "(?<=--postfix ')[^']*" || echo "$cfg" | grep -oP "(?<=--postfix )\S+")

    fit_cfg="${fit_configs[$i]}"
    for j in "${!noi_configs[@]}"; do

        noi_cfg="${noi_configs[j]}"
        noi_out="${noi_outputs[j]}"
        echo "python $WREM_BASE/scripts/rabbit/feedRabbitTheory.py $fit_outdir/fitresults_$postfix.hdf5 -o $fit_outdir/fit_$postfix/ $fit_cfg $noi_cfg"
        python $WREM_BASE/scripts/rabbit/feedRabbitTheory.py $fit_outdir/fitresults_$postfix.hdf5 -o $fit_outdir/fit_$postfix/ $fit_cfg $noi_cfg

        echo "rabbit_fit.py ${fit_outdir}/fit_${postfix}//carrot_${noi_out}.hdf5 -o ${fit_outdir}/fit_${postfix}/ --postfix ${noi_out} --externalCovariance --doImpacts --chisqFit --globalImpacts --saveHists --computeVariations --computeHistErrors"
        rabbit_fit.py $fit_outdir/fit_$postfix//carrot_$noi_out.hdf5 -o $fit_outdir/fit_$postfix/ --postfix $noi_out --externalCovariance --doImpacts --chisqFit --globalImpacts --saveHists --computeVariations --computeHistErrors

        if [[ "$noi_out" == *"alphaS"* ]]; then
            echo "workflows/pullsAndImpacts.sh \"${fit_outdir}/fit_${postfix}/fitresults_${noi_out}.hdf5\" -o \"${MY_PLOT_DIR}/250724_fit/${postfix}_${noi_out}/\""
            ./workflows/pullsAndImpacts.sh "${fit_outdir}/fit_${postfix}/fitresults_${noi_out}.hdf5" -o "${MY_PLOT_DIR}/250724_fit/${postfix}_${noi_out}/"
        fi

        if [[ "$noi_out" == *"mW"* ]]; then
            echo "workflows/pullsAndImpactsMW.sh \"${fit_outdir}/fit_${postfix}/fitresults_${noi_out}.hdf5\" -o \"${MY_PLOT_DIR}/250724_fit/${postfix}_${noi_out}/\""
            ./workflows/pullsAndImpactsMW.sh "${fit_outdir}/fit_${postfix}/fitresults_${noi_out}.hdf5" -o "${MY_PLOT_DIR}/250724_fit/${postfix}_${noi_out}/"
        fi

    done
done
