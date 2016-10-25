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

from proboscis import test
from proboscis.asserts import assert_true
from devops.helpers.helpers import tcp_ping
from devops.helpers.helpers import wait

from fuelweb_test.helpers.os_actions import OpenStackActions
from fuelweb_test.helpers.decorators import log_snapshot_after_test
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.settings import SERVTEST_PASSWORD
from fuelweb_test.settings import SERVTEST_TENANT
from fuelweb_test.settings import SERVTEST_USERNAME
from fuelweb_test.tests.base_test_case import SetupEnvironment
from system_test import logger
from tests.base_plugin_test import TestNSXtBase
from tests.test_plugin_nsxt import TestNSXtBVT


@test(groups=['nsxt_plugin', 'nsxt_failover'])
class TestNSXtFailover(TestNSXtBase):
    """NSX-t failover automated tests"""

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=['nsxt_uninstall_negative'])
    @log_snapshot_after_test
    def nsxt_uninstall_negative(self):
        """Check plugin can not be removed while it is enabled for environment.

        Scenario:
            1. Install NSX-T plugin on Fuel Master node with 5 slaves.
            2. Create new environment with enabled NSX-T plugin.
            3. Try to delete plugin via cli from master node.

        Duration: 10 min
        """
        # Install NSX-T plugin on Fuel Master node with 5 slaves
        self.show_step(1)
        self.env.revert_snapshot('ready_with_5_slaves')
        self.install_nsxt_plugin()

        # Create new environment with enabled NSX-T plugin
        self.show_step(2)
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=self.default.cluster_settings,
            configure_ssl=False)
        self.enable_plugin(cluster_id)

        # Try to delete plugin via cli from master node
        self.show_step(3)
        self.delete_nsxt_plugin(failover=True)

    @test(depends_on=[TestNSXtBVT.nsxt_bvt],
          groups=['nsxt_shutdown_controller'])
    @log_snapshot_after_test
    def nsxt_shutdown_controller(self):
        """Check plugin functionality after shutdown primary controller.

        Scenario:
            1. Get access to OpenStack.
            2. Create VMs and check connectivity to outside world
               from VM.
            3. Shutdown primary controller.
            4. Ensure that VIPs are moved to another controller.
            5. Ensure that there is a connectivity to outside world from
               created VM.
            6. Create new network and attach it to default router.
            7. Create VMs with new network and check network
               connectivity via ICMP.

        Duration: 180 min
        """

        # Get access to OpenStack
        self.show_step(1)
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        # Create vcenter VM and check connectivity to outside world from VM
        self.show_step(2)
        image = os_conn.get_image(self.vmware_image)
        net = os_conn.get_network(self.default.PRIVATE_NET)
        sec_group = os_conn.create_sec_group_for_ssh()

        vms=[]
        vms.append(os_conn.create_server(
            net_id=net['id'],
            security_groups=[sec_group]))
        vms.append(os_conn.create_server(
            availability_zone=self.vcenter_az,
            image=image,
            net_id=net['id'],
            security_groups=[sec_group]))

        ips = []
        for vm in vms:
            floating = os_conn.assign_floating_ip(vm)
            wait(lambda: tcp_ping(floating.ip, 22),
                 timeout=180,
                 timeout_msg="Node {ip} is not accessible by SSH.".format(
                     ip=floating.ip))
            ips.append(floating.ip)

        vip_contr = self._get_controller_with_vip()
        for ip in ips:
            logger.info('Check connectivity from {0}'.format(ip))
            assert_true(self.ping_from_instance(ip,
                                                '8.8.8.8',
                                                vip_contr),
                        'Ping failed')

        # Shutdown primary controller
        self.show_step(3)
        primary_ctrl_devops = self.fuel_web.get_nailgun_primary_node(
            self.env.d_env.nodes().slaves[0])
        self.fuel_web.warm_shutdown_nodes([primary_ctrl_devops])

        # Ensure that VIPs are moved to another controller
        self.show_step(4)
        vip_contr_new = self._get_controller_with_vip()
        assert_true(vip_contr_new and vip_contr_new != vip_contr,
                    'VIPs have not been moved to another controller')
        logger.info('VIPs have been moved to another controller')

        # Ensure that there is a connectivity to outside world from created VM
        self.show_step(5)
        for ip in ips:
            logger.info('Check connectivity from {0}'.format(ip))
            assert_true(self.ping_from_instance(ip,
                                                '8.8.8.8',
                                                vip_contr_new),
                        'Ping failed')

        # Create new network and attach it to default router
        self.show_step(6)
        net_1 = os_conn.create_network(network_name='net_1')['network']
        subnet_1 = os_conn.create_subnet(
            subnet_name='subnet_1',
            network_id=net_1['id'],
            cidr='192.168.77.0/24')

        default_router = os_conn.get_router(os_conn.get_network(
            self.default.ADMIN_NET))
        os_conn.add_router_interface(router_id=default_router['id'],
                                     subnet_id=subnet_1['id'])

        # Create vCenter VM with new network and check ICMP connectivity
        self.show_step(7)

        vms=[]
        vms.append(os_conn.create_server(
            net_id=net_1['id'],
            security_groups=[sec_group]))
        vms.append(os_conn.create_server(
            availability_zone=self.vcenter_az,
            image=image,
            net_id=net_1['id'],
            security_groups=[sec_group]))

        ips = []
        for vm in vms:
            floating = os_conn.assign_floating_ip(vm)
            wait(lambda: tcp_ping(floating.ip, 22),
                 timeout=180,
                 timeout_msg="Node {ip} is not accessible by SSH.".format(
                     ip=floating.ip))
            ips.append(floating.ip)

        for ip in ips:
            logger.info('Check connectivity from {0}'.format(ip))
            assert_true(self.ping_from_instance(ip,
                                                '8.8.8.8',
                                                vip_contr_new),
                        'Ping failed')
