OpenStack environment notes
===========================

Environment configuration
-------------------------

The Fuel NSX-T plugin cannot deploy NSX Transformers.

Before you start OpenStack deployment, verify that your VMware NSX Transformers
is configured and functions properly:

* VLAN transport zone must present
* Overlay transport zone must present
* tier0 router must be created
* uplink profile for OpenStack nodes must be created
* NSX edge cluster must be formed
* IP address pool for OpenStack controllers and compute nodes must exist

To use the NSX-T plugin, create a new OpenStack environment using the Fuel web
UI by doing the following:

#. On the :guilabel:`Networking setup` configuration step, select
   :guilabel:`Neutron with NSX-T plugin` radio button

   .. image:: /image/neutron-nsxt-item.png
      :scale: 70 %

Network setup
-------------

Pay attention to on which interface you assign the *Public* network. The
OpenStack controllers must have connectivity with the NSX Manager host
through the *Public* network since the *Public* network is the default
route for packets.

If NSX Manager and NSX Controllers are going to communicate with OpenStack
controllers and computes through Public network then setting :guilabel:`Assign
public network to all nodes` (Networks tab -> Settings/Other label) must be
enabled. Otherwise compute node will be communicating with NSX Manager through
controller that perform NAT which will hide compute node IP addresses and will
prevent them to register in NSX management plane.

  .. image:: /image/nsx-t-public.png
     :scale: 100%

Another way is to locate NSX nodes in OpenStack management network. In this
setup there is no need to assign public network to all nodes, because OpenStack
and NSX nodes has L2 connectivity and no NAT is performed. OpenStack
controllers and computes will still use Public network as default route.

  .. image:: /image/nsx-t-mgmt.png
     :scale: 100%

During the deployment, the plugin creates a simple network topology for
the admin tenant. The plugin creates a provider network which connects the
tenants with the transport (physical) network: one internal network and
a router that is connected to both networks.

