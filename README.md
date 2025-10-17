# WRemnantsHelpers

Scripts, common workflows, and studies for the `WRemnants` framework ecosystem: `WRemnants`, `rabbit`, `wums`, `narf`.

We assume you're running in the `WRemenants` singularity:

```
singularity run --bind /scratch/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest
```

To initialize the environment, 

```
source setup.sh
```

Which relies on the directory structure,

```
WRemnants/
WRemntantsHelpers/
```

## `scripts/`
General-purpose scripts for use with `WRemnants` and `rabbit`, for example, plotting histmaker outputs, opening fitresults, etc.

## `workflows/`
Common recipes for running the framework, such as running the full histmaker-fitter-plotting chain for given analyses, plotting the pulls and impacts for the $\alpha_S$ fits, etc.

## `studies/`
Scripts used for specific studies for analyses.
Usually more specific, less of general interest, than what is found in `workflows/`.

## `bin/`
Executables added to the `PATH` by `setup.sh`.

- `bin/run`: will run the script in the background, detach the process, and log the output to `logs/my_script_<date>.log`. Usage,
    
    ```
    run scripts/my_script.sh
    ```
    