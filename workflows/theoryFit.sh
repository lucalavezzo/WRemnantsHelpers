#!/usr/bin/env bash

echo "theoryFit.sh is kept as a compatibility alias. Use theoryFitDirect.sh for the direct sigmaUL workflow."
exec "$(dirname "$0")/theoryFitDirect.sh" "$@"
