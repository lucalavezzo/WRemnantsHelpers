# WRemnantsHelpers

Scripts, common recipes, and notes for the `WRemnants` framework.

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

## `notes/`
Contains notes on how to run certain studies in the `WRemnants` framework. 
These are not the outcomes of the studies, which are documented in slides.

## `workflows/`
Common recipes for running the `WRemnants` framework.

## `scripts/`
Scripts used for studies in the `WRemnants` framework.
Usually more specific than what is found in `workflows/`.

## `bin/`
Executables added to the `PATH` by `setup.sh`.

- `bin/run`: will run the script in the background, detach the process, and log the output to `logs/my_script_<date>.log`. Usage,
    
    ```
    run scripts/my_script.sh
    ```
    