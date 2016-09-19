
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

 2016-10-28 12:32:26.086 2832 INFO vmware_nsx.nsxlib.v3.cluster [-] Endpoint
   'https://172.16.0.249' changing from state 'INITIALIZED' to 'DOWN'
 2016-10-28 12:32:26.087 2832 WARNING vmware_nsx.nsxlib.v3.cluster [-] Failed to
   validate API cluster endpoint '[DOWN] https://172.16.0.249' due to: [Errno 1]
   _ssl.c:510: error:14090086:SSL routines:SSL3_GET_SERVER_CERTIFICATE:certificate verify failed


This error indicates that you enabled the SSL/TLS certificate verification, but
the certificate verification failed during connection to NSX Manager.
The possible causes are:

 #. NSX Manager certificate expired. Log into NSX Manager web GUI and check
    certificate validation dates.
 #. Check if the certification authority (CA) certificate is still valid.
    The CA certificate is specified by ``ca_file`` directive in ``nsx.ini``
    (usually ``/etc/neutron/plugins/vmware/nsx.ini`` on controller node).

User access problems
~~~~~~~~~~~~~~~~~~~~

::

 2016-10-28 12:28:20.060 18259 INFO vmware_nsx.plugins.nsx_v3.plugin [-] Starting NsxV3Plugin
 2016-10-28 12:28:20.201 18259 WARNING vmware_nsx.nsxlib.v3.client [-] The HTTP request returned error code 403,
    whereas 200 response codes were expected. Response body {u'module_name': u'common-service',
    u'error_message': u'The username/password combination is incorrect or the account specified has been locked.', u'error_code': u'98'}
 2016-10-28 12:28:20.202 18259 INFO vmware_nsx.nsxlib.v3.cluster [-] Endpoint 'https://172.16.0.249' changing
    from state 'INITIALIZED' to 'DOWN'
 2016-10-28 12:28:20.203 18259 WARNING vmware_nsx.nsxlib.v3.cluster [-] Failed to validate API cluster endpoint
    '[DOWN] https://172.16.0.249' due to: Unexpected error from backend manager (['172.16.0.249']) for GET https://172.16.0.249/api/
    v1/transport-zones : The username/password combination is incorrect or the account specified has been locked.


Verify that username and password that are entered on the plugins pane are
correct.
