System
======


Setup for system tests
----------------------


ID
##

nsxt_ha_mode


Description
###########

Deploy environment with 3 controlers and 1 Compute node. Nova Compute instances are running on controllers nodes. It is a config for all system tests.


Complexity
##########

core


Steps
#####

    1. Log into Fuel web UI with preinstalled plugin.
    2. Create a new environment with following parameters:
        * Compute: KVM, QEMU with vCenter
        * Networking: Neutron with NSX-T plugin
        * Storage: default
        * Additional services: default
    3. Add nodes with following roles:
        * Controller
        * Controller
        * Controller
        * Compute
    4. Configure interfaces on nodes.
    5. Configure network settings.
    6. Enable and configure NSX-T plugin.
    7. Configure VMware vCenter Settings. Add 1 vSphere cluster and configure Nova Compute instance on conrollers.
    8. Verify networks.
    9. Deploy cluster.
    10. Run OSTF.
    11. Launch instances from images which are available under Horizon. Use m1.tiny flavor.


Expected result
###############

Cluster should be deployed and all OSTF test cases should be passed.


Check abilities to create and terminate networks on NSX.
--------------------------------------------------------


ID
##

nsxt_create_terminate_networks


Description
###########

Verifies that creation of network is translated to vcenter.


Complexity
##########

core


Steps
#####

    1. Setup for system tests.
    2. Log in to Horizon Dashboard.
    3. Add private networks net_01 and net_02.
    4. Remove private network net_01.
    5. Add private network net_01.


Expected result
###############

Check that networks are present in the vcenter. Check that network net_01 has been removed from the vcenter on appropriate step.


Check abilities to bind port on NSX to VM, disable and enable this port.
-------------------------------------------------------------------------


ID
##

nsxt_ability_to_bind_port


Description
###########

Verifies that system could manipulate with port.


Complexity
##########

core


Steps
#####

    1. Log in to Horizon Dashboard.
    2. Navigate to Project -> Compute -> Instances
    3. Launch instance VM_1 with image TestVM-VMDK and flavor m1.tiny in vcenter az.
    4. Launch instance VM_2 with image TestVM and flavor m1.tiny in nova az.
    5. Verify that VMs should communicate between each other. Send icmp ping from VM_1 to VM_2 and vice versa.
    6. Disable NSX_port of VM_1.
    7. Verify that VMs should not communicate between each other. Send icmp ping from VM_2 to VM_1 and vice versa.
    8. Enable NSX_port of VM_1.
    9. Verify that VMs should communicate between each other. Send icmp ping from VM_1 to VM_2 and vice versa.


Expected result
###############

Pings should get a response.


Check abilities to assign multiple vNIC to a single VM.
-------------------------------------------------------


ID
##

nsxt_multi_vnic


Description
###########

Check abilities to assign multiple vNICs to a single VM.


Complexity
##########

core


Steps
#####

    1. Setup for system tests.
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


Check connectivity between VMs attached to different networks with a router between them.
-----------------------------------------------------------------------------------------


ID
##

nsxt_connectivity_diff_networks


Description
###########

Verifies that there is a connection between networks connected through the router.


Complexity
##########

core


Steps
#####

    1. Setup for system tests.
    2. Log in to Horizon Dashboard.
    3. Add two private networks (net01 and net02).
    4. Add one subnet (net01_subnet01: 192.168.101.0/24, net02_subnet01, 192.168.101.0/24) to each network. Disable gateway for all subnets.
    5. Navigate to Project -> Compute -> Instances
    6. Launch instances VM_1 and VM_2 in the network 192.168.101.0/24 with image TestVM-VMDK and flavor m1.tiny in vcenter az. Attach default private net as a NIC 1.
    7. Launch instances VM_3 and VM_4 in the network 192.168.101.0/24 with image TestVM and flavor m1.tiny in nova az. Attach default private net as a NIC 1.
    8. Verify that VMs of same networks should communicate
       between each other. Send icmp ping from VM_1 to VM_2, VM_3 to VM_4 and vice versa.
    9. Verify that VMs of different networks should not communicate
       between each other. Send icmp ping from VM_1 to VM_3, VM_4 to VM_2 and vice versa.
    10. Create Router_01, set gateway and add interface to external network.
    11. Enable gateway on subnets. Attach private networks to router.
    12. Verify that VMs of different networks should communicate between each other. Send icmp ping from VM_1 to VM_3, VM_4 to VM_2 and vice versa.
    13. Add new Router_02, set gateway and add interface to external network.
    14. Detach net_02 from Router_01 and attach to Router_02
    15. Assign floating IPs for all created VMs.
    16. Verify that VMs of different networks should communicate between each other. Send icmp ping from VM_1 to VM_3, VM_4 to VM_2 and vice versa.


Expected result
###############

Pings should get a response.


Check isolation between VMs in different tenants.
-------------------------------------------------


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

    1. Setup for system tests.
    2. Log in to Horizon Dashboard.
    3. Create non-admin tenant test_tenant.
    4. Navigate to Identity -> Projects.
    5. Click on Create Project.
    6. Type name test_tenant.
    7. On tab Project Members add admin with admin and member.
       Activate test_tenant project by selecting at the top panel.
    8. Navigate to Project -> Network -> Networks
    9. Create network with 2 subnet.
       Create Router, set gateway and add interface.
    10. Navigate to Project -> Compute -> Instances
    11. Launch instance VM_1
    12. Activate default tenant.
    13. Navigate to Project -> Network -> Networks
    14. Create network with subnet.
        Create Router, set gateway and add interface.
    15. Navigate to Project -> Compute -> Instances
    16. Launch instance VM_2.
    17. Verify that VMs on different tenants should not communicate between each other. Send icmp ping from VM_1 of admin tenant to VM_2 of test_tenant and vice versa.


Expected result
###############

Pings should not get a response.


Check connectivity between VMs with same ip in different tenants.
-----------------------------------------------------------------


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

    1. Setup for system tests.
    2. Log in to Horizon Dashboard.
    3. Create 2 non-admin tenants 'test_1' and 'test_2'.
    4. Navigate to Identity -> Projects.
    5. Click on Create Project.
    6. Type name 'test_1' of tenant.
    7. Click on Create Project.
    8. Type name 'test_2' of tenant.
    9. On tab Project Members add admin with admin and member.
    10. In tenant 'test_1' create net1 and subnet1 with CIDR 10.0.0.0/24
    11. In tenant 'test_1' create security group 'SG_1' and add rule that allows ingress icmp traffic
    12. In tenant 'test_2' create net2 and subnet2 with CIDR 10.0.0.0/24
    13. In tenant 'test_2' create security group 'SG_2'
    14. In tenant 'test_1' add VM_1 of vcenter in net1 with ip 10.0.0.4 and 'SG_1' as security group.
    15. In tenant 'test_1' add VM_2 of nova in net1 with ip 10.0.0.5 and 'SG_1' as security group.
    16. In tenant 'test_2' create net1 and subnet1 with CIDR 10.0.0.0/24
    17. In tenant 'test_2' create security group 'SG_1' and add rule that allows ingress icmp traffic
    18. In tenant 'test_2' add VM_3 of vcenter in net1 with ip 10.0.0.4 and 'SG_1' as security group.
    19. In tenant 'test_2' add VM_4 of nova in net1 with ip 10.0.0.5 and 'SG_1' as security group.
    20. Assign floating IPs for all created VMs.
    21. Verify that VMs with same ip on different tenants should communicate between each other. Send icmp ping from VM_1 to VM_3, VM_2 to Vm_4 and vice versa.


Expected result
###############

Pings should get a response.


Check connectivity Vms to public network.
-----------------------------------------


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

    1. Setup for system tests.
    2. Log in to Horizon Dashboard.
    3. Create net01: net01_subnet, 192.168.111.0/24 and attach it to the router04
    4. Launch instance VM_1 of vcenter az with image TestVM-VMDK and flavor m1.tiny in the net_04.
    5. Launch instance VM_1 of nova az with image TestVM and flavor m1.tiny in the net_01.
    6. Send ping from instances VM_1 and VM_2 to 8.8.8.8 or other outside ip.


Expected result
###############

Pings should get a response.


Check connectivity VMs to public network with floating ip.
----------------------------------------------------------


ID
##

nsxt_floating_ip_to_public


Description
###########

Verifies that public network is available via floating ip.


Complexity
##########

core


Steps
#####

    1. Setup for system tests.
    2. Log in to Horizon Dashboard
    3. Create net01: net01_subnet, 192.168.111.0/24 and attach it to the router04
    4. Launch instance VM_1 of vcenter az with image TestVM-VMDK and flavor m1.tiny in the net_04. Associate floating ip.
    5. Launch instance VM_1 of nova az with image TestVM and flavor m1.tiny in the net_01. Associate floating ip.
    6. Send ping from instances VM_1 and VM_2 to 8.8.8.8 or other outside ip.


Expected result
###############

Pings should get a response


Check abilities to create and delete security group.
----------------------------------------------------


ID
##

nsxt_create_and_delete_secgroups


Description
###########

Verifies that creation and removing security group works fine.


Complexity
##########

advanced


Steps
#####

    1. Setup for system tests.
    2. Log in to Horizon Dashboard.
    3. Launch instance VM_1 in the tenant network net_02 with image TestVM-VMDK and flavor m1.tiny in vcenter az.
    4. Launch instance VM_2 in the tenant network net_02 with image TestVM and flavor m1.tiny in nova az.
    5. Create security groups SG_1 to allow ICMP traffic.
    6. Add Ingress rule for ICMP protocol to SG_1
    7. Attach SG_1 to VMs
    8. Check ping between VM_1 and VM_2 and vice verse
    9. Create security groups SG_2 to allow TCP traffic 22 port.
       Add Ingress rule for TCP protocol to SG_2
    10. Attach SG_2 to VMs.
    11. ssh from VM_1 to VM_2 and vice verse.
    12. Delete custom rules from SG_1 and SG_2.
    13. Check ping and ssh aren't available from VM_1 to VM_2 and vice verse.
    14. Add Ingress rule for ICMP protocol to SG_1.
    15. Add Ingress rule for SSH protocol to SG_2.
    16. Check ping between VM_1 and VM_2 and vice verse.
    17. Check ssh from VM_1 to VM_2 and vice verse.
    18. Attach VMs to default security group.
    19. Delete security groups.
    20. Check ping between VM_1 and VM_2 and vice verse.
    21. Check SSH from VM_1 to VM_2 and vice verse.


Expected result
###############

We should have the ability to send ICMP and TCP traffic between VMs in different tenants.


Verify that only the associated MAC and IP addresses can communicate on the logical port.
-----------------------------------------------------------------------------------------


ID
##

nsxt_associated_addresses_communication_on_port


Description
###########

Verify that only the associated MAC and IP addresses can communicate on the logical port.


Complexity
##########

core


Steps
#####

    1. Setup for system tests.
    2. Log in to Horizon Dashboard.
    3. Launch 2 instances in each az.
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


Check creation instance in the one group simultaneously.
--------------------------------------------------------


ID
##

nsxt_create_and_delete_vms


Description
###########

Verifies that system could create and delete several instances simultaneously.


Complexity
##########

core


Steps
#####

    1. Setup for system tests.
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


Check that environment support assigning public network to all nodes
--------------------------------------------------------------------


ID
##

nsxt_public_network_to_all_nodes


Description
###########

Verifies that checkbox "Assign public network to all nodes" works as designed.

Assuming default installation has been done with unchecked option "Assign public network to all nodes".


Complexity
##########

core


Steps
#####

    1. Setup for system tests.
    2. Connect through ssh to Controller node. Run 'ifconfig'.
    3. Connect through ssh to compute-vmware node. Run 'ifconfig'.
    4. Redeploy environment with checked option Public network assignment -> Assign public network to all nodes.
    5. Connect through ssh to Controller node. Run 'ifconfig'.
    6. Connect through ssh to compute-vmware node. Run 'ifconfig'.


Expected result
###############

Verify that before cluster redeployment with checked option only controllers have an IP from public network IP range, other nodes don't.
Verify that after cluster redeployment all nodes have an IP from public IP range.


Deploy cluster with KVM virtualization
--------------------------------------


ID
##

nsxt_kvm_deploy


Description
###########

Verify that nodes with compute-vmware role could be deployed in KVM.


Complexity
##########

core


Steps
#####

  1. Create cluster based on KVM.
  2. Add controller and compute-vmware nodes.
  3. Deploy environment.


Expected result
###############

Environment has been deployed successfully.


Check availability metadata server in public network
----------------------------------------------------


ID
##

nsxt_metadata_listen_public


Description
###########

Test case verifies option nsxt_metadata_listen in public state.

Complexity
##########

core


Steps
#####

    1. Configure cluster.
    2. Install fuel and nsxt plugin.
    3. Configure nsxt plugin.
       In field 'Which network will be used to access the nova-metadata' choose 'Public network'.
       Manually specify the IP address, network mask and default route for the proxy metadata router.
    4. Launch instance and run command from it::

	wget -O - 169.254.169.254


Expected result
###############

'Init metadata infrastructure' is checked by default.
Request should return::

 Connecting to 169.254.169.254 (169.254.169.254:80)
 1.0
 1.07-01-19
 1.07-03-01
 1.07-08-29
 1.07-10-10
 1.07-12-15
 1.08-01.01
 1.08-09-01
 1.09-04-04


Verify that instances could be launched on enabled compute host
---------------------------------------------------------------


ID
##

nsxt_disable_hosts


Description
###########

Check instance creation on enabled cluster.


Complexity
##########

core


Steps
#####

            1. Setup cluster with 3 controllers, 2 Compute nodes and cinder-vmware +
               compute-vmware role.
            2. Assign instances in each az.
            3. Disable one of compute host with vCenter cluster
               (Admin -> Hypervisors).
            4. Create several instances in vcenter az.
            5. Check that instances were created on enabled compute host
               (vcenter cluster).
            6. Disable second compute host with vCenter cluster and enable
               first one.
            7. Create several instances in vcenter az.
            8. Check that instances were created on enabled compute host
               (vcenter cluster).
            9. Create several instances in nova az.
            10. Check that instances were created on enabled compute host
               (nova cluster).


Expected result
###############

All instances work fine.


Check that settings about new cluster are placed in neutron config
------------------------------------------------------------------


ID
##

nsxt_smoke_add_compute


Description
###########

Adding compute role and redeploy cluster with NSX-T plugin has effect in neutron configs.


Complexity
##########

core


Steps
#####

            1. Upload the plugin to master node.
            2. Create cluster and configure NSX for that cluster.
            3. Provision three controller node.
            4. Deploy cluster with plugin.
            5. Get configured clusters morefid from neutron config.
            6. Add node with Compute role.
            7. Redeploy cluster with new node.
            8. Get new configured clusters morefid from neutron config.
            9. Check new cluster added in neutron config.


Expected result
###############

Clusters are reconfigured after Compute has been added.


Fuel create mirror and update core repos on cluster with NSX-T plugin
-------------------------------------------------------------------


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

    1. Setup for system tests
    2. Log into controller node via Fuel CLI and get PID of services which were launched by plugin and store them:
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
OSTF test should be passed on rerun


Configuration with multiple NSX managers
----------------------------------------


ID
##

nsxt_multiple_nsx_managers


Description
###########

NSX-T plugin could configure several NSX managers at once.


Complexity
##########

core


Steps
#####

    1. Create cluster.
       Prepare 2 NSX managers.
    2. Configure plugin.
    3. Set comma separtated list of NSX managers.
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

OSTF test should be passed.


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
       Wait for status COMPLETE.
    4. Run OSTF.


Expected result
###############
All OSTF are passed.
