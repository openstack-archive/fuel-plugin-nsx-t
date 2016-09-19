
.. _troubleshooting:

Troubleshooting
===============

Neutron NSX plugin issues
-------------------------

The Neutron NSX-T plugin does not have a separate log file, its messages
are logged by the neutron server. The default log file on OpenStack controllers
for neutron server is ``/var/log/neutron/server.log``

Inability to resolve NSX Manager hostname
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you see following message:

::

 2016-10-18 ... INFO vmware_nsx.plugins.nsx_v3.plugin [-] Starting NsxV3Plugin
 2016-10-18 ... INFO vmware_nsx.nsxlib.v3.cluster [-] Endpoint 'https://nsxmanager.mydom.org'
    changing from state 'INITIALIZED' to 'DOWN'
 2016-10-18 ... WARNING vmware_nsx.nsxlib.v3.cluster [-] Failed to validate API cluster endpoint
    '[DOWN] https://nsxmanager.mydom.org' due to: HTTPSConnectionPool(host='nsxmanager.mydom.org',
    port=443): Max retries exceeded with url: /a...nes (Caused by NewConnectionError(
    '<requests.packages.urllib3.connection.VerifiedHTTPSConnection object at 0x7ff69b3c4b90>:
    Failed to establish a new connection: [Errno -2] Name or service not known',))
 2016-10-18 ... ERROR neutron.service [-] Unrecoverable error: please check log for details.
 2016-10-18 ... ERROR neutron.service Traceback (most recent call last):
 ...
 2016-10-18 ... ERROR neutron.service ServiceClusterUnavailable: Service cluster:
    'https://nsxmanager.mydom.org' is unavailable. Please, check NSX setup and/or configuration


It means that the controller cannot resolve the NSX Manager hostname
(``nsxmanager.mydom.org`` in this example) that is specified in the
configuration file.
Check that the DNS server IP addresses that you specified in the
:guilabel:`Host OS DNS Servers` section of the Fuel web UI are correct
and reachable by all controllers; pay attention to that the default route
for controllers is *Public* network. Also, verify that the hostname that you
entered is correct by trying to resolve it via the ``host`` or ``dig`` programs.

SSL/TLS certificate problems
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

 2016-02-19 ... ERROR neutron   File "/usr/lib/python2.7/dist-packages/httplib2/__init__.py",
    line 1251, in _conn_request
        2016...  10939 ERROR neutron     conn.connect()
 2016-02-19 ... ERROR neutron   File "/usr/lib/python2.7/dist-packages/httplib2/__init__.py",
    line 1043, in connect
 2016-02-19 ... ERROR neutron     raise SSLHandshakeError(e)
 2016-02-19 ... ERROR neutron SSLHandshakeError: [Errno 1]_ssl.c:510: error:
        14090086:SSL routines:SSL3_GET_SERVER_CERTIFICATE:certificate verify failed

This error indicates that you enabled the SSL/TLS certificate verification, but
the certificate verification failed during connection to NSX Manager.
The possible causes are:

 #. NSX Manager certificate expired. Log into NSX Manager web GUI and check
    certificate validation dates.
 #. Check if the certification authority (CA) certificate is still valid.
    The CA certificate is specified by ``ca_file`` directive in ``nsx.ini``.

User access problems
~~~~~~~~~~~~~~~~~~~~

::

 2016-02-19 ... CRITICAL neutron [-] Forbidden: Forbidden: https://172.16.0.249/api/1.0/
    appliance-management/summary/system
 ...
 2016-02-19 ... ERROR neutron   File "/usr/lib/python2.7/dist-packages/vmware_nsx/plugins/
    nsx_v/vshield/common/VcnsApiClient.py", line 119, in request
 2016-02-19 ... ERROR neutron     raise cls(uri=uri, status=status, header=header, response=response)
 2016-02-19 ... ERROR neutron Forbidden: Forbidden: https://172.16.0.249/api/1.0/
    appliance-management/summary/system

Possible solutions:

 * Username is incorrect.
 * Password is incorrect.

Non-existent vCenter entity specified
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If some settings of vCenter do not exist, the plugin will report the following
message with varying settings is not found in vCenter:

::

 2016-02-19 ... ERROR neutron   File "/usr/lib/python2.7/dist-packages/vmware_nsx/plugins/
    nsx_v/plugin.py", line 2084, in _validate_config
 2016-02-19 ... ERROR neutron     raise nsx_exc.NsxPluginException(err_msg=error)
 2016-02-19 ... ERROR neutron NsxPluginException: An unexpected error occurred in the NSX
    Plugin: Configured datacenter_moid not found
 2016-02-19 ... ERROR neutron

Neutron client returns 504 Gateway timeout
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

 root@node-1:~# neutron router-create r_app --router_type exclusive
 Result:
 <html><body><h1>504 Gateway Time-out</h1>
 The server didn't respond in time.
 </body></html>

This may signal that your NSX Manager or vCenter server are overloaded and
cannot handle the incoming requests in a certain amount of time. A possible
solution to this problem is to increase the haproxy timeouts for nova API and neutron.
Double values of the following settings:

* timeout client
* timeout client-fin
* timeout server
* timeout server-fin

Edit the configuration files in ``/etc/haproxy/conf.d`` and restart
haproxy on all controllers.

