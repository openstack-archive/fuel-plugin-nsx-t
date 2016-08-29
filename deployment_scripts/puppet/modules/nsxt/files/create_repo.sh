#!/bin/bash -e
repo_dir=$1
component_archive=$2

mkdir -p "$repo_dir"
cd "$repo_dir"
tar --wildcards --strip-components=1 -zxvf "$component_archive" "*/"
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz
echo 'Label: nsx-t-protected-packages' > Release
chmod 755 .
chmod 644 *
apt-get update
rm -fr "${component_archive:?}"
