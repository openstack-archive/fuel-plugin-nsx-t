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

from proboscis import test
from devops.helpers.helpers import icmp_ping
from devops.helpers.helpers import wait

from fuelweb_test.helpers import os_actions
from fuelweb_test.helpers.decorators import log_snapshot_after_test
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.settings import SERVTEST_PASSWORD
from fuelweb_test.settings import SERVTEST_TENANT
from fuelweb_test.settings import SERVTEST_USERNAME
from fuelweb_test.tests.base_test_case import SetupEnvironment
from tests.base_plugin_test import TestNSXtBase
from helpers import openstack as os_help
from helpers import vmrun

from tests.test_plugin_system import TestNSXtSystem

WORKSTATION_NODES = os.environ.get('WORKSTATION_NODES').split(' ')
WORKSTATION_USERNAME = os.environ.get('WORKSTATION_USERNAME')
WORKSTATION_PASSWORD = os.environ.get('WORKSTATION_PASSWORD')
VCENTER_IP = os.environ.get('VCENTER_IP')


@test(groups=["plugins", "nsxt_plugin", 'nsxt_failover'])
class TestNSXtFailover(TestNSXtBase):
    """Tests from test plan that have been marked as 'Automated'."""

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=['nsxt_uninstall_negative'])
    @log_snapshot_after_test
    def nsxt_uninstall_negative(self):
        """It is impossible to remove plugin while at least one environment exists.

        Scenario:
          1. Install NSX-T plugin on master node.
          2. Create a new environment with enabled NSX-T plugin.
          3. Try to delete plugin via cli from master node

        Duration: 10 min
        """
        self.show_step(1)
        self.install_nsxt_plugin()

        self.show_step(2)
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=self.default.cluster_settings,
            configure_ssl=False)
        self.enable_plugin(cluster_id)

        self.show_step(3)
        self.delete_nsxt_plugin(failover=True)

    @test(depends_on=[TestNSXtSystem.nsx_ha_mode],
          groups=['nsxt_shutdown_controller'])
    @log_snapshot_after_test
    def nsxt_shutdown_controller(self):
        """Check plugin functionality after shutdown primary controller.

        Scenario:
          1. Log in to the Fuel with preinstalled plugin and deployed
             enviroment with 3 controllers.
          2. Log in to Horizon.
          3. Create vcenter VM and check connectivity to outside world from VM.
          4. Shutdown primary controller.
          5. Ensure that VIPs are moved to other controller.
          6. Ensure taht there is a connectivity to outside world from created
             VM.
          7. Create a new network and attach it to default router.
          8. Create a vCenter VM with new network and check network
             connectivity via ICMP.

        Duration: 180 min
        """
        self.show_step(1)
        self.show_step(2)
        self.show_step(3)
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_ip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            os_ip, SERVTEST_USERNAME, SERVTEST_PASSWORD, SERVTEST_TENANT)
        os_help.create_instance(os_conn, az='vcenter')

        servers = os_conn.get_servers()
        ips = [
            os_conn.get_nova_instance_ip(s, net_name=self.default.PRIVATE_NET)
            for s in servers
        ]
        network = os_conn.nova.networks.find(label=self.default.PRIVATE_NET)
        security_group = os_conn.create_sec_group_for_ssh()
        _sec_groups = os_conn.neutron.list_security_groups()['security_groups']
        _serv_tenant_id = os_conn.get_tenant(SERVTEST_TENANT).id
        default_sg = [sg for sg in _sec_groups
                      if sg['tenant_id'] == _serv_tenant_id and
                      sg['name'] == 'default'][0]

        _, access_point_ip = os_help.create_access_point(
            os_conn=os_conn,
            nics=[{'net-id': network.id}],
            security_groups=[security_group.name, default_sg['name']])

        data = {ip: ['8.8.8.8'] for ip in ips}
        os_help.check_connection_through_host(access_point_ip, data)

        self.show_step(4)
        primary_ctrl_devops = self.fuel_web.get_nailgun_primary_node(
            self.env.d_env.nodes().slaves[0])
        self.fuel_web.warm_shutdown_nodes([primary_ctrl_devops])

        self.show_step(5)
        node = self.fuel_web.get_nailgun_node_by_base_name()
        cmds = ['nova-manage service list | grep vcenter-vmcluster1',
                'nova-manage service list | grep vcenter-vmcluster2']
        os_help.check_service(ip=node['ip'], commands=cmds)

        self.show_step(6)
        os_help.check_connection_through_host(access_point_ip, data)

        self.show_step(7)
        net = os_conn.create_network(network_name='net_1')
        sub = os_conn.create_subnet(subnet_name='sub_1',
                                    network_id=net['network']['id'],
                                    cidr='192.168.77.0/24')
        self.show_step(8)
        os_help.create_instance(os_conn, az='vcenter', net=net['network'])
        # net_1 = os_conn.nova.networks.find(label='net_1')
        ips_1 = [
            os_conn.get_nova_instance_ip(s, net_name='net_1') for s in servers
        ]
        # _, access_point_ip = os_help.create_access_point(
        #     os_conn=os_conn,
        #     nics=[{'net-id': network.id}, {'net-id': net_1.id}],
        #     security_groups=[security_group.name, default_sg['name']])
        ip_pairs = {key: ips_1 for key in data}
        os_help.check_connection_through_host(access_point_ip,ip_pairs)
        # TODO

    @test(depends_on=[TestNSXtSystem.nsx_ha_mode],
          groups=['nsxt_reboot_vcenter'])
    @log_snapshot_after_test
    def nsxt_reboot_vcenter(self):
        """Check cluster functionality after reboot vCenter.

        Scenario:
          1. Log in to the Fuel with installed plugin and deployed enviroment.
          2. Log in to Horizon.
          3. Launch vcenter instance VM_1 with image TestVM-VMDK.
          4. Launch vcenter instance VM_2 with image TestVM-VMDK.
          5. Check connection between VMs, send ping from VM_1 to VM_2 and
             vice verse.
          6. Reboot vcenter::
              vmrun -T ws-shared -h https://localhost:443/sdk -u vmware -p pass
              reset "[standard] vcenter/vcenter.vmx"

          7. Check that controller lost connection with vCenter.
          8. Wait for vCenter is online.
          9. Ensure that all instances from vCenter are displayed in dashboard.
          10. Ensure there is connectivity between VMs.
          11. Run OSTF.

        Duration: 180 min
        """
        self.show_step(1)
        self.show_step(2)

        cluster_id = self.fuel_web.get_last_created_cluster()
        os_ip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            os_ip, SERVTEST_USERNAME, SERVTEST_PASSWORD, SERVTEST_TENANT)

        self.show_step(3)
        os_help.create_instance(os_conn, az='vcenter')

        self.show_step(4)
        os_help.create_instance(os_conn, az='vcenter')

        self.show_step(5)
        servers = os_conn.get_servers()
        ips = [
            os_conn.get_nova_instance_ip(s, net_name=self.default.PRIVATE_NET)
            for s in servers
        ]
        network = os_conn.nova.networks.find(label=self.default.PRIVATE_NET)
        security_group = os_conn.create_sec_group_for_ssh()
        _sec_groups = os_conn.neutron.list_security_groups()['security_groups']
        _serv_tenant_id = os_conn.get_tenant(SERVTEST_TENANT).id
        default_sg = [sg for sg in _sec_groups
                      if sg['tenant_id'] == _serv_tenant_id and
                      sg['name'] == 'default'][0]
        _, access_point_ip = os_help.create_access_point(
            os_conn=os_conn,
            nics=[{'net-id': network.id}],
            security_groups=[security_group.name, default_sg['name']])
        os_help.ping_each_other(ips=ips, access_point_ip=access_point_ip)

        self.show_step(6)
        host_type = 'ws-shared'
        path_to_vmx_file = '"[standard] {0}/{0}.vmx"'
        host_name = 'https://localhost:443/sdk'

        vcenter_name = [name for name in WORKSTATION_NODES
                        if 'vcenter' in name].pop()
        node = vmrun.Vmrun(
            host_type,
            path_to_vmx_file.format(vcenter_name),
            host_name=host_name,
            username=WORKSTATION_USERNAME,
            password=WORKSTATION_PASSWORD)
        node.reset()

        self.show_step(7)
        wait(lambda: not icmp_ping(VCENTER_IP),
             interval=1,
             timeout=10,
             timeout_msg='vCenter is still available.')

        self.show_step(8)
        wait(lambda: icmp_ping(VCENTER_IP),
             interval=5,
             timeout=120,
             timeout_msg='vCenter is not available.')
        self.show_step(9)
        os_help.check_instances_state(os_conn)
        self.show_step(10)
        os_help.ping_each_other(ips=ips, access_point_ip=access_point_ip)

        self.show_step(11)
        self.fuel_web.run_ostf(cluster_id)
