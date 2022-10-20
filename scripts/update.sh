#!/bin/bash
set -eou pipefail

version=${1-}

if test -z "$version"; then
    echo -n "No version specified - fetching latest tagged version..."
    version=$(git ls-remote --tags --refs --sort='v:refname' https://github.com/opensafely-core/job-runner | awk -F/ 'END{print$NF}')
    echo " found $version"
fi

grep -q "$version" vendor.in && { echo "Already at version $version"; exit; }

echo "Compiling vendor.txt from vendor.in with latest dependencies"

cat > vendor.in << EOF 
--requirement https://raw.githubusercontent.com/opensafely-core/job-runner/$version/requirements.prod.txt
git+https://github.com/opensafely-core/job-runner@$version
EOF

pip-compile vendor.in

# We can't (and don't want to) vendor this binary package but I can't find a
# way to prevent pip-tools from including it so we excise it here.
echo "Removing ruamel.yaml.clib dependency"
sed -i.bak -e 's/^\(ruamel[.-]yaml[.-]clib\)/# \1/' vendor.txt
rm -f vendor.txt.bak

echo "Vendoring all dependencies"
vendoring sync -v

# clean up
echo "Removing all .so libraries"
find opensafely/_vendor/ -name \*.so -exec rm {} \;
