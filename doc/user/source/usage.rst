Usage
=====

The easiest way to check that the plugin works as expected is to create a
network or router using the ``neutron`` command-line tool:

::

  [root@nailgun ~]# ssh node-4    # node-4 is a controller node
  root@node-4:~# . openrc
  root@node-4:~# neutron router-create r1

You can monitor the plugin actions in ``/var/log/neutron/server.log`` and see
how edges appear in the list of the ``Networking & Security -> NSX Edges``
pane in vSphere Web Client. If you see error messages, check the
:ref:`Troubleshooting <troubleshooting>` section.

STT MTU considerations
----------------------

NSX Transformers uses STT protocol to encapsulate VM traffic. The protocol adds
additional data to the packet. Consider increasing MTU on the network equipment
connected to hosts that will emit STT traffic.

Consider the following calculation:

Outer IPv4 header    == 20 bytes

Outer TCP header     == 24 bytes

STT header           == 18 bytes

Inner Ethernet frame == 1518 (14 bytes header, 4 bytes 802.1q header, 1500 Payload)

Summarizing all of these we get 1580 bytes. Consider increasing MTU on the
network hardware up to 1600 bytes.
