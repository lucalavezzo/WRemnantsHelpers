# Shared settings for the gen-level cold NOLAT/LAT fits (sourced by run_fit.sh / run_pf.sh).
# rabbit: all3-bf-local = all3-local d573c1d (warm start + trust-constr precond + face-held impacts)
#         + cherry-pick of 196bfca (--blindingFrame) -> ece1d16, worktree /work/submit/lavezzo/rabbit-all3-bf.
RB=/work/submit/lavezzo/rabbit-all3-bf
export PYTHONPATH=$RB:${PYTHONPATH:-}
CE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
OUT=$CE/261017_gen_nominal_fits
# Gen-level card: iteration-0 real-data unfolding (261001, HEAD binning 20 ptV x 10 |Y|), sigma_UL + full covariance.
CARD=$CE/261009_ad_genlevel_iter0/sigmaUL_iter0_ad_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_adcorrAV_alphaS.hdf5
# Same AD cache as the reco nominal fits (770-bin |Y|<=2.5 subset); the model folds it onto the gen bins (coverage checked).
CACHE=$CE/scetlib_ad_caches/pdf62_y35_260921_y25
MODEL="--paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel cache=$CACHE/cache.npz conf=$CACHE/cache.conf gen_level=1 threads=128"
# Gen-level likelihood: covariance chi2 of the unfolded sigma_UL, no bin-by-bin stat (the card has none).
GEN="--covarianceFit --noBinByBinStat --noPostfitProfileBB"
# Same blinding frame as the reco fits (integer data -> 'data'); the sigma_UL card is non-integral (auto -> mc).
BLIND="--blindingFrame data"
# = fitterAD.sh --constraints
CONSTR="--constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
--minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-8 \
--minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerMaxiter 600"
# = fitterAD.sh --lattice (LatticeCSTerm defaults = LATFROZ_V3), tau = 8
LAT_ARGS="--regularizationStrength 8 -r wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTerm wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping"
latargs() { case "$1" in *NOLAT*) echo "";; *LAT*) echo "$LAT_ARGS";; esac; }
hdr() { echo "[run] $(date -Is) rabbit $RB @ $(git -C $RB rev-parse --short HEAD); WRemnants $(git -C $WREM_BASE rev-parse --short HEAD)"; python3 -c "import rabbit; print('[run] rabbit from', rabbit.__file__)"; }
