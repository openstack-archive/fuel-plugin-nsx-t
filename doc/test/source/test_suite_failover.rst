Failover
========


Verify deleting of Fuel NSX-T plugin is impossible if it's used by created cluster.
-----------------------------------------------------------------------------------


ID
##

nsxt_uninstall_negative


Description
###########

It is impossible to remove plugin while at least one environment exists.


Complexity
##########

smoke


Steps
#####

    1. Install NSX-T plugin on master node.
    2. Create a new environment with enabled NSX-T plugin.
    3. Try to delete plugin via cli from master node::

          fuel plugins --remove nsxt==1.0.0


Expected result
###############

Alert: "400 Client Error: Bad Request (Can't delete plugin which is enabled for some environment.)" should be displayed.


Check plugin functionality after shutdown primary controller.
-------------------------------------------------------------


ID
##

nsxt_shutdown_controller


Description
###########

Check plugin functionality after shutdown primary controller.


Complexity
##########

core


Steps
#####

    1. Log in to the Fuel with preinstalled plugin and deployed ha enviroment with 3 controllers, 1 compute and 1 compute-vmware nodes.
    2. Log in to Horizon.
    3. Launch two instances in different az (nova and vcenter) and check connectivity to outside world from VMs.
    4. Shutdown primary controller.
    5. Ensure that VIPs are moved to other controller.
    6. Ensure that there is a connectivity to outside world from created VMs.
    7. Create a new network and attach it to default router.
    8. Launch two instances in different az (nova and vcenter) with new network and check network connectivity via ICMP.


Expected result
###############

Networking works correct after failure of primary controller.


Check cluster functionality after interrupt connection with NSX manager.
------------------------------------------------------------------------


ID
##

nsxt_interrupt_connection


Description
###########

Test verifies that cluster will functional after interrupt connection with NSX manager.


Complexity
##########

core


Steps
#####

    1. Log in to the Fuel with preinstalled plugin and deployed enviroment.
    2. Launch instances in each az with default network.
    3. Disrupt connection with NSX manager and check that controller lost connection with NSX.
    4. Try to create new network.
    5. Restore connection with NSX manager.
    6. Try to create new network again.
    7. Launch instance in created network.
    8. Ensure that all instances have connectivity to external network.
    9. Run OSTF.


Expected result
###############

After restore connection with NSX manager cluster should be fully functional. All created VMs should be operable. All OSTF test cases should be passed.
