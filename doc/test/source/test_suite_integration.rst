Integration
===========


Deploy cluster with NSX-T plugin and ceilometer.
------------------------------------------------


ID
##

nsxt_ceilometer


Description
###########

Check deployment of environment with Fuel NSX-T plugin and Ceilometer.


Complexity
##########

core


Steps
#####

    1. Log in to the Fuel UI with preinstalled NSX-T plugin.
    2. Create a new environment with following parameters:
        * Compute: KVM/QEMU with vCenter
        * Networking: Neutron with NSX-T plugin
        * Storage: default
        * Additional services: Ceilometer
    3. Add nodes with following roles:
        * Controller + Mongo
        * Controller + Mongo
        * Controller + Mongo
        * Compute-vmware
        * Compute
    4. Configure interfaces on nodes.
    5. Configure network settings.
    6. Enable and configure NSX-T plugin.
    7. Configure VMware vCenter Settings. Add 2 vSphere clusters and configure Nova Compute instances on conrollers and compute-vmware.
    8. Verify networks.
    9. Deploy cluster.
    10. Run OSTF.


Expected result
###############

Cluster should be deployed and all OSTF tests cases should be passed.
