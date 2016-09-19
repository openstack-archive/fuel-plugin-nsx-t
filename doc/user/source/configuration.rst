Configuration
=============

Node interfaces for overlay traffic
-----------------------------------

NSX Transformers uses STT protocol to carry virtual machines traffic.  Plugin
requires that interfaces which are going to be used for STT traffic must not
carry any other traffic (PXE, storage, openstack management).

.. image:: /image/stt-interface.png

Switch to the :guilabel:`Networks` tab of the Fuel web UI and click the
:guilabel:`Settings`/`Other` label. The plugin checkbox is enabled
by default. The screenshot below shows only the settings in focus:

.. image:: /image/nsxt-settings.png
   :scale: 60 %

The plugin contains the following settings:

#. Bypass NSX Manager certificate verification -- if enabled, the HTTPS
   connection to NSX Manager is not verified. Otherwise, the two following
   options are available:

   * The setting "CA certificate file" appears below making it possible to
     upload a CA certificate that issued the NSX Manager certificate.

   * With no CA certificate provided, the NSX Manager certificate is verified
     against the CA certificate bundle that comes with Ubuntu 14.04.

#. NSX Manager -- IP address or hostname, multiple values can be separated by
   comma. If you are going to use hostname in this textbox, ensure that your
   OpenStack controller can resolve the hostname.  Add necessary DNS servers in
   the :guilabel:`Host OS DNS Servers` section.

   OpenStack Controller must have L3 connectivity with NSX Manager through
   the Public network which is used as default route.

#. Overlay transport zone ID -- UUID of overlay (STT) transport zone which must
   be pre-created in NSX Manager.

#. VLAN transport zone ID --- UUID of transport zone which represents network
   that connects virtual machines with physical infrastructure.

#. Tier-0 router ID -- UUID of tier0 router that must exist in NSX Transformers.

#. Edge cluster -- UUID of NSX edge nodes cluster that must be installed and
   configured.

#. Uplink profile ID -- UUID of uplink profile which specifies STT interfaces
   configuration (e.g. MTU value).


#. IP pool ID for controller VTEPs -- UUID of IP pool that will be assigned to
   controllers STT interfaces.

#. Colon separated pnics pairs for controller nodes -- this field sets
   correspondence between physical NIC and uplink name that is used in "Uplink
   profile ID" on controller nodes, e.g. ``enp0s1:uplink``. Each pair must be one
   separate line.

   .. warning::
      Uplink name must exactly match value of "Active uplink" or "Standby
      uplink" in uplink switch profile that was specified above.

#. IP pool ID for compute VTEPs -- UUID of IP pool that will be assigned to
   STT interfaces of compute nodes.

#. Colon separated pnics pairs for compute nodes -- this fields sets
   correspondence between physical NIC and uplink name that is used in "Uplink
   profile ID" on compute nodes, e.g. "enp0s1:uplink". Each pair must be one
   separate line.

#. Floating IP ranges -- dash-separated IP addresses allocation pool for
   external network, e.g. "172.16.212.2-172.16.212.40".

#. External network CIDR -- network in CIDR notation that includes floating IP ranges.

#. Gateway -- default gateway for the external network; if not defined, the
   first IP address of the network is used.

#. Internal network CIDR -- network in CIDR notation for use as internal.

#. DNS for internal network -- comma-separated IP addresses of DNS server for
   internal network.
