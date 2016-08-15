Scale
=====


Deploy cluster with plugin and deletion one node with controller role.
----------------------------------------------------------------------


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


Deployment with 3 Controlers, Compute-vmware, Cinder-vmware and check adding/deleting of nodes.
---------------------------------------------------------------------------------------------


ID
##

nsxt_add_delete_nodes


Description
###########

Verify that system functionality is ok after redeploy.


Complexity
##########

advanced


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
    7. Configure VMware vCenter Settings. Add 2 vSphere clusters and configure Nova Compute instances on controllers and compute-vmware.
    8. Deploy cluster.
    9. Run OSTF.
    10. Add node with Cinder-vmware role.
        Redeploy cluster.
    11. Run OSTF.
    12. Remove node with Cinder-vmware role.
        Redeploy cluster.
    13. Run OSTF.
    14. Remove node with Compute-vmware role.
        Redeploy cluster.
    15. Run OSTF.


Expected result
###############

Changing of cluster configuration was successful. Cluster should be deployed and all OSTF test cases should be passed.
