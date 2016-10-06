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
          groups=['nsxt_setup_system'])
    @log_snapshot_after_test
    def nsxt_setup_system(self):
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
            6. Configure VMware vCenter Settings. Add 2 vSphere clusters,
               configure Nova Compute instances on controller and
               compute-vmware.
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
                                    'slave-02': ['compute-vmware'],
                                    'slave-03': ['compute'],
                                    'slave-04': ['compute']})

        self.show_step(4)  # Configure interfaces on nodes
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(5)  # Enable and configure plugin, configure networks
        self.enable_plugin(cluster_id)

        # Configure VMware settings. 2 Cluster, 1 Nova Instance on controllers
        # and 1 Nova Instance on compute-vmware
        self.show_step(6)
        target_node2 = self.fuel_web.get_nailgun_node_by_name('slave-02')
        self.fuel_web.vcenter_configure(cluster_id,
                                        target_node_2=target_node2['hostname'],
                                        multiclusters=True)

        self.show_step(7)  # Verify networks
        self.fuel_web.verify_network(cluster_id)

        self.show_step(8)  # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(9)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)

        self.env.make_snapshot("nsxt_setup_system", is_make=True)

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_manage_ports'])
    @log_snapshot_after_test
    def nsxt_manage_ports(self):
        """Check ability to bind port on NSX to VM, disable and enable it.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Launch two instances in default network. Instances should belong
               to different az (nova and vcenter).
            4. Check that instances can communicate with each other.
            5. Disable port attached to instance in nova az.
            6. Check that instances can't communicate with each other.
            7. Enable port attached to instance in nova az.
            8. Check that instances can communicate with each other.
            9. Disable port attached to instance in vcenter az.
            10. Check that instances can't communicate with each other.
            11. Enable port attached to instance in vcenter az.
            12. Check that instances can communicate with each other.
            13. Delete created instances.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_setup_system')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()

        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        # Launch two instances in default network. Instances should belong to
        # different az (nova and vcenter)
        self.show_step(3)
        vm1 = os_help.create_instance(os_conn)
        vm2 = os_help.create_instance(os_conn, az='vcenter')

        # Check that instances can communicate with each other
        self.show_step(4)
        default_net = os_conn.nova.networks.find(
            label=self.default.PRIVATE_NET)
        _, access_point_ip = os_help.create_access_point(
            os_conn=os_conn, nics=[{'net-id': default_net.id}],
            security_groups=['default'])

        vm1_fip = os_conn.assign_floating_ip(vm1)
        vm2_fip = os_conn.assign_floating_ip(vm2)

        os_help.ping_each_other(ips=[vm1_fip, vm2_fip],
                                access_point_ip=access_point_ip)

        # Disable port attached to instance in nova az
        self.show_step(5)
        vm1_ip = os_conn.get_nova_instance_ip(
            vm1, net_name=self.default.PRIVATE_NET)
        ports = os_conn.neutron.list_ports(retrieve_all=True,
                                           network_id=default_net.id,
                                           ip_address=vm1_ip)
        os_conn.neutron.update_port(ports[0], body={'admin_state_up': False})

        # Check that instances can't communicate with each other
        self.show_step(6)
        os_help.ping_each_other(ips=[vm1_fip, vm2_fip],
                                access_point_ip=access_point_ip,
                                expected_ec=1)

        # Enable port attached to instance in nova az
        self.show_step(7)
        os_conn.neutron.update_port(ports[0], body={'admin_state_up': True})

        # Check that instances can communicate with each other
        self.show_step(8)
        os_help.ping_each_other(ips=[vm1_fip, vm2_fip],
                                access_point_ip=access_point_ip)

        # Disable port attached to instance in vcenter az
        self.show_step(9)
        vm2_ip = os_conn.get_nova_instance_ip(
            vm2, net_name=self.default.PRIVATE_NET)
        ports = os_conn.neutron.list_ports(retrieve_all=True,
                                           network_id=default_net.id,
                                           ip_address=vm2_ip)
        os_conn.neutron.update_port(ports[0], body={'admin_state_up': False})

        # Check that instances can't communicate with each other
        self.show_step(10)
        os_help.ping_each_other(ips=[vm1_fip, vm2_fip],
                                access_point_ip=access_point_ip,
                                expected_ec=1)

        # Enable port attached to instance in vcenter az
        self.show_step(11)
        os_conn.neutron.update_port(ports[0], body={'admin_state_up': True})

        # Check that instances can communicate with each other
        self.show_step(12)
        os_help.ping_each_other(ips=[vm1_fip, vm2_fip],
                                access_point_ip=access_point_ip)

        # Delete created instances
        self.show_step(13)
        vm1.delete()
        vm2.delete()

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_manage_networks'])
    @log_snapshot_after_test
    def nsxt_manage_networks(self):
        """Check abilities to create and terminate networks on NSX.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Create private networks net_01 and net_02 with subnets.
            4. Launch 1 instance on each network. Instances should belong to
               different az (nova and vcenter).
            5. Check that instances can't communicate with each other.
            6. Attach (add interface) both networks to default router.
            7. Check that instances can communicate with each other via router.
            8. Detach (delete interface) both networks from default router.
            9. Check that instances can't communicate with each other.
            10. Delete created instances.
            11. Delete created networks.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_setup_system')

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
        subnet1 = os_conn.create_subnet(subnet_name=net1['name'],
                                        network_id=net1['id'],
                                        cidr='192.168.1.0/24',
                                        ip_version=4)

        net2 = self._create_net(os_conn, 'net_02')
        subnet2 = os_conn.create_subnet(subnet_name=net2['name'],
                                        network_id=net2['id'],
                                        cidr='192.168.2.0/24',
                                        ip_version=4)

        # Launch 2 instances on each network. Instances should belong to
        # different az (nova and vcenter)
        self.show_step(4)
        vm1 = os_help.create_instance(os_conn, net=net1)
        vm2 = os_help.create_instance(os_conn, net=net2, az='vcenter')

        # Check that instances can't communicate with each other
        self.show_step(5)
        _, access_point_ip = os_help.create_access_point(
            os_conn=os_conn, nics=[{'net-id': net1.id}, {'net-id': net2.id}],
            security_groups=['default'])

        vm1_fip = os_conn.assign_floating_ip(vm1)
        vm2_fip = os_conn.assign_floating_ip(vm2)

        os_help.ping_each_other(ips=[vm1_fip, vm2_fip],
                                access_point_ip=access_point_ip,
                                expected_ec=1)

        # Attach (add interface) both networks to default router
        self.show_step(6)
        router_id = os_conn.get_router(os_conn.get_network(
            self.default.ADMIN_NET))['id']

        os_conn.add_router_interface(router_id=router_id,
                                     subnet_id=subnet1['id'])
        os_conn.add_router_interface(router_id=router_id['id'],
                                     subnet_id=subnet2['id'])

        # Check that instances can communicate with each other via router
        self.show_step(7)
        os_help.ping_each_other(ips=[vm1_fip, vm2_fip],
                                access_point_ip=access_point_ip)

        # Detach (delete interface) both networks from default router
        self.show_step(8)
        os_conn.neutron.remove_interface_router(
            router_id, {"router_id": router_id, "subnet_id": subnet1['id']})
        os_conn.neutron.remove_interface_router(
            router_id, {"router_id": router_id, "subnet_id": subnet2['id']})

        # Check that instances can't communicate with each other
        self.show_step(9)
        os_help.ping_each_other(ips=[vm1_fip, vm2_fip],
                                access_point_ip=access_point_ip,
                                expected_ec=1)

        self.show_step(10)  # Delete created instances
        os_conn.delete_instance(vm1)
        os_conn.delete_instance(vm2)
        os_conn.verify_srv_deleted(vm1)
        os_conn.verify_srv_deleted(vm2)

        self.show_step(11)  # Delete created networks
        os_conn.nova.delete_network(net1['name'])
        os_conn.nova.delete_network(net2['name'])

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_multiple_vnics'])
    @log_snapshot_after_test
    def nsxt_multiple_vnics(self):
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
        self.env.revert_snapshot('nsxt_setup_system')

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

    @test(depends_on=[nsxt_setup_system],
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
        self.env.revert_snapshot('nsxt_setup_system')

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

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_different_tenants'])
    @log_snapshot_after_test
    def nsxt_different_tenants(self):
        """Check isolation between VMs in different tenants.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Create new tenant with new user.
            4. In new tenant create network with subnet.
            5. In new tenant create router, set gateway and add interface.
            6. In new tenant launch instance and associate floating ip with vm.
            7. Launch instance in default network and associate floating ip
               with vm.
            8. Check that default security group allow ingress icmp traffic.
            9. Send icmp ping between instances in different tenants via
               floating ip.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_setup_system')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()

        os_ip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            os_ip, SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        self.show_step(3)  # Create new tenant with new user
        os_conn.create_user_and_tenant('test_tenant', 'test', 'test')
        os_help.add_role_to_user(os_conn, 'test', 'admin', 'test_tenant')

        os_conn_test = os_actions.OpenStackActions(os_ip, 'test', 'test',
                                                   'test_tenant')

        self.show_step(4)  # In new tenant create network with subnet
        net1 = self._create_net(os_conn_test, 'net_01')
        subnet1 = os_conn_test.create_subnet(
            subnet_name=net1['name'],
            network_id=net1['id'],
            cidr='192.168.1.0/24',
            ip_version=4,
            gateway_ip=None)

        # In new tenant create router, set gateway and add interface
        self.show_step(5)
        test_tenant = os_conn_test.get_tenant('test_tenant')
        router = os_conn_test.create_router('test_router', test_tenant)
        os_conn.add_router_interface(router_id=router["id"],
                                     subnet_id=subnet1["id"])

        # In new tenant launch instance and associate floating ip with vm
        self.show_step(6)
        vm1 = os_help.create_instance(os_conn_test)
        vm1_fip = os_conn_test.assign_floating_ip(vm1).ip

        # Launch instance in default network and associate floating ip with vm
        self.show_step(7)
        vm2 = os_help.create_instance(os_conn, az='vcenter')
        vm2_fip = os_conn.assign_floating_ip(vm2).ip

        # Check that default security group allow ingress icmp traffic
        self.show_step(8)
        # Send icmp ping between instances in different tenants via floating ip
        self.show_step(9)
        default_net = os_conn.nova.networks.find(
            label=self.default.PRIVATE_NET)
        _, access_point_ip = os_help.create_access_point(
            os_conn=os_conn, nics=[{'net-id': default_net.id}],
            security_groups=['default'])
        os_help.ping_each_other(ips=[vm1_fip, vm2_fip],
                                access_point_ip=access_point_ip)

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_same_ip_different_tenants'])
    @log_snapshot_after_test
    def nsxt_same_ip_different_tenants(self):
        """Check connectivity between VMs with same ip in different tenants.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Create 2 non-admin tenants 'test_1' and 'test_2' with common
               admin user.
            4. In tenant 'test_1' create network 'net1' and subnet 'subnet1'
               with CIDR 10.0.0.0/24.
            5. In tenant 'test_1' create router 'router1' and attach 'net1'
               to it.
            6. In tenant 'test_1' create security group 'SG_1' and add rule
               that allows ingress icmp traffic.
            7. In tenant 'test_1' launch two instances (VM_1 and VM_2) in
               created network with created security group. Instances should
               belong to different az (nova and vcenter).
            8. Assign floating IPs for created VMs.
            9. In tenant 'test_2' create network 'net2' and subnet 'subnet2'
               with CIDR 10.0.0.0/24.
            10. In tenant 'test_2' create router 'router2' and attach 'net2'
                to it.
            11. In tenant 'test_2' create security group 'SG_2' and add rule
                that allows ingress icmp traffic.
            12. In tenant 'test_2' launch two instances (VM_3 and VM_4) in
                created network with created security group. Instances should
                belong to different az (nova and vcenter).
            13. Assign floating IPs for created VMs.
            14. Verify that VMs with same ip on different tenants communicate
                between each other by FIPs. Send icmp ping from VM_1 to VM_3,
                VM_2 to VM_4 and vice versa.

        Duration: 30 min
        """
        icmp_rule = {
            'ip_protocol': 'icmp',
            'from_port': -1,
            'to_port': -1,
            'cidr': '0.0.0.0/0',
        }

        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_setup_system')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()

        os_ip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            os_ip, SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        # Create 2 non-admin tenants 'test_1' and 'test_2' with common
        # admin user
        self.show_step(3)
        os_conn.create_tenant('test_1')
        os_conn.create_tenant('test_2')

        os_conn1 = os_actions.OpenStackActions(os_ip, 'admin',
                                               'admin', 'test_1')
        os_conn2 = os_actions.OpenStackActions(os_ip, 'admin',
                                               'admin', 'test_2')

        test1_tenant = os_conn1.get_tenant('test_1')
        test2_tenant = os_conn2.get_tenant('test_2')

        # In tenant 'test_1' create network 'net1' and subnet 'subnet1' with
        # CIDR 10.0.0.0/24
        self.show_step(4)
        net1 = self._create_net(os_conn1, 'net01')
        subnet1 = os_conn1.create_subnet(
            subnet_name='subnet1',
            network_id=net1['id'],
            cidr='10.0.0.0/24')

        # In tenant 'test_1' create router 'router1' and attach 'net1' to it
        self.show_step(5)
        router1 = os_conn1.create_router('router1', test1_tenant)
        os_conn1.add_router_interface(router_id=router1["id"],
                                      subnet_id=subnet1["id"])

        # In tenant 'test_1' create security group 'SG_1' and add rule that
        # allows ingress icmp traffic
        self.show_step(6)
        sg1 = os_conn1.nova.security_groups.create('SG_1', 'descr')
        os_conn1.nova.security_group_rules.create(sg1.id, **icmp_rule)

        # In tenant 'test_1' launch two instances (VM_1 and VM_2) in created
        # network with created security group. Instances should belong to
        # different az
        self.show_step(7)
        vm1 = os_help.create_instance(os_conn1, net=net1, sg_names=['SG_1'])
        vm2 = os_help.create_instance(os_conn1, net=net1, sg_names=['SG_1'],
                                      az='vcenter')

        self.show_step(8)  # Assign floating IPs for created VMs
        default_net = os_conn.nova.networks.find(
            label=self.default.PRIVATE_NET)
        _, access_point_ip = os_help.create_access_point(
            os_conn=os_conn, nics=[{'net-id': default_net.id}],
            security_groups=['default'])

        vm1_fip = os_conn1.assign_floating_ip(vm1).ip
        vm2_fip = os_conn1.assign_floating_ip(vm2).ip

        # In tenant 'test_2' create network 'net2' and subnet 'subnet2' with
        # CIDR 10.0.0.0/24
        self.show_step(9)
        net2 = self._create_net(os_conn2, 'net02')
        subnet2 = os_conn2.create_subnet(
            subnet_name='subnet2',
            network_id=net1['id'],
            cidr='10.0.0.0/24')

        # In tenant 'test_2' create router 'router2' and attach 'net2' to it
        self.show_step(10)
        router2 = os_conn2.create_router('router2', test2_tenant)
        os_conn2.add_router_interface(router_id=router2["id"],
                                      subnet_id=subnet2["id"])

        # In tenant 'test_2' create security group 'SG_2' and add rule that
        # allows ingress icmp traffic
        self.show_step(11)
        sg2 = os_conn2.nova.security_groups.create('SG_2', 'descr')
        os_conn2.nova.security_group_rules.create(sg2.id, **icmp_rule)

        # In tenant 'test_2' launch two instances (VM_3 and VM_4) in created
        # network with created security group. Instances should belong to
        # different az
        self.show_step(12)
        vm3 = os_help.create_instance(os_conn2, net=net2, sg_names=['SG_2'])
        vm4 = os_help.create_instance(os_conn2, net=net2, sg_names=['SG_2'],
                                      az='vcenter')

        self.show_step(13)  # Assign floating IPs for created VMs
        vm3_fip = os_conn1.assign_floating_ip(vm3).ip
        vm4_fip = os_conn1.assign_floating_ip(vm4).ip

        # Verify that VMs with same ip on different tenants communicate
        # between each other by FIPs. Send icmp ping from VM_1 to VM_3,
        # VM_2 to VM_4 and vice versa
        self.show_step(14)
        pair1, pair2 = [vm1_fip, vm3_fip], [vm2_fip, vm4_fip]

        os_help.ping_each_other(ips=pair1, access_point_ip=access_point_ip)
        os_help.ping_each_other(ips=pair2, access_point_ip=access_point_ip)

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_public_network_availability'])
    @log_snapshot_after_test
    def nsxt_public_network_availability(self):
        """Check connectivity from VMs to public network.

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
        self.env.revert_snapshot('nsxt_setup_system')

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

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_manage_secgroups'])
    @log_snapshot_after_test
    def nsxt_manage_secgroups(self):
        """Check ability to create and delete security group.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Create new security group with default rules.
            4. Add ingress rule for ICMP protocol.
            5. Launch two instances in default network. Instances should
               belong to different az (nova and vcenter).
            6. Attach created security group to instances.
            7. Check that instances can ping each other.
            8. Delete ingress rule for ICMP protocol.
            9. Check that instances can't ping each other.
            10. Delete instances.
            11. Delete security group.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_setup_system')

        self.show_step(2)  # Get access to OpenStack
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        # Create new security group with default rules.
        self.show_step(3)
        sg1 = os_conn.nova.security_groups.create('SG_1', 'descr')

        # Add ingress rule for ICMP protocol.
        self.show_step(4)
        icmp_rule = {
            'ip_protocol': 'icmp',
            'from_port': -1,
            'to_port': -1,
            'cidr': '0.0.0.0/0',
        }
        sg1_rule = os_conn.nova.security_group_rules.create(sg1.id,
                                                            **icmp_rule)

        # Launch two instances in default network. Instances should belong to
        # different az (nova and vcenter)
        self.show_step(5)
        vm1 = os_help.create_instance(os_conn)
        vm2 = os_help.create_instance(os_conn, az='vcenter')

        # Attach created security group to instances
        self.show_step(6)
        os_conn.nova.servers.add_security_group(vm1, 'SG_1')
        os_conn.nova.servers.add_security_group(vm2, 'SG_1')

        # Check that instances can ping each other
        self.show_step(7)
        default_net = os_conn.nova.networks.find(
            label=self.default.PRIVATE_NET)
        _, access_point_ip = os_help.create_access_point(
            os_conn=os_conn, nics=[{'net-id': default_net.id}],
            security_groups=['default'])

        vm1_fip = os_conn.assign_floating_ip(vm1).ip
        vm2_fip = os_conn.assign_floating_ip(vm2).ip

        os_help.ping_each_other(ips=[vm1_fip, vm2_fip],
                                access_point_ip=access_point_ip)

        # Delete ingress rule for ICMP protocol
        self.show_step(8)
        os_conn.nova.security_group_rules.delete(sg1.id, sg1_rule)

        # Check that instances can't ping each other
        self.show_step(9)
        os_help.ping_each_other(ips=[vm1_fip, vm2_fip],
                                access_point_ip=access_point_ip,
                                expected_ec=1)

        # Delete instances
        self.show_step(10)
        os_conn.delete_instance(vm1)
        os_conn.delete_instance(vm2)
        os_conn.verify_srv_deleted(vm1)
        os_conn.verify_srv_deleted(vm2)

        # Delete security group
        self.show_step(11)
        os_conn.nova.security_groups.delete(sg1)

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_manage_compute_hosts'])
    @log_snapshot_after_test
    def nsxt_manage_compute_hosts(self):
        """Verify that instances could be launched on enabled compute host.

        Scenario:
            1. Set up for system tests.
            2. Disable one of compute host in each availability zone
               (vcenter and nova).
            3. Create several instances in both az.
            4. Check that instances were created on enabled compute hosts.
            5. Disable second compute host and enable first one in each
               availability zone (vcenter and nova).
            6. Create several instances in both az.
            7. Check that instances were created on enabled compute hosts.

        Duration: 30 min
        """
        self.show_step(1)  # Set up for system tests
        self.env.revert_snapshot('nsxt_setup_system')

        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        # Disable one of compute host in each availability zone
        self.show_step(2)
        services = os_conn.nova.services.list(binary='nova-compute')
        disabled_services = [
            [srv for srv in services if srv.zone == 'vcenter'].pop(),
            [srv for srv in services if srv.zone == 'nova'].pop()
        ]
        for service in disabled_services:
            os_conn.disable_nova_service(service)

        self.show_step(3)  # Create several instances in both az
        instances = []
        for i in range(2):
            instances.append(os_help.create_instance(os_conn, az='vcenter'))
            os_help.create_instance(os_conn)

        # Check that instances were created on enabled compute hosts
        self.show_step(4)
        vmware_hosts = [srv.host for srv in disabled_services]
        for inst in instances:
            inst_host = getattr(inst, 'OS-EXT-SRV-ATTR:host')
            assert_true(inst_host not in vmware_hosts,
                        'Instance was launched on disabled cluster')
        for i in instances:
            i.delete()
        instances = []

        # Disable second compute host and enable first one in each
        # availability zone (vcenter and nova)
        self.show_step(5)
        for service in services:
            if service in disabled_services:
                os_conn.enable_nova_service(service)
            else:
                os_conn.disable_nova_service(service)

        self.show_step(6)  # Create several instances in both az
        for i in range(2):
            instances.append(os_help.create_instance(os_conn, az='vcenter'))
            os_help.create_instance(os_conn)

        # Check that instances were created on enabled compute hosts
        self.show_step(7)
        for inst in instances:
            inst_host = getattr(inst, 'OS-EXT-SRV-ATTR:host')
            assert_true(inst_host in vmware_hosts,
                        'Instance was launched on disabled cluster')

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_batch_instance_creation'])
    @log_snapshot_after_test
    def nsxt_batch_instance_creation(self):
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
        self.env.revert_snapshot('nsxt_setup_system')

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
        net = os_conn.get_network(self.default.PRIVATE_NET)

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
        for instance in instances:
            instance.delete()
        for instance in instances:
            os_conn.verify_srv_deleted(instance)

    @test(depends_on=[nsxt_setup_system],
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
        template_path = 'plugin_test/test_templates/nsxt_stack.yaml'

        self.show_step(1)  # Deploy cluster with NSX-t
        self.env.revert_snapshot("nsxt_setup_system")

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
        expect_state = 'CREATE_COMPLETE'
        try:
            wait(lambda:
                 os_conn.heat.stacks.get(stack_id).stack_status ==
                 expect_state, timeout=60 * 5)
        except TimeoutError:
            current_state = os_conn.heat.stacks.get(stack_id).stack_status
            assert_true(current_state == expect_state,
                        'Timeout is reached. Current state of stack '
                        'is {}'.format(current_state))

        self.show_step(4)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)
