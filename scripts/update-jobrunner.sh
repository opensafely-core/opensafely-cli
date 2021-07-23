#!/bin/bash
set -eou pipefail

script_dir="$( unset CDPATH && cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

exec "$script_dir/update-all-dependencies.sh" --upgrade-package opensafely-jobrunner
