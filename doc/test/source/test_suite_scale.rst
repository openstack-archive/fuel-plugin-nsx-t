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

    1. Log in to the Fuel with preinstalled NSX-T plugin.
    2. Create a new environment with following parameters:
        * Compute: KVM/QEMU with vCenter
        * Networking: Neutron with NSX-T plugin
        * Storage: default
    3. Add nodes with following roles:
        * Controller
        * Controller
        * Controller
        * Compute
    4. Configure interfaces on nodes.
    5. Configure network settings.
    6. Enable and configure NSX-T plugin.
    7. Configure VMware vCenter Settings. Add vSphere cluster and configure Nova Compute instance on conrollers.
    8. Deploy cluster.
    9. Run OSTF.
    10. Launch 1 KVM and 1 vcenter VMs.
    11. Add 2 controller nodes.
    12. Redeploy cluster.
    13. Check that all instances are in place.
    14. Run OSTF.
    15. Remove 2 controller nodes.
    16. Redeploy cluster.
    17. Check that all instances are in place.
    18. Run OSTF.


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

    1. Connect to the Fuel web UI with preinstalled NSX-T plugin.
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
    9. Launch instance.
    10. Add node with compute role.
    11. Redeploy cluster.
    12. Check that all instances are in place.
    13. Run OSTF.
    14. Remove node with compute role from base installation.
    15. Redeploy cluster.
    16. Check that all instances are in place.
    17. Run OSTF.


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

    1. Connect to the Fuel web UI with preinstalled NSX-T plugin.
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
    11. Add node with compute-vmware role.
    12. Reconfigure vcenter compute clusters.
    13. Redeploy cluster.
    14. Check vm instance has been removed.
    15. Run OSTF.
    16. Remove node with compute-vmware role.
    17. Reconfigure vcenter compute clusters.
    18. Redeploy cluster.
    19. Run OSTF.


Expected result
###############

Changing of cluster configuration was successful. Cluster should be deployed and all OSTF test cases should be passed.
