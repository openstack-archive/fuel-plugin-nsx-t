Limitations
===========

Plugin is not hotpluggable
--------------------------

It is not possible to enable plugin on already existing OpenStack.


Ubuntu cloud archive distribution is not supported
--------------------------------------------------

   .. image:: /image/uca-archive.png
      :scale: 70 %

Fuel 9.0 provides two options for OpenStack release. One is plain Ubuntu
distribution, another one includes Ubuntu cloud archive. The plugin does not
support Ubuntu cloud archive packages.

Ironic service is not supported
-------------------------------

Ironic service requires control of top of rack switches.


OpenStack environment reset/deletion
------------------------------------

The Fuel NSX-T plugin does not provide a cleanup mechanism when an OpenStack
environment is reset or deleted. All logical switches and routers remain
intact, it is up to the operator to delete them and free resources.
