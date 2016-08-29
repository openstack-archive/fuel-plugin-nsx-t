#!/bin/bash -e
repo_dir=$1
manifest=$2

nsx_ubuntu_component=$(wget -q -c ${manifest} -O -|awk -v FS='=' '/NSX_HOST_COMPONENT_UBUNTU_1404_TAR/ {print $2}')
mkdir -p $repo_dir
cd $repo_dir
wget -c "http://${manager}:8080/${nsx_ubuntu_component}" -O - |tar --wildcards --strip-components=1 -zxvf - "*/"
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz
echo 'Label: nsx-t-protected-packages' > Release
chmod 755 .
chmod 644 *
apt-get update
