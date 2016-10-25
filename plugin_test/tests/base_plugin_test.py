"""Copyright 2016 Mirantis, Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
"""

import os

from devops.helpers.ssh_client import SSHAuth
from proboscis.asserts import assert_true

from fuelweb_test import logger
from fuelweb_test.helpers import utils
from fuelweb_test.helpers.utils import pretty_log
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test.settings import SSH_IMAGE_CREDENTIALS
from helpers import settings

cirros_auth = SSHAuth(**SSH_IMAGE_CREDENTIALS)

class TestNSXtBase(TestBasic):
    """Base class for NSX-T plugin tests"""

    def __init__(self):
        super(TestNSXtBase, self).__init__()
        self.default = settings
        self.vcenter_az = 'vcenter'
        self.vmware_image = 'TestVM-VMDK'

    def install_nsxt_plugin(self):
        """Download and install NSX-T plugin on master node.

        :return: None
        """
        master_ip = self.ssh_manager.admin_ip
        utils.upload_tarball(ip=master_ip,
                             tar_path=self.default.NSXT_PLUGIN_PATH,
                             tar_target='/var')

        utils.install_plugin_check_code(
            ip=master_ip,
            plugin=os.path.basename(self.default.NSXT_PLUGIN_PATH))

    def enable_plugin(self, cluster_id, settings=None):
        """Enable NSX-T plugin on cluster.

        :param cluster_id: cluster id
        :param settings: settings in dict format
        :return: None
        """
        msg = "Plugin couldn't be enabled. Check plugin version. Test aborted"
        settings = settings if settings else {}
        checker = self.fuel_web.check_plugin_exists(cluster_id,
                                                    self.default.PLUGIN_NAME)
        assert_true(checker, msg)
        logger.info('Configure cluster with '
                    'following parameters: \n{}'.format(pretty_log(settings)))
        self.fuel_web.update_plugin_settings(
            cluster_id,
            self.default.PLUGIN_NAME,
            self.default.NSXT_PLUGIN_VERSION,
            dict(self.default.plugin_configuration, **settings))

    def reconfigure_cluster_interfaces(self, cluster_id):
        # clear network mapping enp0s6 for all deployed nodes
        nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in nodes:
            self.fuel_web.update_node_networks(node['id'],
                                               settings.assigned_networks)

    def delete_nsxt_plugin(self, failover=False):
        """Delete NSX-T plugin

        :param failover: True if we expect that plugin won't be deleted
        :return:
        """
        plugin_name = self.default.PLUGIN_NAME
        plugin_vers = self.default.NSXT_PLUGIN_VERSION
        tmp = "Plugin '{0}' {1} removed"
        msg = tmp.format(plugin_name, 'was' if failover else "wasn't")
        cmd = 'fuel plugins --remove {0}=={1}'.format(plugin_name, plugin_vers)

        self.ssh_manager.check_call(
            ip=self.ssh_manager.admin_ip,
            command=cmd,
            expected=[1 if failover else 0],
            raise_on_err=not failover
        )

    def _get_controller_with_vip(self):
        """Return name of controller with VIPs."""
        for node in self.env.d_env.nodes().slaves:
            ng_node = self.fuel_web.get_nailgun_node_by_devops_node(node)
            if ng_node['online'] and 'controller' in ng_node['roles']:
                hosts_vip = self.fuel_web.get_pacemaker_resource_location(
                    ng_node['devops_name'], 'vip__management')
                logger.info('Now primary controller is '
                            '{}'.format(hosts_vip[0].name))
                return hosts_vip[0].name
        return True

    def ping_from_instance(self, src_floating_ip, dst_ip, primary,
                           size=56, count=1):
        """Verify ping between instances.

        :param src_floating_ip: floating ip address of instance
        :param dst_ip: destination ip address
        :param primary: name of the primary controller
        :param size: number of data bytes to be sent
        :param count: number of packets to be sent
        """

        with self.fuel_web.get_ssh_for_node(primary) as ssh:
            command = "ping -s {0} -c {1} {2}".format(size, count,
                                                      dst_ip)
            ping = ssh.execute_through_host(
                hostname=src_floating_ip,
                cmd=command,
                auth=cirros_auth
            )

            logger.info("Ping result is {}".format(ping['stdout_str']))
            return 0 == ping['exit_code']
