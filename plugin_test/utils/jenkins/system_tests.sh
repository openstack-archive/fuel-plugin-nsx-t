#!/bin/sh
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# functions

INVALIDOPTS_ERR=100
NOJOBNAME_ERR=101
NOISOPATH_ERR=102
NOTASKNAME_ERR=103
NOWORKSPACE_ERR=104
NOISOFOUND_ERR=107
CDWORKSPACE_ERR=110
ISODOWNLOAD_ERR=111
INVALIDTASK_ERR=112

# Defaults

export REBOOT_TIMEOUT=${REBOOT_TIMEOUT:-5000}
export ALWAYS_CREATE_DIAGNOSTIC_SNAPSHOT=${ALWAYS_CREATE_DIAGNOSTIC_SNAPSHOT:-true}

ShowHelp() {
cat << EOF
System Tests Script

It can perform several actions depending on Jenkins JOB_NAME it's ran from
or it can take names from exported environment variables or command line options
if you do need to override them.

-w (dir)    - Path to workspace where fuelweb git repository was checked out.
              Uses Jenkins' WORKSPACE if not set
-e (name)   - Directly specify environment name used in tests
              Uses ENV_NAME variable is set.
-j (name)   - Name of this job. Determines ISO name, Task name and used by tests.
              Uses Jenkins' JOB_NAME if not set
-v          - Do not use virtual environment
-V (dir)    - Path to python virtual environment
-i (file)   - Full path to ISO file to build or use for tests.
              Made from iso dir and name if not set.
-t (name)   - Name of task this script should perform. Should be one of defined ones.
              Taken from Jenkins' job's suffix if not set.
-o (str)    - Allows you any extra command line option to run test job if you
              want to use some parameters.
-a (str)    - Allows you to path NOSE_ATTR to the test job if you want
              to use some parameters.
-A (str)    - Allows you to path  NOSE_EVAL_ATTR if you want to enter attributes
              as python expressions.
-m (name)   - Use this mirror to build ISO from.
              Uses 'srt' if not set.
-U          - ISO URL for tests.
              Null by default.
-r (yes/no) - Should built ISO file be places with build number tag and
              symlinked to the last build or just copied over the last file.
-b (num)    - Allows you to override Jenkins' build number if you need to.
-l (dir)    - Path to logs directory. Can be set by LOGS_DIR evironment variable.
              Uses WORKSPACE/logs if not set.
-d          - Dry run mode. Only show what would be done and do nothing.
              Useful for debugging.
-k          - Keep previously created test environment before tests run
-K          - Keep test environment after tests are finished
-h          - Show this help page

Most variables uses guesses from Jenkins' job name but can be overriden
by exported variable before script is run or by one of command line options.

You can override following variables using export VARNAME="value" before running this script
WORKSPACE  - path to directory where Fuelweb repository was checked out by Jenkins or manually
JOB_NAME   - name of Jenkins job that determines which task should be done and ISO file name.

If task name is "iso" it will make iso file
Other defined names will run Nose tests using previously built ISO file.

ISO file name is taken from job name prefix
Task name is taken from job name suffix
Separator is one dot '.'

For example if JOB_NAME is:
mytest.somestring.iso
ISO name: mytest.iso
Task name: iso
If ran with such JOB_NAME iso file with name mytest.iso will be created

If JOB_NAME is:
mytest.somestring.node
ISO name: mytest.iso
Task name: node
If script was run with this JOB_NAME node tests will be using ISO file mytest.iso.

First you should run mytest.somestring.iso job to create mytest.iso.
Then you can ran mytest.somestring.node job to start tests using mytest.iso and other tests too.
EOF
}

GlobalVariables() {
  # where built iso's should be placed
  # use hardcoded default if not set before by export
  ISO_DIR="${ISO_DIR:=/var/www/fuelweb-iso}"

  # name of iso file
  # taken from jenkins job prefix
  # if not set before by variable export
  if [ -z "${ISO_NAME}" ]; then
    ISO_NAME="${JOB_NAME%.*}.iso"
  fi

  # full path where iso file should be placed
  # make from iso name and path to iso shared directory
  # if was not overriden by options or export
  if [ -z "${ISO_PATH}" ]; then
    ISO_PATH="${ISO_DIR}/${ISO_NAME}"
  fi

  # what task should be ran
  # it's taken from jenkins job name suffix if not set by options
  if [ -z "${TASK_NAME}" ]; then
    TASK_NAME="${JOB_NAME##*.}"
  fi

  # do we want to keep iso's for each build or just copy over single file
  ROTATE_ISO="${ROTATE_ISO:=yes}"

  # choose mirror to build iso from. Default is 'srt' for Saratov's mirror
  # you can change mirror by exporting USE_MIRROR variable before running this script
  USE_MIRROR="${USE_MIRROR:=srt}"

  # only show what commands would be executed but do nothing
  # this feature is usefull if you want to debug this script's behaviour
  DRY_RUN="${DRY_RUN:=no}"

  VENV="${VENV:=yes}"
}

GetoptsVariables() {
  while getopts ":w:j:i:t:o:a:A:m:U:r:b:V:l:dkKe:v:h" opt; do
    case $opt in
      w)
        WORKSPACE="${OPTARG}"
        ;;
      j)
        JOB_NAME="${OPTARG}"
        ;;
      i)
        ISO_PATH="${OPTARG}"
        ;;
      t)
        TASK_NAME="${OPTARG}"
        ;;
      o)
        TEST_OPTIONS="${TEST_OPTIONS} ${OPTARG}"
        ;;
      a)
        NOSE_ATTR="${OPTARG}"
        ;;
      A)
        NOSE_EVAL_ATTR="${OPTARG}"
        ;;
      m)
        USE_MIRROR="${OPTARG}"
        ;;
      U)
        ISO_URL="${OPTARG}"
        ;;
      r)
        ROTATE_ISO="${OPTARG}"
        ;;
      V)
        VENV_PATH="${OPTARG}"
        ;;
      l)
        LOGS_DIR="${OPTARG}"
        ;;
      k)
        KEEP_BEFORE="yes"
        ;;
      K)
        KEEP_AFTER="yes"
        ;;
      e)
        ENV_NAME="${OPTARG}"
        ;;
      d)
        DRY_RUN="yes"
        ;;
      v)
        VENV="no"
        ;;
      h)
        ShowHelp
        exit 0
        ;;
      \?)
        echo "Invalid option: -$OPTARG"
        ShowHelp
        exit $INVALIDOPTS_ERR
        ;;
      :)
        echo "Option -$OPTARG requires an argument."
        ShowHelp
        exit $INVALIDOPTS_ERR
        ;;
    esac
  done
}

CheckVariables() {

  if [ -z "${JOB_NAME}" ]; then
    echo "Error! JOB_NAME is not set!"
    exit $NOJOBNAME_ERR
  fi
  if [ -z "${ISO_PATH}" ]; then
    echo "Error! ISO_PATH is not set!"
    exit $NOISOPATH_ERR
  fi
  if [ -z "${TASK_NAME}" ]; then
    echo "Error! TASK_NAME is not set!"
    exit $NOTASKNAME_ERR
  fi
  if [ -z "${WORKSPACE}" ]; then
    echo "Error! WORKSPACE is not set!"
    exit $NOWORKSPACE_ERR
  fi

  if [ -z "${POOL_PUBLIC}" ]; then
    export POOL_PUBLIC='172.16.0.0/24:24'
  fi
  if [ -z "${POOL_MANAGEMENT}" ]; then
    export POOL_MANAGEMENT='172.16.1.0/24:24'
  fi
  if [ -z "${POOL_PRIVATE}" ]; then
    export POOL_PRIVATE='192.168.0.0/24:24'
  fi

  # Vcenter variables
  if [ -z "${DISABLE_SSL}" ]; then
    export DISABLE_SSL="true"
  fi
  if [ -z "${VCENTER_USE}" ]; then
    export VCENTER_USE="true"
  fi
  if [ -z "${VCENTER_IP}" ]; then
    export VCENTER_IP="172.16.0.254"
  fi
  if [ -z "${VCENTER_USERNAME}" ]; then
    export VCENTER_USERNAME="administrator@vsphere.local"
  fi
  if [ -z "${VCENTER_PASSWORD}" ]; then
    echo "Error! VCENTER_PASSWORD is not set!"
    exit 1
  fi
  if [ -z "${VC_DATACENTER}" ]; then
    export VC_DATACENTER="Datacenter"
  fi
  if [ -z "${VC_DATASTORE}" ]; then
    export VC_DATASTORE="nfs"
  fi
  if [ -z "${VCENTER_IMAGE_DIR}" ]; then
    export VCENTER_IMAGE_DIR="/openstack_glance"
  fi
  if [ -z "${WORKSTATION_NODES}" ]; then
    export WORKSTATION_NODES="esxi1 esxi2 esxi3 vcenter trusty nsx-edge"
  fi
  if [ -z "${WORKSTATION_IFS}" ]; then
    export WORKSTATION_IFS="vmnet1 vmnet2 vmnet5"
  fi
  if [ -z "${VCENTER_CLUSTERS}" ]; then
    export VCENTER_CLUSTERS="Cluster1,Cluster2"
  fi
  if [ -z "${WORKSTATION_SNAPSHOT}" ]; then
    echo "Error! WORKSTATION_SNAPSHOT is not set!"
    exit 1
  fi
  if [ -z "${WORKSTATION_USERNAME}" ]; then
    echo "Error! WORKSTATION_USERNAME is not set!"
    exit 1
  fi
  if [ -z "${WORKSTATION_PASSWORD}" ]; then
    echo "Error! WORKSTATION_PASSWORD is not set!"
    exit 1
  fi

  # NSXt variables
  if [ -z "${NSXT_PLUGIN_PATH}" ]; then
    echo "Error! NSXT_PLUGIN_PATH is not set!"
    exit 1
  fi
  if [ -z "${NEUTRON_SEGMENT_TYPE}" ]; then
    export NEUTRON_SEGMENT_TYPE="tun"
  fi
  if [ -z "${NSXT_INSECURE}" ]; then
    export NSXT_INSECURE='true'
  fi
  if [ -z "${NSXT_MANAGERS_IP}" ]; then
    export NSXT_MANAGERS_IP="172.16.0.249"
  fi
  if [ -z "${NSXT_USER}" ]; then
    export NSXT_USER='admin'
  fi
  if [ -z "${NSXT_PASSWORD}" ]; then
    echo "Error! NSXT_PASSWORD is not set!"
    exit 1
  fi
  if [ -z "${NSXT_OVERLAY_TZ_UUID}" ]; then
    export NSXT_OVERLAY_TZ_UUID='0eeb1b85-c826-403d-8762-6a9c23a4f132'
  fi
  if [ -z "${NSXT_VLAN_TZ_UUID}" ]; then
    export NSXT_VLAN_TZ_UUID='8efe20d2-e71a-4d6e-acdd-f78a2ec2e90c'
  fi
  if [ -z "${NSXT_TIER0_ROUTER_UUID}" ]; then
    export NSXT_TIER0_ROUTER_UUID='606acd01-c5f8-40ea-ae20-9a91eb7ebcb4'
  fi
  if [ -z "${NSXT_EDGE_CLUSTER_UUID}" ]; then
    export NSXT_EDGE_CLUSTER_UUID='c53d602a-4010-47cc-a8b1-4ef11d0a3edd'
  fi
  if [ -z "${NSXT_UPLINK_PROFILE_UUID}" ]; then
    export NSXT_UPLINK_PROFILE_UUID='99864272-b34f-46a5-89c8-5657fa7042ea'
  fi
  if [ -z "${NSXT_CONTROLLER_IP_POOL_UUID}" ]; then
    export NSXT_CONTROLLER_IP_POOL_UUID='2e06fcb2-7c5b-4515-a7a9-98809c7b863a'
  fi
  if [ -z "${NSXT_CONTROLLER_PNICS_PAIRS}" ]; then
    export NSXT_CONTROLLER_PNICS_PAIRS='enp0s6:uplink'
  fi
  if [ -z "${NSXT_COMPUTE_IP_POOL_UUID}" ]; then
    export NSXT_COMPUTE_IP_POOL_UUID='2e06fcb2-7c5b-4515-a7a9-98809c7b863a'
  fi
  if [ -z "${NSXT_COMPUTE_PNICS_PAIRS}" ]; then
    export NSXT_COMPUTE_PNICS_PAIRS='enp0s6:uplink'
  fi

  if [ -z "${NSXT_FLOATING_IP_RANGE}" ]; then
    export NSXT_FLOATING_IP_RANGE='172.16.212.2-172.16.212.40'
  fi
  if [ -z "${NSXT_FLOATING_NET_CIDR}" ]; then
    export NSXT_FLOATING_NET_CIDR='172.16.212.0/24'
  fi
  if [ -z "${NSXT_ROUTING_NET_CIDR}" ]; then
    export NSXT_ROUTING_NET_CIDR='172.16.214.0/30'
  fi
  if [ -z "${NSXT_FLOATING_NET_GW}" ]; then
    export NSXT_FLOATING_NET_GW='172.16.212.1'
  fi
  if [ -z "${NSXT_INTERNAL_NET_CIDR}" ]; then
    export NSXT_INTERNAL_NET_CIDR='192.168.251.0/24'
  fi
  if [ -z "${NSXT_INTERNAL_NET_DNS}" ]; then
    export NSXT_INTERNAL_NET_DNS='8.8.8.8'
  fi

  # Export settings
  if [ -z "${NODE_VOLUME_SIZE}" ]; then
    export NODE_VOLUME_SIZE=350
  fi
  if [ -z "${ADMIN_NODE_MEMORY}" ]; then
    export ADMIN_NODE_MEMORY=4096
  fi
  if [ -z "${ADMIN_NODE_CPU}" ]; then
    export ADMIN_NODE_CPU=4
  fi
  if [ -z "${SLAVE_NODE_MEMORY}" ]; then
    export SLAVE_NODE_MEMORY=4096
  fi
  if [ -z "${SLAVE_NODE_CPU}" ]; then
    export SLAVE_NODE_CPU=4
  fi
}

CdWorkSpace() {
    # chdir into workspace or fail if could not
    if [ "${DRY_RUN}" != "yes" ]; then
        cd "${WORKSPACE}"
        ec=$?

        if [ "${ec}" -gt "0" ]; then
            echo "Error! Cannot cd to WORKSPACE!"
            exit $CDWORKSPACE_ERR
        fi
    else
        echo cd "${WORKSPACE}"
    fi
}

RunTest() {
    # Run test selected by task name

    # check if iso file exists
    if [ ! -f "${ISO_PATH}" ]; then
        if [ -z "${ISO_URL}" -a "${DRY_RUN}" != "yes" ]; then
            echo "Error! File ${ISO_PATH} not found and no ISO_URL (-U key) for downloading!"
            exit $NOISOFOUND_ERR
        else
            if [ "${DRY_RUN}" = "yes" ]; then
                echo wget -c ${ISO_URL} -O ${ISO_PATH}
            else
                echo "No ${ISO_PATH} found. Trying to download file."
                wget -c ${ISO_URL} -O ${ISO_PATH}
                rc=$?
                if [ $rc -ne 0 ]; then
                    echo "Failed to fetch ISO from ${ISO_URL}"
                    exit $ISODOWNLOAD_ERR
                fi
            fi
        fi
    fi

    if [ -z "${VENV_PATH}" ]; then
        VENV_PATH="/home/jenkins/venv-nailgun-tests"
    fi

    # run python virtualenv
    if [ "${VENV}" = "yes" ]; then
        if [ "${DRY_RUN}" = "yes" ]; then
            echo . $VENV_PATH/bin/activate
        else
            . $VENV_PATH/bin/activate
        fi
    fi

    if [ "${ENV_NAME}" = "" ]; then
      ENV_NAME="${JOB_NAME}_system_test"
    fi

    if [ "${LOGS_DIR}" = "" ]; then
      LOGS_DIR="${WORKSPACE}/logs"
    fi

    if [ ! -f "$LOGS_DIR" ]; then
      mkdir -p $LOGS_DIR
    fi

    export ENV_NAME
    export LOGS_DIR
    export ISO_PATH

    if [ "${KEEP_BEFORE}" != "yes" ]; then
      # remove previous environment
      if [ "${DRY_RUN}" = "yes" ]; then
        echo dos.py erase "${ENV_NAME}"
      else
        if dos.py list | grep -q "^${ENV_NAME}\$" ; then
          dos.py erase "${ENV_NAME}"
        fi
      fi
    fi

    # gather additional option for this nose test run
    OPTS=""
    if [ -n "${NOSE_ATTR}" ]; then
        OPTS="${OPTS} -a ${NOSE_ATTR}"
    fi
    if [ -n "${NOSE_EVAL_ATTR}" ]; then
        OPTS="${OPTS} -A ${NOSE_EVAL_ATTR}"
    fi
    if [ -n "${TEST_OPTIONS}" ]; then
        OPTS="${OPTS} ${TEST_OPTIONS}"
    fi

    clean_old_bridges

    # run python test set to create environments, deploy and test product
    if [ "${DRY_RUN}" = "yes" ]; then
        echo export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}${WORKSPACE}"
        echo python plugin_test/run_tests.py -q --nologcapture --with-xunit ${OPTS}
    else
        export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}${WORKSPACE}"
        echo ${PYTHONPATH}
        python plugin_test/run_tests.py -q --nologcapture --with-xunit ${OPTS} &

    fi

    SYSTEST_PID=$!

    if ! ps -p $SYSTEST_PID > /dev/null
    then
	echo System tests exited prematurely, aborting
	exit 1
    fi

    while [ "$(virsh net-list | grep -c $ENV_NAME)" -ne 5 ];do sleep 10
	if ! ps -p $SYSTEST_PID > /dev/null
	then
	    echo System tests exited prematurely, aborting
	    exit 1
	fi
    done
    sleep 10


    # Configre vcenter nodes and interfaces
    setup_net $ENV_NAME
    clean_iptables
    setup_stt $ENV_NAME
    setup_external_net

    revert_ws "$WORKSTATION_NODES" || { echo "killing $SYSTEST_PID and its childs" && pkill --parent $SYSTEST_PID && kill $SYSTEST_PID && exit 1; }

    echo waiting for system tests to finish
    wait $SYSTEST_PID

    export RES=$?
    echo ENVIRONMENT NAME is $ENV_NAME
    virsh net-dumpxml ${ENV_NAME}_admin | grep -P "(\d+\.){3}" -o | awk '{print "Fuel master node IP: "$0"2"}'

    if [ "${KEEP_AFTER}" != "yes" ]; then
      # remove environment after tests
      if [ "${DRY_RUN}" = "yes" ]; then
        echo dos.py destroy "${ENV_NAME}"
      else
        dos.py destroy "${ENV_NAME}"
      fi
    fi

    exit "${RES}"
}

RouteTasks() {
  # this selector defines task names that are recognised by this script
  # and runs corresponding jobs for them
  # running any jobs should exit this script

  case "${TASK_NAME}" in
  test)
    RunTest
    ;;
  iso)
    MakeISO
    ;;
  *)
    echo "Unknown task: ${TASK_NAME}!"
    exit $INVALIDTASK_ERR
    ;;
  esac
  exit 0
}

add_interface_to_bridge() {
  env=$1
  net_name=$2
  nic=$3
  ip=$4

  for net in $(virsh net-list |grep ${env}_${net_name} |awk '{print $1}');do
    bridge=$(virsh net-info $net |grep -i bridge |awk '{print $2}')
    setup_bridge $bridge $nic $ip && echo $net_name bridge $bridge ready
  done
}

setup_bridge() {
  bridge=$1
  nic=$2
  ip=$3

  sudo /sbin/brctl stp $bridge off
  sudo /sbin/brctl addif $bridge $nic
  # set if with existing ip down
  for itf in $(sudo ip -o addr show to $ip |cut -d' ' -f2); do
      echo deleting $ip from $itf
      sudo ip addr del dev $itf $ip
  done
  echo adding $ip to $bridge
  sudo /sbin/ip addr add $ip dev $bridge
  echo $nic added to $bridge
  sudo /sbin/ip link set dev $bridge up
  if sudo /sbin/iptables-save |grep $bridge | grep -i reject| grep -q FORWARD;then
    sudo /sbin/iptables -D FORWARD -o $bridge -j REJECT --reject-with icmp-port-unreachable
    sudo /sbin/iptables -D FORWARD -i $bridge -j REJECT --reject-with icmp-port-unreachable
  fi
}

clean_old_bridges() {
  for intf in $WORKSTATION_IFS; do
    for br in $(/sbin/brctl show | grep -v "bridge name" | cut -f1 -d'	'); do
      /sbin/brctl show $br| grep -q $intf && sudo /sbin/brctl delif $br $intf \
        && sudo /sbin/ip link set dev $br down && echo $intf deleted from $br
    done
  done
}

clean_iptables() {
  sudo /sbin/iptables -F
  sudo /sbin/iptables -t nat -F
  sudo /sbin/iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
}

revert_ws() {
  for i in $1
  do
    vmrun -T ws-shared -h https://localhost:443/sdk -u $WORKSTATION_USERNAME -p $WORKSTATION_PASSWORD listRegisteredVM | grep -q $i || { echo "VM $i does not exist"; continue; }
    echo vmrun: reverting $i to $WORKSTATION_SNAPSHOT
    vmrun -T ws-shared -h https://localhost:443/sdk -u $WORKSTATION_USERNAME -p $WORKSTATION_PASSWORD revertToSnapshot "[standard] $i/$i.vmx" $WORKSTATION_SNAPSHOT || { echo "Error: revert of $i failed";  return 1; }
  done

  for i in $1
  do
    echo vmrun: starting $i
    vmrun -T ws-shared -h https://localhost:443/sdk -u $WORKSTATION_USERNAME -p $WORKSTATION_PASSWORD start "[standard] $i/$i.vmx" || { echo "Error: $i failed to start";  return 1; }
  done
}

setup_net() {
  env=$1
  add_interface_to_bridge $env public vmnet1 172.16.0.1/24
}

setup_stt() {
  set -e
  env=$1
  net_name='private'
  nic='vmnet2'

  for net in $(virsh net-list |grep ${env}_${net_name} |awk '{print $1}');do
    bridge=$(virsh net-info $net | grep -i bridge | awk '{print $2}')
  done
  sudo /sbin/brctl stp $bridge off
  sudo /sbin/brctl addif $bridge $nic
  echo $nic added to $bridge
  sudo /sbin/ip link set dev $bridge up
  if sudo /sbin/iptables-save |grep $bridge | grep -i reject| grep -q FORWARD;then
    sudo /sbin/iptables -D FORWARD -o $bridge -j REJECT --reject-with icmp-port-unreachable
    sudo /sbin/iptables -D FORWARD -i $bridge -j REJECT --reject-with icmp-port-unreachable
  fi

  echo "Stt added to $net_name bridge $bridge"
}

setup_external_net() {
  nic='vmnet5'

  ip=${NSXT_ROUTING_NET_CIDR%\.*}.1
  gw_ip=${NSXT_ROUTING_NET_CIDR%\.*}.2
  mask=${NSXT_ROUTING_NET_CIDR##*\/}

  #set if with existing ip down
  for itf in $(sudo ip -o addr show to $ip | cut -d' ' -f2); do
      echo deleting $ip from $itf
      sudo ip addr del $ip/$mask dev $itf
  done

  for itf in $(sudo ip -o ro show to ${NSXT_FLOATING_NET_CIDR} | cut -d' ' -f5); do
      echo deleting route to ${NSXT_FLOATING_NET_CIDR} dev $itf
      sudo ip ro del ${NSXT_FLOATING_NET_CIDR} dev $itf
  done

  set -e
  sudo /sbin/ip addr add ${ip}/${mask} dev $nic
  sudo /sbin/ip ro add ${NSXT_FLOATING_NET_CIDR} via ${gw_ip}
  echo "Routing net added to $nic"
}

# MAIN

# first we want to get variable from command line options
GetoptsVariables "${@}"

# then we define global variables and there defaults when needed
GlobalVariables

# check do we have all critical variables set
CheckVariables

# first we chdir into our working directory unless we dry run
CdWorkSpace

# finally we can choose what to do according to TASK_NAME
RouteTasks
