System
======


Set up for system tests
-----------------------


ID
##

nsxt_setup_system


Description
###########

Deploy environment with 3 controllers and 1 Compute node. Nova Compute instances are running on controllers and compute-vmware nodes. It is a config for all system tests.


Complexity
##########

core


Steps
#####

    1. Log in to the Fuel web UI with pre-installed NSX-T plugin.
    2. Create new environment with the following parameters:
        * Compute: KVM, QEMU with vCenter
        * Networking: Neutron with NSX-T plugin
        * Storage: default
        * Additional services: default
    3. Add nodes with following roles:
        * Controller
        * Compute-vmware
        * Compute
        * Compute
    4. Configure interfaces on nodes.
    5. Configure network settings.
    6. Enable and configure NSX-T plugin.
    7. Configure VMware vCenter Settings. Add 2 vSphere clusters, configure Nova Compute instances on controller and compute-vmware.
    8. Verify networks.
    9. Deploy cluster.
    10. Run OSTF.


Expected result
###############

Cluster should be deployed and all OSTF test cases should pass.


Check connectivity from VMs to public network
---------------------------------------------


ID
##

nsxt_public_network_availability


Description
###########

Verifies that public network is available.


Complexity
##########

core


Steps
#####

    1. Set up for system tests.
    2. Log in to Horizon Dashboard.
    3. Launch two instances in default network. Instances should belong to different az (nova and vcenter).
    4. Send ping from each instance to 8.8.8.8.


Expected result
###############

Pings should get a response.


Check abilities to create and terminate networks on NSX
-------------------------------------------------------


ID
##

nsxt_manage_networks


Description
###########

Check ability to create/delete networks and attach/detach it to router.


Complexity
##########

core


Steps
#####

    1. Set up for system tests.
    2. Log in to Horizon Dashboard.
    3. Create private networks net_01 and net_02 with subnets.
    4. Launch 1 instance on each network. Instances should belong to different az (nova and vcenter).
    5. Attach (add interface) net_01 to default router. Check that instances can't communicate with each other.
    6. Attach net_02 to default router.
    7. Check that instances can communicate with each other via router.
    8. Detach (delete interface) net_01 from default router.
    9. Check that instances can't communicate with each other.
    10. Delete created instances.
    11. Delete created networks.


Expected result
###############

No errors.


Check abilities to bind port on NSX to VM, disable and enable this port
-----------------------------------------------------------------------


ID
##

nsxt_manage_ports


Description
###########

Verifies that system can not manipulate with port (plugin limitation).


Complexity
##########

core


Steps
#####

    1. Set up for system tests.
    2. Log in to Horizon Dashboard.
    3. Launch two instances in default network. Instances should belong to different az (nova and vcenter).
    4. Check that instances can communicate with each other.
    5. Disable port attached to instance in nova az.
    6. Check that instances can't communicate with each other.
    7. Enable port attached to instance in nova az.
    8. Check that instances can communicate with each other.
    9. Disable port attached to instance in vcenter az.
    10. Check that instances can't communicate with each other.
    11. Enable port attached to instance in vcenter az.
    12. Check that instances can communicate with each other.
    13. Delete created instances.


Expected result
###############

NSX-T plugin should be able to manage admin state of ports.


Check abilities to assign multiple vNIC to a single VM
------------------------------------------------------


ID
##

nsxt_multiple_vnics


Description
###########

Check abilities to assign multiple vNICs to a single VM.


Complexity
##########

core


Steps
#####

    1. Set up for system tests.
    2. Log in to Horizon Dashboard.
    3. Add two private networks (net01 and net02).
    4. Add one subnet (net01_subnet01: 192.168.101.0/24, net02_subnet01, 192.168.101.0/24) to each network.
       NOTE: We have a constraint about network interfaces. One of subnets should have gateway and another should not. So disable gateway on that subnet.
    5. Launch instance VM_1 with image TestVM-VMDK and flavor m1.tiny in vcenter az.
    6. Launch instance VM_2 with image TestVM and flavor m1.tiny in nova az.
    7. Check abilities to assign multiple vNIC net01 and net02 to VM_1.
    8. Check abilities to assign multiple vNIC net01 and net02 to VM_2.
    9. Send icmp ping from VM_1 to VM_2 and vice versa.


Expected result
###############

VM_1 and VM_2 should be attached to multiple vNIC net01 and net02. Pings should get a response.


Check connectivity between VMs attached to different networks with a router between them
----------------------------------------------------------------------------------------


ID
##

nsxt_connectivity_diff_networks


Description
###########

Test verifies that there is a connection between networks connected through the router.


Complexity
##########

core


Steps
#####

    1. Set up for system tests.
    2. Log in to Horizon Dashboard.
    3. Add two private networks (net01 and net02).
    4. Add one subnet (net01_subnet01: 192.168.101.0/24, net02_subnet01, 192.168.101.0/24) to each network. Disable gateway for all subnets.
    5. Launch 1 instance in each network. Instances should belong to different az (nova and vcenter).
    6. Create new router (Router_01), set gateway and add interface to external network.
    7. Enable gateway on subnets. Attach private networks to created router.
    8. Verify that VMs of different networks should communicate between each other.
    9. Add one more router (Router_02), set gateway and add interface to external network.
    10. Detach net_02 from Router_01 and attach it to Router_02.
    11. Assign floating IPs for all created VMs.
    12. Check that default security group allow the ICMP.
    13. Verify that VMs of different networks should communicate between each other by FIPs.
    14. Delete instances.
    15. Detach created networks from routers.
    16. Delete created networks.
    17. Delete created routers.


Expected result
###############

NSX-T plugin should be able to create/delete routers and assign floating ip on instances.


Check abilities to create and delete security group
---------------------------------------------------


ID
##

nsxt_manage_secgroups


Description
###########

Verifies that creation and removing security group works fine.


Complexity
##########

core


Steps
#####

    1. Set up for system tests.
    2. Log in to Horizon Dashboard.
    3. Create new security group with default rules.
    4. Add ingress rule for ICMP protocol.
    5. Launch two instances in default network. Instances should belong to different az (nova and vcenter).
    6. Attach created security group to instances.
    7. Check that instances can ping each other.
    8. Delete ingress rule for ICMP protocol.
    9. Check that instances can't ping each other.
    10. Delete instances.
    11. Delete security group.


Expected result
###############

NSX-T plugin should be able to create/delete security groups and add/delete rules.


Check isolation between VMs in different tenants
------------------------------------------------


ID
##

nsxt_different_tenants


Description
###########

Verifies isolation in different tenants.


Complexity
##########

core


Steps
#####

    1. Set up for system tests.
    2. Log in to Horizon Dashboard.
    3. Create new tenant with new user.
    4. Activate new project.
    5. Create network with subnet.
    6. Create router, set gateway and add interface.
    7. Launch instance and associate floating ip with vm.
    8. Activate default tenant.
    9. Launch instance (use the default network) and associate floating ip with vm.
    10. Check that default security group allow ingress icmp traffic.
    11. Send icmp ping between instances in different tenants via floating ip.


Expected result
###############

Instances on different tenants can communicate between each other only via floating ip.


Check connectivity between VMs with same ip in different tenants
----------------------------------------------------------------


ID
##

nsxt_same_ip_different_tenants


Description
###########

Verifies connectivity with same IP in different tenants.


Complexity
##########

advanced


Steps
#####

    1. Set up for system tests.
    2. Log in to Horizon Dashboard.
    3. Create 2 non-admin tenants 'test_1' and 'test_2' with common admin user.
    4. Activate project 'test_1'.
    5. Create network 'net1' and subnet 'subnet1' with CIDR 10.0.0.0/24
    6. Create router 'router1' and attach 'net1' to it.
    7. Create security group 'SG_1' and add rule that allows ingress icmp traffic
    8. Launch two instances (VM_1 and VM_2) in created network with created security group. Instances should belong to different az (nova and vcenter).
    9. Assign floating IPs for created VMs.
    10. Activate project 'test_2'.
    11. Create network 'net2' and subnet 'subnet2' with CIDR 10.0.0.0/24
    12. Create router 'router2' and attach 'net2' to it.
    13. Create security group 'SG_2' and add rule that allows ingress icmp traffic
    14. Launch two instances (VM_3 and VM_4) in created network with created security group. Instances should belong to different az (nova and vcenter).
    15. Assign floating IPs for created VMs.
    16. Verify that VMs with same ip on different tenants communicate between each other by FIPs. Send icmp ping from VM_1 to VM_3, VM_2 to VM_4 and vice versa.


Expected result
###############

Pings should get a response.


Verify that only the associated MAC and IP addresses can communicate on the logical port
----------------------------------------------------------------------------------------


ID
##

nsxt_bind_mac_ip_on_port


Description
###########

Verify that only the associated MAC and IP addresses can communicate on the logical port.


Complexity
##########

core


Steps
#####

    1. Set up for system tests.
    2. Log in to Horizon Dashboard.
    3. Launch two instances in default network. Instances should belong to different az (nova and vcenter).
    4. Verify that traffic can be successfully sent from and received on the MAC and IP address associated with the logical port.
    5. Configure a new IP address from the subnet not like original one on the instance associated with the logical port.
        * ifconfig eth0 down
        * ifconfig eth0 192.168.99.14 netmask 255.255.255.0
        * ifconfig eth0 up
    6. Confirm that the instance cannot communicate with that IP address.
    7. Revert IP address. Configure a new MAC address on the instance associated with the logical port.
        * ifconfig eth0 down
        * ifconfig eth0 hw ether 00:80:48:BA:d1:30
        * ifconfig eth0 up
    8. Confirm that the instance cannot communicate with that MAC address and the original IP address.


Expected result
###############

Instance should not communicate with new ip and mac addresses but it should communicate with old IP.


Check creation instance in the one group simultaneously
-------------------------------------------------------


ID
##

nsxt_batch_instance_creation


Description
###########

Verifies that system could create and delete several instances simultaneously.


Complexity
##########

core


Steps
#####

    1. Set up for system tests.
    2. Navigate to Project -> Compute -> Instances
    3. Launch 5 instance VM_1 simultaneously with image TestVM-VMDK and flavor m1.tiny in vcenter az in default net_04.
    4. All instance should be created without any error.
    5. Launch 5 instance VM_2 simultaneously with image TestVM and flavor m1.tiny in nova az in default net_04.
    6. All instance should be created without any error.
    7. Check connection between VMs (ping, ssh)
    8. Delete all VMs from horizon simultaneously.


Expected result
###############

All instance should be created and deleted without any error.


Verify that instances could be launched on enabled compute host
---------------------------------------------------------------


ID
##

nsxt_manage_compute_hosts


Description
###########

Check instance creation on enabled cluster.


Complexity
##########

core


Steps
#####

    1. Set up for system tests.
    2. Disable one of compute host in each availability zone (vcenter and nova).
    3. Create several instances in both az.
    4. Check that instances were created on enabled compute hosts.
    5. Disable second compute host and enable first one in each availability zone (vcenter and nova).
    6. Create several instances in both az.
    7. Check that instances were created on enabled compute hosts.


Expected result
###############

All instances were created on enabled compute hosts.


Fuel create mirror and update core repos on cluster with NSX-T plugin
---------------------------------------------------------------------


ID
##

nsxt_update_core_repos


Description
###########

Fuel create mirror and update core repos in cluster with NSX-T plugin


Complexity
##########

core


Steps
#####

    1. Set up for system tests
    2. Log into controller node via Fuel CLI and get PIDs of services which were launched by plugin and store them:
        `ps ax | grep neutron-server`
    3. Launch the following command on the Fuel Master node:
        `fuel-mirror create -P ubuntu -G mos ubuntu`
    4. Run the command below on the Fuel Master node:
        `fuel-mirror apply -P ubuntu -G mos ubuntu --env <env_id> --replace`
    5. Run the command below on the Fuel Master node:
        `fuel --env <env_id> node --node-id <node_ids_separeted_by_coma> --tasks setup_repositories`
        And wait until task is done.
    6. Log into controller node and check plugins services are alive and their PID are not changed.
    7. Check all nodes remain in ready status.
    8. Rerun OSTF.

Expected result
###############

Cluster (nodes) should remain in ready state.
OSTF tests should be passed on rerun.


Configuration with multiple NSX managers
----------------------------------------


ID
##

nsxt_multiple_nsx_managers


Description
###########

NSX-T plugin can configure several NSX managers at once.


Complexity
##########

core


Steps
#####

    1. Create cluster.
       Prepare 2 NSX managers.
    2. Configure plugin.
    3. Set comma separated list of NSX managers.
       nsx_api_managers = 1.2.3.4,1.2.3.5
    4. Deploy cluster.
    5. Run OSTF.
    6. Power off the first NSX manager.
    7. Run OSTF.
    8. Power off the second NSX manager.
       Power on the first NSX manager.
    9. Run OSTF.


Expected result
###############

OSTF tests should be passed.


Deploy HOT
----------


ID
##

nsxt_hot


Description
###########

Template creates flavor, net, security group, instance.


Complexity
##########

smoke


Steps
#####

    1. Deploy cluster with NSX.
    2. Copy nsxt_stack.yaml to controller on which heat will be run.
    3. On controller node run command::

         . ./openrc
         heat stack-create -f nsxt_stack.yaml teststack

    4. Wait for complete creation of stack.
    5. Check that created instance is operable.


Expected result
###############
All objects related to stack should be successfully created.
