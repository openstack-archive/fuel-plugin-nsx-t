Scale
=====


Check scale actions for controller nodes.
-----------------------------------------


ID
##

nsxt_add_delete_controller


Description
###########

Verifies that system functionality is ok when controller has been removed.


Complexity
##########

core


Steps
#####

    1. Log into Fuel with preinstalled plugin.
    2. Create a new environment with following parameters:
        * Compute: KVM/QEMU with vCenter
        * Networking: Neutron with NSX-T plugin
        * Storage: default
    3. Add nodes with following roles:
        * Controller
        * Controller
        * Controller
        * Controller
        * Cinder-vmware
        * Compute-vmware
    4. Configure interfaces on nodes.
    5. Configure network settings.
    6. Enable and configure NSX-T plugin.
    7. Configure VMware vCenter Settings. Add 2 vSphere clusters and configure Nova Compute instances on conrollers and compute-vmware.
    8. Deploy cluster.
    9. Run OSTF.
    10. Launch KVM and vcenter VMs.
    11. Remove node with controller role.
    12. Redeploy cluster.
        Check that all instances are in place.
    13. Run OSTF.
    14. Add controller.
    15. Redeploy cluster.
        Check that all instances are in place.
    16. Run OSTF.


Expected result
###############

Cluster should be deployed and all OSTF test cases should be passed.


Check scale actions for compute nodes.
--------------------------------------


ID
##

nsxt_add_delete_compute_node


Description
###########

Verify that system functionality is ok after redeploy.


Complexity
##########

core


Steps
#####

    1. Connect to a Fuel web UI with preinstalled plugin.
    2. Create a new environment with following parameters:
        * Compute: KVM/QEMU
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
    7. Deploy cluster.
    8. Run OSTF.
    9. Launch KVM vm.
    10. Add node with compute role.
        Redeploy cluster.
        Check that all instances are in place.
    11. Run OSTF.
    12. Remove node with compute role from base installation.
        Redeploy cluster.
        Check that all instances are in place.
    13. Run OSTF.


Expected result
###############

Changing of cluster configuration was successful. Cluster should be deployed and all OSTF test cases should be passed.


Check scale actions for compute-vmware nodes.
---------------------------------------------


ID
##

nsxt_add_delete_compute_vmware_node


Description
###########

Verify that system functionality is ok after redeploy.


Complexity
##########

core


Steps
#####

    1. Connect to a Fuel web UI with preinstalled plugin.
    2. Create a new environment with following parameters:
        * Compute: KVM/QEMU with vCenter
        * Networking: Neutron with NSX-T plugin
        * Storage: default
        * Additional services: default
    3. Add nodes with following roles:
        * Controller
        * Controller
        * Controller
        * Compute-vmware
    4. Configure interfaces on nodes.
    5. Configure network settings.
    6. Enable and configure NSX-T plugin.
    7. Configure VMware vCenter Settings. Add 1 vSphere cluster and configure Nova Compute instance on compute-vmware.
    8. Deploy cluster.
    9. Run OSTF.
    10. Launch vcenter vm.
    11. Remove node with compute-vmware role.
        Reconfigure vcenter compute clusters.
        Redeploy cluster.
        Check vm instance has been removed.
    12. Run OSTF.
    13. Add node with compute-vmware role.
        Reconfigure vcenter compute clusters.
        Redeploy cluster.
    14. Run OSTF.


Expected result
###############

Changing of cluster configuration was successful. Cluster should be deployed and all OSTF test cases should be passed.
