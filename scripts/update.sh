#!/bin/bash
set -euo pipefail

echo "Vendoring prod dependencies"
vendoring sync -v

# clean up
echo "Removing all .so libraries"
find opensafely/_vendor/ -name \*.so -exec rm {} \;
