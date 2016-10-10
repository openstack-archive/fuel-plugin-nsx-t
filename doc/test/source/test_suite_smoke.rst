Smoke
=====


Install Fuel VMware NSX-T plugin.
---------------------------------


ID
##

nsxt_install


Description
###########

Check that plugin can be installed.


Complexity
##########

smoke


Steps
#####

    1. Connect to the Fuel master node via ssh.
    2. Upload NSX-T plugin.
    3. Install NSX-T plugin.
    4. Run command 'fuel plugins'.
    5. Check name, version and package version of plugin.


Expected result
###############
Output::

 [root@nailgun ~]# fuel plugins --install nsx-t-1.0-1.0.0-1.noarch.rpm
 Loaded plugins: fastestmirror, priorities
 Examining nsx-t-1.0-1.0.0-1.noarch.rpm: nsx-t-1.0-1.0.0-1.noarch
 Marking nsx-t-1.0-1.0.0-1.noarch.rpm to be installed
 Resolving Dependencies
 --> Running transaction check
 ---> Package nsx-t-1.0.noarch 0:1.0.0-1 will be installed
 --> Finished Dependency Resolution

 Dependencies Resolved


  Package Arch Version Repository Size
 Installing:
  nsx-t-1.0 noarch 1.0.0-1 /nsx-t-1.0-1.0.0-1.noarch 20 M

 Transaction Summary
 Install  1 Package

 Total size: 20 M
 Installed size: 20 M
 Downloading packages:
 Running transaction check
 Running transaction test
 Transaction test succeeded
 Running transaction
   Installing : nsx-t-1.0-1.0.0-1.noarch 1/1
   Verifying  : nsx-t-1.0-1.0.0-1.noarch 1/1

 Installed:
   nsx-t-1.0.noarch 0:1.0.0-1

 Complete!
 Plugin nsx-t-1.0-1.0.0-1.noarch.rpm was successfully installed.

Plugin was installed successfully using cli.


Uninstall Fuel VMware NSX-T plugin.
-----------------------------------


ID
##

nsxt_uninstall


Description
###########

Check that plugin can be removed.


Complexity
##########

smoke


Steps
#####

    1. Connect to fuel node with preinstalled NSX-T plugin via ssh.
    2. Remove NSX-T plugin.
    3. Run command 'fuel plugins' to ensure the NSX-T plugin has been removed.


Expected result
###############
Output::

 [root@nailgun ~]# fuel plugins --remove nsx-t==1.0.0
 Loaded plugins: fastestmirror, priorities
 Resolving Dependencies
 --> Running transaction check
 ---> Package nsx-t-1.0.noarch 0:1.0.0-1 will be erased
 --> Finished Dependency Resolution

 Dependencies Resolved

  Package  Arch  Version Repository Size
 Removing:
  nsx-t-1.0 noarch 1.0.0-1 @/nsx-t-1.0-1.0.0-1.noarch 20 M

 Transaction Summary
 Remove  1 Package

 Installed size: 20 M
 Downloading packages:
 Running transaction check
 Running transaction test
 Transaction test succeeded
 Running transaction
   Erasing    : nsx-t-1.0-1.0.0-1.noarch 1/1
   Verifying  : nsx-t-1.0-1.0.0-1.noarch 1/1

 Removed:
   nsx-t-1.0.noarch 0:1.0.0-1

 Complete!
 Plugin nsx-t==1.0.0 was successfully removed.

Plugin was removed.


Verify that all UI elements of NSX-T plugin section meets the requirements.
---------------------------------------------------------------------------


ID
##

nsxt_gui


Description
###########

Verify that all UI elements of NSX-T plugin section meets the requirements.


Complexity
##########

smoke


Steps
#####

    1. Login to the Fuel web UI.
    2. Click on the Networks tab.
    3. Verify that section of NSX-T plugin is present under the Other menu option.
    4. Verify that check box 'NSX-T plugin' is enabled by default.
    5. Verify that all labels of 'NSX-T plugin' section have the same font style and colour.
    6. Verify that all elements of NSX-T plugin section are vertical aligned.


Expected result
###############

All elements of NSX-T plugin section are regimented.


Deployment with plugin, controller and vmware datastore backend.
----------------------------------------------------------------


ID
##

nsxt_smoke


Description
###########

Check deployment of non-ha environment with NSX-T plugin and one compute node.


Complexity
##########

smoke


Steps
#####

    1. Log in to the Fuel with preinstalled NSX-T plugin.
    2. Create a new environment with following parameters:
        * Compute: KVM, QEMU with vCenter
        * Networking: Neutron with NSX-T plugin
        * Storage: default
        * Additional services: default
    3. Add nodes with following roles:
        * Controller
        * Compute
    4. Configure interfaces on nodes.
    5. Configure network settings.
    6. Enable and configure NSX-T plugin.
    7. Deploy cluster.
    8. Run OSTF.


Expected result
###############

Cluster should be deployed successfully and all OSTF tests should be passed.


Deploy HA cluster with NSX-T plugin.
------------------------------------


ID
##

nsxt_bvt


Description
###########

Check deployment of environment with NSX-T plugin, 3 Controllers, 1 Compute, 3 CephOSD, cinder-vware + compute-vmware roles.


Complexity
##########

smoke


Steps
#####

    1. Connect to the Fuel web UI with preinstalled NSX-T plugin.
    2. Create a new environment with following parameters:
        * Compute: KVM, QEMU with vCenter
        * Networking: Neutron with NSX-T plugin
        * Storage: default
        * Additional services: default
    3. Add nodes with following roles:
        * Controller
        * Controller
        * Controller
        * Compute-vmware, cinder-vmware
        * Compute, cinder
    4. Configure interfaces on nodes.
    5. Configure network settings.
    6. Enable and configure NSX-T plugin.
    7. Configure VMware vCenter Settings. Add 2 vSphere clusters and configure Nova Compute instances on controllers and compute-vmware.
    8. Verify networks.
    9. Deploy cluster.
    10. Run OSTF.


Expected result
###############

Cluster should be deployed and all OSTF tests should be passed.


Check option 'Bypass NSX Manager certificate verification' works correct
------------------------------------------------------------------------


ID
##

nsxt_insecure_false


Description
###########

Check that insecure checkbox functions properly.


Complexity
##########

core


Steps
#####

    1. Provide CA certificate via web UI or through system storage.
    2. Install NSX-T plugin.
    3. Enable plugin on tab Networks -> NSX-T plugin.
    4. Fill the form with corresponding values.
    5. Uncheck checkbox 'Bypass NSX Manager certificate verification'.
    6. Deploy cluster with one controller.
    7. Run OSTF.


Expected result
###############

Cluster should be deployed and all OSTF tests should be passed.


Verify that nsxt driver configured properly after enabling NSX-T plugin
-----------------------------------------------------------------------


ID
##

nsxt_config_ok


Description
###########

Check that all parameters of nsxt driver config files have been filled up with values were entered from GUI. Applicable values that are typically used are described in plugin docs. Root & intermediate certificate are signed, in attachment.


Complexity
##########

advanced


Steps
#####

    1. Install NSX-T plugin.
    2. Enable plugin on tab Networks -> NSX-T plugin.
    3. Fill the form with corresponding values.
    4. Do all things that are necessary to provide interoperability of NSX-T plugin and NSX Manager with certificate.
    5. Check Additional settings. Fill the form with corresponding values. Save settings by pressing the button.


Expected result
###############

Check that nsx.ini on controller nodes is properly configured.
