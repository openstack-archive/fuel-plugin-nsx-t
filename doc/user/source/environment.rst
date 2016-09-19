OpenStack environment notes
===========================

Environment configuration
-------------------------

Before you start the actual deployment, verify that your VMware NSX
Transformers is configured and functions properly:

* VLAN transport zone must present
* Overlay transport zone must present
* tier0 router must be created
* uplink profile for OpenStack nodes must be created
* edge cluster must be formed
* IP address pool for OpenStack controllers and compute nodes must exist

The Fuel NSX-T plugin cannot deploy NSX Transformers.

To use the NSX-T plugin, create a new OpenStack environment using the Fuel web
UI by doing the following:

#. On the :guilabel:`Networking setup` configuration step, select
   :guilabel:`Neutron with NSX-T plugin` radio button

   .. image:: /image/neutron-nsxt-item.png
      :scale: 70 %

Pay attention to on which interface you assign the *Public* network. The
OpenStack controllers must have connectivity with the NSX Manager host
through the *Public* network since the *Public* network is the default
route for packets.

During the deployment, the plugin creates a simple network topology for
the admin tenant. The plugin creates a provider network which connects the
tenants with the transport (physical) network: one internal network and
a router that is connected to both networks.

