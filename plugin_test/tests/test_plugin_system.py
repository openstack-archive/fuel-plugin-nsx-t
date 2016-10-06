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

from devops.error import TimeoutError
from devops.helpers.helpers import wait
from proboscis import test
from proboscis.asserts import assert_true
from proboscis.asserts import assert_false

from fuelweb_test import logger
from fuelweb_test.helpers import os_actions
from fuelweb_test.helpers.decorators import log_snapshot_after_test
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.settings import SERVTEST_PASSWORD
from fuelweb_test.settings import SERVTEST_TENANT
from fuelweb_test.settings import SERVTEST_USERNAME
from fuelweb_test.tests.base_test_case import SetupEnvironment
from tests.base_plugin_test import TestNSXtBase
from helpers import openstack as os_help


@test(groups=['nsxt_plugin', 'nsxt_system'])
class TestNSXtSystem(TestNSXtBase):
    """Tests from test plan that have been marked as 'Automated'."""

    _tenant = None  # default tenant

    def _create_net(self, os_conn, name):
        """Create network in default tenant."""
        if not self._tenant:
            self._tenant = os_conn.get_tenant(SERVTEST_TENANT)

        return os_conn.create_network(
            network_name=name, tenant_id=self._tenant.id)['network']

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=['nsxt_ha_mode'])
    @log_snapshot_after_test
    def nsxt_ha_mode(self):
        """Set up for system tests.

        Scenario:
            1. Install NSX-T plugin to Fuel Master node with 5 slaves.
            2. Create new environment with the following parameters:
                * Compute: KVM, QEMU with vCenter
                * Networking: Neutron with NSX-T plugin
                * Storage: default
                * Additional services: default
            3. Add nodes with following roles:
                * Controller
                * Controller
                * Controller
                * Compute
            4. Configure interfaces on nodes.
            5. Enable and configure NSX-T plugin, configure network settings.
            6. Configure VMware vCenter Settings. Add 1 vSphere cluster and
               configure Nova Compute instance on controllers.
            7. Verify networks.
            8. Deploy cluster.
            9. Run OSTF.

        Duration: 120 min
        """
        self.show_step(1)  # Install plugin to Fuel Master node with 5 slaves
        self.env.revert_snapshot('ready_with_5_slaves')
        self.install_nsxt_plugin()

        self.show_step(2)  # Create new environment with vCenter
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=self.default.cluster_settings,
            configure_ssl=False)

        self.show_step(3)  # Add nodes
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-01': ['controller'],
                                    'slave-02': ['controller'],
                                    'slave-03': ['controller'],
                                    'slave-04': ['compute']})

        self.show_step(4)  # Configure interfaces on nodes
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(5)  # Enable and configure plugin, configure networks
        self.enable_plugin(cluster_id)

        # Configure VMware settings. 1 Cluster, 1 Nova Instance on controllers
        self.show_step(6)
        self.fuel_web.vcenter_configure(cluster_id)

        self.show_step(7)  # Verify networks
        self.fuel_web.verify_network(cluster_id)

        self.show_step(8)  # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(9)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)

    @test(depends_on=[nsxt_ha_mode],
          groups=['nsxt_create_terminate_networks'])
    @log_snapshot_after_test
    def nsxt_create_terminate_networks(self):
        """Check abilities to create and terminate networks on NSX.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Create private networks net_01 and net_02 with subnets.
            4. Check that networks are present in vCenter.
            5. Remove private network net_01.
            6. Check that network net_01 has been removed from the vCenter.
            7. Create private network net_01.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_ha_mode')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()

        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        # Create private networks net_01 and net_02 with subnets
        self.show_step(3)
        net1 = self._create_net(os_conn, 'net_01')
        os_conn.create_subnet(subnet_name=net1['name'],
                              network_id=net1['id'],
                              cidr='192.168.1.0/24',
                              ip_version=4)

        net2 = self._create_net(os_conn, 'net_02')
        os_conn.create_subnet(subnet_name=net2['name'],
                              network_id=net2['id'],
                              cidr='192.168.2.0/24',
                              ip_version=4)

        self.show_step(4)  # Check that networks are present in vCenter
        assert_true(os_conn.get_network(net1['name'])['id'] == net1['id'])
        assert_true(os_conn.get_network(net2['name'])['id'] == net2['id'])

        self.show_step(5)  # Remove private network net_01
        os_conn.nova.delete_network(net1['name'])
        networks = os_conn.get_nova_network_list()['networks']
        net_names = [net['name'] for net in networks]

        # Check that network net_01 has been removed from the vCenter
        self.show_step(6)
        assert_false(net1['name'] in net_names)
        assert_true(net2['name'] in net_names)

        self.show_step(7)  # Create private network net_01
        self._create_net(os_conn, 'net_01')

    @test(depends_on=[nsxt_ha_mode],
          groups=['nsxt_multi_vnic'])
    @log_snapshot_after_test
    def nsxt_multi_vnic(self):
        """Check ability to assign multiple vNIC to a single VM.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Add two private networks (net01 and net02).
            4. Add one subnet to each network:
                  net01_subnet01: 192.168.1.0/24,
                  net02_subnet01, 192.168.2.0/24
               NOTE: We have a constraint about network interfaces.
               One of subnets should have gateway and another should not.
               So disable gateway on that subnet.
            5. Launch instance VM_1 with image TestVM-VMDK in vcenter az.
            6. Launch instance VM_2 with image TestVM in nova az.
            7. Check ability to assign multiple vNIC net01 and net02 to VM_1.
            8. Check ability to assign multiple vNIC net01 and net02 to VM_2.
            9. Send icmp ping from VM_1 to VM_2 and vice versa.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_hs_mode')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()

        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        self.show_step(3)  # Add two private networks (net01 and net02)
        net1 = self._create_net(os_conn, 'net_01')
        net2 = self._create_net(os_conn, 'net_02')

        # Add one subnet to each network: net01_subnet01 and net02_subnet01.
        # One of subnets should have gateway and another should not
        self.show_step(4)
        os_conn.create_subnet(
            subnet_name=net1['name'],
            network_id=net1['id'],
            cidr='192.168.1.0/24',
            ip_version=4,
            gateway_ip=None)

        os_conn.create_subnet(
            subnet_name=net2['name'],
            network_id=net2['id'],
            cidr='192.168.2.0/24',
            ip_version=4)

        net1 = os_conn.nova.networks.find(label=net1['name'])
        net2 = os_conn.nova.networks.find(label=net2['name'])

        # Launch instance VM_1 with image TestVM-VMDK in vcenter az
        self.show_step(5)
        vm1 = os_help.create_instance(os_conn, az='vcenter')

        # Launch instance VM_2 with image TestVM in nova az
        self.show_step(6)
        vm2 = os_help.create_instance(os_conn)

        # Check ability to assign multiple vNIC net01 and net02 to VM_1
        self.show_step(7)
        vm1.interface_attach(None, net1.id, None)
        vm1.interface_attach(None, net2.id, None)
        vm1.reboot()

        # Check ability to assign multiple vNIC net01 and net02 to VM_2
        self.show_step(8)
        vm2.interface_attach(None, net1.id, None)
        vm2.interface_attach(None, net2.id, None)
        vm2.reboot()

        self.show_step(9)  # Send icmp ping from VM_1 to VM_2 and vice versa
        nets = [net1['name'], net2['name']]

        vm1_ips = [os_conn.get_nova_instance_ip(vm2, net_name=n) for n in nets]
        vm2_ips = [os_conn.get_nova_instance_ip(vm2, net_name=n) for n in nets]

        _, access_point_ip = os_help.create_access_point(
            os_conn=os_conn,
            nics=[{'net-id': net1.id}, {'net-id': net2.id}],
            security_groups=['default'])

        p1, p2 = {i: vm2_ips for i in vm1_ips}, {i: vm1_ips for i in vm2_ips}
        ip_pair = p1.update(p2)

        os_help.check_connection_through_host(access_point_ip, ip_pair)

    @test(depends_on=[nsxt_ha_mode],
          groups=['nsxt_connectivity_diff_networks'])
    @log_snapshot_after_test
    def nsxt_connectivity_diff_networks(self):
        """Check connection between VMs from different nets through the router.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Add two private networks (net01 and net02).
            4. Add one subnet to each network:
                   net01_subnet01: 192.168.101.0/24,
                   net02_subnet01, 192.168.102.0/24.
               Disable gateway for all subnets.
            5. Launch instances VM_1 and VM_2 in net01 with image TestVM-VMDK
               and flavor m1.tiny in vcenter az.
            6. Attach default private net as a NIC 1.
            7. Launch instances VM_3 and VM_4 in net02 with image TestVM and
               flavor m1.tiny in nova az.
            8. Attach default private net as a NIC 1.
            9. Verify that VMs of same networks communicate between each other.
               Send icmp ping from VM_1 to VM_2, VM_3 to VM_4 and vice versa.
            10. Verify that VMs of different networks don't communicate
                between each other. Send icmp ping from VM_1 to VM_3, VM_4 to
                VM_2 and vice versa.
            11. Create Router_01, set gateway and add interface to external
                network.
            12. Enable gateway on subnets. Attach private networks to router.
            13. Verify that VMs of different networks communicate between
                each other. Send icmp ping from VM_1 to VM_3, VM_4 to VM_2 and
                vice versa.
            14. Create Router_02, set gateway and add interface to external
                network.
            15. Detach net_02 from Router_01 and attach it to Router_02.
            16. Assign floating IPs to all created VMs.
            17. Verify that VMs of different networks communicate between
                each other by FIPs. Send icmp ping from VM_1 to VM_3, VM_4 to
                VM_2 and vice versa.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_ha_mode')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        self.show_step(3)  # Add two private networks (net01 and net02)
        net01 = self._create_net(os_conn, 'net_01')
        net02 = self._create_net(os_conn, 'net_02')

        # Add one subnet to each network: net01_subnet01 and net02_subnet01.
        # Disable gateway for all subnets
        self.show_step(4)
        os_conn.create_subnet(
            subnet_name=net01['name'],
            network_id=net01['id'],
            cidr='192.168.1.0/24',
            ip_version=4,
            gateway_ip=None)

        os_conn.create_subnet(
            subnet_name=net02['name'],
            network_id=net02['id'],
            cidr='192.168.2.0/24',
            ip_version=4,
            gateway_ip=None)

        net1 = os_conn.nova.networks.find(label=net01['name'])
        net2 = os_conn.nova.networks.find(label=net02['name'])
        default_net = os_conn.nova.networks.find(
            label=self.default.PRIVATE_NET)

        # Launch instances VM_1 and VM_2 in net01 with image TestVM-VMDK
        # and flavor m1.tiny in vcenter az
        self.show_step(5)
        tiny_flavor = [flavor for flavor in self.nova.flavors.list()
                       if flavor.name == 'm1.tiny'].pop()
        vm1 = os_help.create_instance(
            os_conn, net=net1, az='vcenter', flavor=tiny_flavor.id)
        vm2 = os_help.create_instance(
            os_conn, net=net1, az='vcenter', flavor=tiny_flavor.id)

        self.show_step(6)  # Attach default private net as a NIC 1
        vm1.interface_attach(None, default_net.id, None)
        vm2.interface_attach(None, default_net.id, None)
        vm1.reboot()
        vm2.reboot()

        # Launch instances VM_3 and VM_4 in net02 with image TestVM and
        # flavor m1.tiny in nova az
        self.show_step(7)
        vm3 = os_help.create_instance(os_conn, net=net2, flavor=tiny_flavor.id)
        vm4 = os_help.create_instance(os_conn, net=net2, flavor=tiny_flavor.id)

        self.show_step(8)  # Attach default private net as a NIC 1
        vm3.interface_attach(None, default_net.id, None)
        vm4.interface_attach(None, default_net.id, None)
        vm3.reboot()
        vm4.reboot()

        # Verify that VMs of same networks communicate between each other.
        # Send icmp ping from VM_1 to VM_2, VM_3 to VM_4 and vice versa
        self.show_step(9)
        _, access_point_ip = os_help.create_access_point(
            os_conn=os_conn, nics=[{'net-id': default_net.id}],
            security_groups=['default'])

        vm1_ip = os_conn.get_nova_instance_ip(vm1, net_name=net01['name'])
        vm2_ip = os_conn.get_nova_instance_ip(vm2, net_name=net01['name'])

        vm3_ip = os_conn.get_nova_instance_ip(vm3, net_name=net02['name'])
        vm4_ip = os_conn.get_nova_instance_ip(vm4, net_name=net02['name'])

        net01_ips, net02_ips = [vm1_ip, vm2_ip], [vm3_ip, vm4_ip]

        os_help.ping_each_other(ips=net01_ips, access_point_ip=access_point_ip)
        os_help.ping_each_other(ips=net02_ips, access_point_ip=access_point_ip)

        # Verify that VMs of different networks don't communicate between each
        # other. Send icmp ping from VM_1 to VM_3, VM_4 to VM_2 and vice versa
        self.show_step(10)
        pair1, pair2 = [vm1_ip, vm3_ip], [vm2_ip, vm4_ip]

        os_help.ping_each_other(ips=pair1,
                                access_point_ip=access_point_ip,
                                expected_ec=1)
        os_help.ping_each_other(ips=pair2,
                                access_point_ip=access_point_ip,
                                expected_ec=1)

        # Create Router_01, set gateway and add interface to external network
        self.show_step(11)
        rout1 = os_conn.get_router(os_conn.get_network(self.ext_net_name))

        external_net = os_conn.nova.networks.find(label=self.default.ADMIN_NET)
        os_conn.add_router_interface(router_id=rout1['id'],
                                     subnet_id=external_net.id)

        # Enable gateway on subnets. Attach private networks to router
        self.show_step(12)
        os_conn.add_router_interface(router_id=rout1['id'], subnet_id=net1.id)
        os_conn.add_router_interface(router_id=rout1['id'], subnet_id=net2.id)

        # Verify that VMs of different networks communicate between each other.
        # Send icmp ping from VM_1 to VM_3, VM_4 to VM_2 and vice versa
        self.show_step(13)
        os_help.ping_each_other(ips=pair1, access_point_ip=access_point_ip)
        os_help.ping_each_other(ips=pair2, access_point_ip=access_point_ip)

        # Create Router_02, set gateway and add interface to external network
        self.show_step(14)
        rout2 = os_conn.get_router(os_conn.get_network(self.ext_net_name))
        os_conn.add_router_interface(router_id=rout2['id'],
                                     subnet_id=external_net.id)

        # Detach net_02 from Router_01 and attach it to Router_02
        self.show_step(15)
        os_conn.neutron.remove_interface_router(
            rout1['id'], {'router_id': rout1['id'], 'subnet_id': net2.id})
        os_conn.add_router_interface(router_id=rout2['id'], subnet_id=net2.id)

        self.show_step(16)  # Assign floating IPs to all created VMs
        fips = []
        for server in [vm1, vm2, vm3, vm4]:
            fips.append(os_conn.assign_floating_ip(server).ip)

        # Verify that VMs of different networks communicate between each other
        # by FIPs. Send ping from VM_1 to VM_3, VM_4 to VM_2 and vice versa
        self.show_step(17)
        os_help.ping_each_other(fips)

    @test(depends_on=[nsxt_ha_mode],
          groups=['nsxt_different_tenants'])
    @log_snapshot_after_test
    def nsxt_different_tenants(self):
        """Check isolation between VMs in different tenants.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Create and activate non-admin tenant test_tenant.
               Members: admin with admin and member.
            4. Create network with 2 subnet.
            5. Create Router, set gateway and add interface.
            6. Launch instance VM_1
            7. Activate default tenant.
            8. Create network with subnet.
            9. Create Router, set gateway and add interface.
            10. Launch instance VM_2.
            11. Verify that VMs on different tenants don't communicate
                between each other. Send icmp ping from VM_1 of admin tenant to
                VM_2 of test_tenant and vice versa.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_hs_mode')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()

        os_ip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            os_ip, SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        # Create and activate non-admin tenant test_tenant.
        # Members: admin with admin and member.
        self.show_step(3)
        os_conn.create_user_and_tenant('test_tenant', 'test', 'test')
        os_help.add_role_to_user(os_conn, 'test', 'admin', 'test_tenant')

        test_tenant_conn = os_actions.OpenStackActions(os_ip, 'test', 'test',
                                                       'test_tenant')
        test_tenant = test_tenant_conn.get_tenant('test_tenant')

        # Create network with 2 subnet
        self.show_step(4)
        test_tenant_net = test_tenant_conn.create_network(
            network_name='net_1',
            tenant_id=test_tenant.id)['network']

        test_tenant_subnet1 = test_tenant_conn.create_subnet(
            subnet_name='sub_1',
            network_id=test_tenant_net['id'],
            cidr='192.168.1.0/24')

        test_tenant_subnet2 = test_tenant_conn.create_subnet(
            subnet_name='sub_2',
            network_id=test_tenant_net['id'],
            cidr='192.168.2.0/24')

        self.show_step(5)  # Create Router, set gateway and add interface
        router = test_tenant_conn.create_router('router_1', tenant=test_tenant)

        test_tenant_conn.add_router_interface(
            router_id=router["id"], subnet_id=test_tenant_subnet1["id"])
        test_tenant_conn.add_router_interface(
            router_id=router["id"], subnet_id=test_tenant_subnet2["id"])

        self.show_step(6)  # Launch instance VM_1
        clerk_vm = os_help.create_instance(test_tenant_conn,
                                           net=test_tenant_net)

        self.show_step(7)  # Activate default tenant
        self.show_step(8)  # Create network with subnet
        admin_net = self._create_net(os_conn, 'net_1')

        admin_subnet_1 = os_conn.create_subnet(
            subnet_name='sub_1',
            network_id=admin_net['id'],
            cidr='192.168.3.0/24')

        admin_subnet_2 = os_conn.create_subnet(
            subnet_name='sub_2',
            network_id=admin_net['id'],
            cidr='192.168.4.0/24')

        self.show_step(9)  # Create Router, set gateway and add interface
        router_1 = test_tenant_conn.create_router('router_1',
                                                  tenant=self._tenant)

        os_conn.add_router_interface(
            router_id=router_1["id"], subnet_id=admin_subnet_1["id"])
        os_conn.add_router_interface(
            router_id=router["id"], subnet_id=admin_subnet_2["id"])

        self.show_step(10)  # Launch instance VM_2
        admin_vm = os_help.create_instance(os_conn, net=admin_net)

        # Verify that VMs on different tenants don't communicate between each
        # other. Send icmp ping from VM_1 of admin tenant to VM_2 of
        # test_tenant and vice versa
        self.show_step(11)
        test_tenant_ip = test_tenant_conn.get_nova_instance_ip(
            clerk_vm, net_name=test_tenant_net['name'])
        admin_ip = os_conn.get_nova_instance_ip(
            admin_vm, net_name=admin_net['name'])

        test_tenant_fip = test_tenant_conn.assign_floating_ip(clerk_vm)
        admin_fip = os_conn.assign_floating_ip(admin_vm)

        pair = {test_tenant_fip: [admin_ip], admin_fip: [test_tenant_ip]}

        os_help.check_connection_vms(ip_pair=pair, result_of_command=1)

    @test(depends_on=[nsxt_ha_mode],
          groups=['nsxt_same_ip_different_tenants'])
    @log_snapshot_after_test
    def nsxt_same_ip_different_tenants(self):
        """Check connectivity between VMs with same ip in different tenants.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Create 2 non-admin tenants 'test_1' and 'test_2'.
               Members: admin with admin and member.
            4. In tenant 'test_1' create net1 and subnet1: 10.0.0.0/24.
            5. In tenant 'test_1' create security group 'SG_1' and add rule
               that allows ingress icmp traffic.
            6. In tenant 'test_2' create net2 and subnet2: 10.0.0.0/24
            7. In tenant 'test_2' create security group 'SG_2'.
            8. In tenant 'test_1' add VM_1 of vcenter in net1 with ip 10.0.0.4
               and 'SG_1' as security group.
            9. In tenant 'test_1' add VM_2 of nova in net1 with ip 10.0.0.5 and
               'SG_1' as security group.
            10. In tenant 'test_2' create net1 and subnet1: 10.0.0.0/24.
            11. In tenant 'test_2' create security group 'SG_1' and add rule
                that allows ingress icmp traffic.
            12. In tenant 'test_2' add VM_3 of vcenter in net1 with ip 10.0.0.4
                and 'SG_1' as security group.
            13. In tenant 'test_2' add VM_4 of nova in net1 with ip 10.0.0.5
                and 'SG_1' as security group.
            14. Assign floating IPs for all created VMs.
            15. Verify that VMs with same ip on different tenants communicate
                between each other by FIPs. Send icmp ping from VM_1 to VM_3,
                VM_2 to VM_4 and vice versa.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_hs_mode')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()

        os_ip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            os_ip, SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        # Create 2 non-admin tenants 'test_1' and 'test_2'. Members: admin
        # with admin and member
        self.show_step(3)
        os_conn.create_user_and_tenant('test_1', 'test', 'test')
        os_help.add_role_to_user(os_conn, 'test', 'admin', 'test_1')

        os_conn.create_user_and_tenant('test_2', 'test', 'test')
        os_help.add_role_to_user(os_conn, 'test', 'admin', 'test_2')

        test1_conn = os_actions.OpenStackActions(
            os_ip, 'test', 'test', 'test_1')
        test2_conn = os_actions.OpenStackActions(
            os_ip, 'test', 'test', 'test_2')

        test1_tenant = test1_conn.get_tenant('test_1')
        test2_tenant = test2_conn.get_tenant('test_2')

        # In tenant 'test_1' create net1 and subnet1 with CIDR 10.0.0.0/24
        self.show_step(4)
        test1_net = test1_conn.create_network(
            network_name='net1',
            tenant_id=test1_tenant.id)['network']

        test1_subnet1 = test1_conn.create_subnet(
            subnet_name='subnet1',
            network_id=test1_net['id'],
            cidr='10.0.0.0/24')

        # In tenant 'test_1' create security group 'SG_1' and add rule that
        # allows ingress icmp traffic
        self.show_step(5)
        sg_1 = self.nova.security_groups.create('SG_1', 'descr')

        ruleset = {
            'ip_protocol': 'icmp',
            'from_port': -1,
            'to_port': -1,
            'cidr': '0.0.0.0/0',
        }
        self.nova.security_group_rules.create(secgroup.id, **ruleset)

        # In tenant 'test_2' create net2 and subnet2 with CIDR 10.0.0.0/24
        self.show_step(6)
        test2_net = test2_conn.create_network(
            network_name='net2',
            tenant_id=test2_tenant.id)['network']

        test2_subnet2 = test2_conn.create_subnet(
            subnet_name='subnet2',
            network_id=test2_net['id'],
            cidr='10.0.0.0/24')

        self.show_step(7)  # In tenant 'test_2' create security group 'SG_2'
        sg_2 = self.nova.security_groups.create('SG_2', 'descr')
        self.nova.security_group_rules.create(secgroup.id, **ruleset)

        # In tenant 'test_1' add VM_1 of vcenter in net1 with ip 10.0.0.4
        # and 'SG_1' as security group
        self.show_step(8)

        # In tenant 'test_1' add VM_2 of nova in net1 with ip 10.0.0.5 and
        # 'SG_1' as security group
        self.show_step(9)

        # In tenant 'test_2' create net1 and subnet1 with CIDR 10.0.0.0/24
        self.show_step(10)

        # In tenant 'test_2' create security group 'SG_1' and add rule that
        # allows ingress icmp traffic
        self.show_step(11)

        # In tenant 'test_2' add VM_3 of vcenter in net1 with ip 10.0.0.4
        # and 'SG_1' as security group
        self.show_step(12)

        # In tenant 'test_2' add VM_4 of nova in net1 with ip 10.0.0.5 and
        # 'SG_1' as security group
        self.show_step(13)

        self.show_step(14)  # Assign floating IPs for all created VMs

        # Verify that VMs with same ip on different tenants communicate
        # between each other by FIPs. Send icmp ping from VM_1 to VM_3,
        # VM_2 to VM_4 and vice versa
        self.show_step(15)

    @test(depends_on=[nsxt_ha_mode],
          groups=['nsxt_public_network_availability'])
    @log_snapshot_after_test
    def nsxt_public_network_availability(self):
        """Check connectivity Vms to public network.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Create net1 with net1_subnet: 192.168.111.0/24
               and attach it to default router.
            4. Launch instance VM_1 of vcenter az with image TestVM-VMDK and
               flavor m1.tiny in default net.
            5. Launch instance VM_1 of nova az with image TestVM and flavor
               m1.tiny in net1.
            6. Send ping from instances VM_1 and VM_2 to 8.8.8.8.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_ha_mode')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()

        os_ip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            os_ip, SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        # Create net1 with net1_subnet: 192.168.111.0/24 and attach it
        # to default router
        self.show_step(3)
        net1 = self._create_net(os_conn, 'net01')

        subnet1 = os_conn.create_subnet(
            subnet_name=net1['name'],
            network_id=net1['id'],
            cidr='192.168.111.0/24')
        router = os_conn.get_router(os_conn.get_network(
                self.default.ADMIN_NET))

        os_conn.add_router_interface(router_id=router["id"],
                                     subnet_id=subnet1["id"])

        # Launch instance VM_1 of vcenter az with image TestVM-VMDK and
        # flavor m1.tiny in default net
        self.show_step(4)
        vm1 = os_help.create_instance(os_conn, net=net1, az='vcenter')
        vm1_ip = os_conn.get_nova_instance_ip(vm1, net1['name'])

        # Launch instance VM_1 of nova az with image TestVM and flavor
        # m1.tiny in net1
        self.show_step(5)
        vm2 = os_help.create_instance(os_conn, net=net1)
        vm2_ip = os_conn.get_nova_instance_ip(vm2, net1['name'])

        self.show_step(6)  # Send ping from instances VM_1 and VM_2 to 8.8.8.8
        _, access_point_ip = os_help.create_access_point(
            os_conn=os_conn, nics=[{'net-id': net1['id']}],
            security_groups=['default'])

        ip_pair = {vm1_ip: '8.8.8.8', vm2_ip: '8.8.8.8'}

        os_help.check_connection_through_host(access_point_ip, ip_pair)

    @test(depends_on=[nsxt_ha_mode],
          groups=['nsxt_floating_ip_to_public'])
    @log_snapshot_after_test
    def nsxt_floating_ip_to_public(self):
        """Check connectivity VMs to public network with floating ip.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Create net1 with net1_subnet: 192.168.111.0/24
               and attach it to default router.
            4. Launch instance VM_1 of vcenter az with image TestVM-VMDK and
               flavor m1.tiny in default net. Associate floating ip.
            5. Launch instance VM_1 of nova az with image TestVM and flavor
               m1.tiny in the net1. Associate floating ip.
            6. Send ping from instances VM_1 and VM_2 to 8.8.8.8.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_ha_mode')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()

        os_ip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            os_ip, SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        # Create net1 with net1_subnet: 192.168.111.0/24
        # and attach it to default router
        self.show_step(3)
        net1 = self._create_net(os_conn, 'net1')
        subnet = os_conn.create_subnet(
            subnet_name=net1['name'],
            network_id=net1['id'],
            cidr='192.168.111.0/24')

        default_router = os_conn.get_router(os_conn.get_network(
            self.default.ADMIN_NET))

        os_conn.add_router_interface(router_id=default_router["id"],
                                     subnet_id=subnet["id"])

        # Launch instance VM_1 of vcenter az with image TestVM-VMDK and
        # flavor m1.tiny in default net. Associate floating ip
        self.show_step(4)
        default_net = os_conn.nova.networks.find(
            label=self.default.PRIVATE_NET)
        vm1 = os_help.create_instance(os_conn, net=default_net, az='vcenter')
        vm1_fip = os_conn.assign_floating_ip(vm1)

        # Launch instance VM_1 of nova az with image TestVM and flavor
        # m1.tiny in the net1. Associate floating ip
        self.show_step(5)
        vm2 = os_help.create_instance(os_conn, net=net1)
        vm2_fip = os_conn.assign_floating_ip(vm2)

        self.show_step(6)  # Send ping from instances VM_1 and VM_2 to 8.8.8.8
        ip_pair = {vm1_fip: '8.8.8.8', vm2_fip: '8.8.8.8'}
        os_help.check_connection_vms(ip_pair=ip_pair)

    @test(depends_on=[nsxt_ha_mode],
          groups=['nsxt_create_and_delete_secgroups'])
    @log_snapshot_after_test
    def nsxt_create_and_delete_secgroups(self):
        """Check ability to create and delete security group.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Launch instance VM_1 in the tenant network net_02 with image
               TestVM-VMDK and flavor m1.tiny in vcenter az.
            4. Launch instance VM_2 in the tenant network net_02 with image
               TestVM and flavor m1.tiny in nova az.
            5. Create security groups SG_1 to allow ICMP traffic.
            6. Add Ingress rule for ICMP protocol to SG_1
            7. Attach SG_1 to VMs.
            8. Check ping between VM_1 and VM_2 and vice versa.
            9. Create security groups SG_2 to allow TCP traffic 22 port.
               Add Ingress rule for TCP protocol to SG_2
            10. Attach SG_2 to VMs.
            11. ssh from VM_1 to VM_2 and vice versa.
            12. Delete custom rules from SG_1 and SG_2.
            13. Check ping and ssh aren't available from VM_1 to VM_2 and
                vice versa.
            14. Add Ingress rule for ICMP protocol to SG_1.
            15. Add Ingress rule for SSH protocol to SG_2.
            16. Check ping between VM_1 and VM_2 and vice versa.
            17. Check ssh from VM_1 to VM_2 and vice versa.
            18. Attach VMs to default security group.
            19. Delete security groups.
            20. Check ping between VM_1 and VM_2 and vice versa.
            21. Check SSH from VM_1 to VM_2 and vice versa.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_ha_mode')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        self.show_step(3)

        self.show_step(4)

        self.show_step(5)

        self.show_step(6)

        self.show_step(7)

        self.show_step(8)

        self.show_step(9)

        self.show_step(10)

        self.show_step(11)

        self.show_step(12)

        self.show_step(13)

        self.show_step(14)

        self.show_step(15)

        self.show_step(16)

        self.show_step(17)

        self.show_step(18)

        self.show_step(19)

        self.show_step(20)

        self.show_step(21)

    @test(depends_on=[nsxt_ha_mode],
          groups=['nsxt_associated_addresses_communication_on_port'])
    @log_snapshot_after_test
    def nsxt_associated_addresses_communication_on_port(self):
        """Verify that only associated MAC|IP can communicate on logical port.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Launch 2 instances in each az.
            4. Verify that traffic can be successfully sent from and received
               on the MAC and IP address associated with the logical port.
            5. Configure new IP address from the subnet not like original one
               on the instance associated with the logical port:
                 * ifconfig eth0 down
                 * ifconfig eth0 192.168.99.14 netmask 255.255.255.0
                 * ifconfig eth0 up
            6. Verify that the instance can't communicate with that IP address.
            7. Revert IP address. Configure new MAC address on the instance
               associated with the logical port:
                 * ifconfig eth0 down
                 * ifconfig eth0 hw ether 00:80:48:BA:d1:30
                 * ifconfig eth0 up
            8. Verify that instance can't communicate with that MAC address
               and the original IP address.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_ha_mode')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        self.show_step(3)  # Launch 2 instances in each az

        self.show_step(4)

        self.show_step(5)

        self.show_step(6)

        self.show_step(7)

        self.show_step(8)

    @test(depends_on=[nsxt_ha_mode],
          groups=['nsxt_create_and_delete_vms'])
    @log_snapshot_after_test
    def nsxt_create_and_delete_vms(self):
        """Check instance creation in the one group simultaneously.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Launch 5 instances VM_1 simultaneously with image TestVM-VMDK
               and flavor m1.tiny in vcenter az in default net.
            4. Launch 5 instances VM_2 simultaneously with image TestVM and
               flavor m1.tiny in nova az in default net.
            5. Check connection between VMs (ping, ssh).
            6. Delete all VMs simultaneously.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_ha_mode')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        # Launch 5 instances VM_1 simultaneously. Image: TestVM-VMDK,
        # flavor: m1.tiny, az: vcenter, net: default
        self.show_step(3)
        ssh_sg = os_conn.create_sec_group_for_ssh()
        net = os_conn.nova.networks.find(label=self.default.PRIVATE_NET)

        flavors = os_conn.nova.flavors.list()
        tiny_flavor = [f for f in flavors if f.name == 'm1.tiny'][0]

        image = os_conn.get_image(os_help.zone_image_maps['vcenter'])
        os_conn.nova.servers.create(
            flavor=tiny_flavor,
            name='VM_1',
            image=image,
            min_count=5,
            availability_zone='vcenter',
            nics=net['id'],
            security_groups=ssh_sg)
        os_help.verify_instance_state(os_conn)

        # Launch 5 instances VM_2 simultaneously. Image TestVM,
        # flavor: m1.tiny, az: nova, net: default
        self.show_step(4)
        image = os_conn.get_image(os_help.zone_image_maps['nova'])
        os_conn.nova.servers.create(
            flavor=tiny_flavor,
            name='VM_2',
            image=image,
            min_count=5,
            availability_zone='nova',
            nics=net['id'],
            security_groups=ssh_sg)
        os_help.verify_instance_state(os_conn)

        self.show_step(5)  # Check connection between VMs (ping, ssh)
        instances = os_conn.nova.servers.list()
        fips = os_help.create_and_assign_floating_ips(os_conn, instances)
        os_help.ping_each_other(fips)

        self.show_step(6)  # Delete all VMs simultaneously
        for instance in instances:  # TODO
            instance.delete()

        wait(lambda: os_conn.get_servers() is None, timeout=300)

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=['nsxt_smoke_add_compute'])
    @log_snapshot_after_test
    def nsxt_smoke_add_compute(self):
        """Check that settings about new cluster are placed in neutron config.

        Scenario:
            1. Install NSX-T plugin to Fuel Master node with 5 slaves.
            2. Create cluster and configure NSX-T for the cluster.
            3. Add 3 controller nodes.
            4. Deploy cluster.
            5. Get configured clusters morefid (Managed Object Reference)
               from neutron config.
            6. Add node with compute-vmware role.
            7. Redeploy cluster with new node.
            8. Get new configured clusters morefid from neutron config.
            9. Check new cluster added in neutron config.

        Duration: 30 min
        """
        # Install NSX-T plugin to Fuel Master node with 5 slaves
        self.show_step(1)
        self.env.revert_snapshot('ready_with_5_slaves')
        self.install_nsxt_plugin()

        #  Create cluster and configure NSX-T for the cluster
        self.show_step(2)
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=self.default.cluster_settings,
            configure_ssl=False)

        self.show_step(3)  # Add 3 controller nodes
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-01': ['controller'],
                                    'slave-02': ['controller'],
                                    'slave-03': ['controller']})

        self.enable_plugin(cluster_id)
        self.reconfigure_cluster_interfaces(cluster_id)
        self.fuel_web.vcenter_configure(cluster_id)

        self.show_step(4)  # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Get configured clusters morefid (Managed Object Reference)
        # from neutron config
        self.show_step(5)
        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        ctrl = [n for n in nailgun_nodes if 'controller' in n['pending_roles']]

        old_configured_clusters = {}
        for c in ctrl:
            old_configured_clusters[c] = self.get_configured_clusters(c['ip'])
            logger.info('Old configured clusters on {0} is {1}'.format(
                    c, old_configured_clusters[c]))

        self.show_step(6)  # Add node with compute-vmware role
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-04': ['compute-vmware']})
        target_node = self.fuel_web.get_nailgun_node_by_name('slave-04')
        target_node = target_node['hostname']
        self.fuel_web.vcenter_configure(cluster_id,
                                        target_node_2=target_node,
                                        multiclusters=True)

        self.show_step(7)  # Redeploy cluster with new node
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Get new configured clusters morefid from neutron config
        self.show_step(8)
        new_configured_clusters = {}
        for c in ctrl:
            new_configured_clusters[c] = self.get_configured_clusters(c['ip'])
            logger.info('New configured clusters on {0} is {1}'
                        .format(c, new_configured_clusters[c]))

        self.show_step(9)  # Check new cluster added in neutron config
        for c in ctrl:
            assert_true(set(new_configured_clusters[c]) -
                        set(old_configured_clusters[c]),
                        'Clusters on node {0} was not reconfigured'.format(c))

    @test(depends_on=[nsxt_ha_mode],
          groups=['nsxt_hot'])
    @log_snapshot_after_test
    def nsxt_hot(self):
        """Deploy HOT.

        Scenario:
            1. Deploy cluster with NSX-t.
            2. On controller node create teststack with nsxt_stack.yaml.
            3. Wait for status COMPLETE.
            4. Run OSTF.

        Duration: 30 min
        """
        template_path = 'plugin_test/templates/nsxt_stack.yaml'

        self.show_step(1)  # Deploy cluster with NSX-t
        self.env.revert_snapshot("nsxt_ha_mode")

        # # On controller node create teststack with nsxt_stack.yaml
        self.show_step(2)
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        with open(template_path) as f:
            template = f.read()

        stack_id = os_conn.heat.stacks.create(
            stack_name='nsxt_stack',
            template=template,
            disable_rollback=True
        )['stack']['id']

        self.show_step(3)  # Wait for status COMPLETE
        try:
            wait(lambda:
                 os_conn.heat.stacks.get(stack_id).stack_status ==
                 'CREATE_COMPLETE', timeout=60 * 5)
        except TimeoutError:
            current_state = os_conn.heat.stacks.get(stack_id).stack_status
            assert_true(current_state == expect_state,
                        'Timeout is reached. Current state of stack '
                        'is {}'.format(current_state))

        self.show_step(4)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)
