Failover
========


Verify that it is not possible to uninstall of Fuel NSX plugin with deployed environment.
-------------------------------------------------------------------------------------------


ID
##

nsxt_uninstall_negative


Description
###########

It is not possible to remove plugin while at least one environment exists.


Complexity
##########

smoke


Steps
#####

    1. Install NSX plugin on master node.
    2. Create a new environment with enabled plugin.
    3. Try to delete plugin via cli from master node::

          fuel plugins --remove nsxt==1.0.0


Expected result
###############

Alert: "400 Client Error: Bad Request (Can't delete plugin which is enabled for some environment.)" should be displayed.


Shutdown primary controller and check plugin functionality.
-----------------------------------------------------------


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

    1. Log in to Fuel with preinstalled plugin and deployed enviroment with 3 controllers.
    2. Log in to Horizon.
    3. Create vcenter VM and check connectivity to outside world from VM.
    4. Shutdown primary controller.
    5. Ensure that VIPs are moved to other controller.
    6. Ensure connectivity to outside world from created VM.
    7. Create a new network and attach it to router.
    8. Create a vcenter VM with new network and check network connectivity.


Expected result
###############

Networking is working correct after failure of primary controller.


Check cluster functionality after reboot vcenter.
-------------------------------------------------


ID
##

nsxt_reboot_vcenter


Description
###########

Verifies that system functionality is ok when vcenter has been rebooted.


Complexity
##########

core


Steps
#####

    1. Log in to Fuel with preinstalled plugin and deployed enviroment.
    2. Log in to Horizon.
    3. Launch vcenter instance VM_1 with image TestVM-VMDK and flavor m1.tiny.
    4. Launch vcenter instance VM_2 with image TestVM-VMDK and flavor m1.tiny.
    5. Check connection between VMs, send ping from VM_1 to VM_2 and vice verse.
    6. Reboot vcenter::

          vmrun -T ws-shared -h https://localhost:443/sdk -u vmware -p pass
          reset "[standard] vcenter/vcenter.vmx"
    7. Check that controller lost connection with vCenter.
    8. Wait for vCenter.
    9. Ensure that all instances from vCenter displayed in dashboard.
    10. Ensure connectivity between vcenter1's and vcenter2's VM.
    11. Run OSTF.


Expected result
###############

Cluster should be deployed and all OSTF test cases should be passed. Ping should get response.
