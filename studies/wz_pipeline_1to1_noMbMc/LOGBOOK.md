# Run log

## 2026-03-04
- Created isolated output directory:
  - `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260304_zonly_compare_noMbMc_171212`
- Attempted theory branch (`feedRabbitTheory`) multiple times from:
  - `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260303_histmaker_dilepton_unfolding/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults_asimov.hdf5`
- Theory branch failure (reproducible):
  - `ValueError: Cannot rebin histogram due to incompatible edges for axis 'absYVGen'`
  - correction edges: `[0, 0.25, ..., 5.0]`
  - requested edges: `[0, 0.15, 0.3, ..., 2.5]`
- Ran MC-events branch in isolated dir:
  - setup output:
    - `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260304_zonly_compare_noMbMc_171212/ZMassDilepton_ptVGen_absYVGen_theoryfitViaMC_260304_zonly_compare_noMbMc_171212_mconly/ZMassDilepton.hdf5`
  - fit output:
    - `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260304_zonly_compare_noMbMc_171212/ZMassDilepton_ptVGen_absYVGen_theoryfitViaMC_260304_zonly_compare_noMbMc_171212_mconly/fitresults_260304_zonly_compare_noMbMc_171212_mconly.hdf5`
  - mb/mc removal used in fit:
    - `--freezeParameters 'pdfMSHT20m[bc]rangeSym.*'`

## 2026-03-04 (follow-up)
- Implemented nuisance filtering support in `feedRabbitTheory.py`:
  - added CLI args `--excludeNuisances` and `--keepNuisances`
  - applied filtering at systematic insertion points (`add_systematic`, `add_scale_systematic`)
- Theory branch rerun succeeded with nuisance exclusion:
  - command used `--excludeNuisances 'pdfMSHT20m[bc]range(Sym.*)?'`
  - output dir:
    - `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260304_theoryExcludeMbMc2_173308`
  - theory setup output:
    - `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260304_theoryExcludeMbMc2_173308/carrot_scetlib_dyturbo_CT18Z_N3p0LL_N2LO_ct18z_alphaS_260304_theoryExcludeMbMc2_173308.hdf5`
  - theory fit output:
    - `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260304_theoryExcludeMbMc2_173308/fitresults_260304_theoryExcludeMbMc2_173308.hdf5`
- MC branch rerun with setup-time exclusion succeeded:
  - command used `setupRabbit --excludeNuisances 'pdfMSHT20m[bc]range.*'`
  - output dir:
    - `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260304_zonly_compare_noMbMc_setupExcludeBroad_173409`
  - MC fit output:
    - `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260304_zonly_compare_noMbMc_setupExcludeBroad_173409/ZMassDilepton_ptVGen_absYVGen_theoryfitViaMC_260304_zonly_compare_noMbMc_setupExcludeBroad_173409/fitresults_260304_zonly_compare_noMbMc_setupExcludeBroad_173409.hdf5`
  - post-check on fit metadata:
    - `MBMC_COUNT = 0` (no `mbrange/mcrange` nuisances left)
