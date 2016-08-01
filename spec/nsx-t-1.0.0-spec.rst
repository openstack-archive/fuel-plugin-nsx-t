..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

========================
Fuel NSX-T plugin v1.0.0
========================

NSX-T plugin for Fuel provides an ability to deploy OpenStack cluster that uses
NSX Transformers platform as backend for Neutron server.

Proposed change
===============

Requirements
------------
- the plugin must be compatible with Fuel 9.0
- NSX Transformers platform is correctly configured and is running before
  plugin starts deployment process
- the plugin is not hot pluggable, i.e. it cannot be added later after
  OpenStack cluster was deployed
- overlay (STT) traffic must reside in Fuel Private network

NSX Transformers plaform provides NSX agents that provide STT support for
OpenStack nodes (controller, compute). It also supports ESXi hypervisor.

Plugin component
----------------

Plugin reuses ``network:neutron:core:nsx`` component (component-registry [1]_)
that is also declared by Fuel NSXv plugin [2]_. This means that these two
plugins cannot be installed together on fuel master node. This is a limitation
of Fuel UI [3]_.

Incompatible roles
------------------

Plugin is not compatible with following roles:

  * Ironic

Plugin deployment workflow
--------------------------

#. Install custom OVS package with STT support
#. Install dependencies for OVS and NSX-T packages
#. Install NSX plugin on controller
#. Register node as transport node in NSX-T Manager
#. Add permit rule for STT traffic
#. Configure neutron-server to use NSX plugin
#. Configure neutron dhcp agent
#. Configure neutron metadata agent
#. Configure nova to NSX managed OVS bridge

Data model impact
-----------------

Plugin will produce following array of settings into astute.yaml:

.. code-block:: yaml

  nsx:
    nsx_api_managers:
      value: 172.16.0.249
    nsx_api_user:
      value: admin
    nsx_api_password:
      value: r00tme
    nsx_default_overlay_tz:
      value: a1ed818c-3580-45ac-a1bc-8fd4bf045cff
    nsx_default_vlan_tz:
      value: 59919e1c-9689-4335-97cd-758d27204287
    nsx_default_tier0_router:
      value: 0785e4bc-10d0-4744-8088-9cb26b38f23f


Upgrade impact
--------------

None.

Other end user impact
---------------------

None.

Implementation
==============

Assignee(s)
-----------

Primary assignee:

- Igor Zinovik <izinovik@mirantis.com> - developer

Other contributors:

- Artem Savinov <asavinov@mirantis.com> - developer

Project manager:

- Andrian Noga <anoga@mirantis.com>

Quality assurance:

- Andrey Setyaev <asetyaev@mirantis.com>


Work items
==========

* Create pre-dev environment and manually deploy NSX Transformers

* Create Fuel plugin bundle, which contains deployments scripts, puppet
  modules and metadata

* Implement puppet module

* Create system tests for the plugin

* Prepare user guide


Dependencies
============

* Fuel 9.0

* VMware NSX Transformers 1.0


Testing
=======

* Sanity checks including plugin build
* Syntax check
* Functional testing
* Non-functional testing
* Destructive testing

Documentation impact
====================

* User guide
* Test plan

References
==========

.. [1] Component registry specification https://github.com/openstack/fuel-specs/blob/master/specs/8.0/component-registry.rst
.. [2] Fuel NSXv plugin component https://github.com/openstack/fuel-plugin-nsxv/blob/master/components.yaml
.. [3] Fuel UI component binding https://github.com/openstack/fuel-ui/blob/stable/mitaka/static/views/wizard.js#L348
