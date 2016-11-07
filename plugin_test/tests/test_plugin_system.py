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
                * Compute-vmware
                * Compute
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
        sg = os_conn.create_sec_group_for_ssh().name
        vm1 = os_help.create_instance(os_conn, sg_names=[sg])
        vm2 = os_help.create_instance(os_conn, az='vcenter', sg_names=[sg])

        # Check that instances can communicate with each other
        self.show_step(4)
        default_net = os_conn.nova.networks.find(
            label=self.default.PRIVATE_NET)

        vm1_fip = os_conn.assign_floating_ip(vm1).ip
        vm2_fip = os_conn.assign_floating_ip(vm2).ip

        vm1_ip = os_conn.get_nova_instance_ip(vm1, net_name=default_net)
        vm2_ip = os_conn.get_nova_instance_ip(vm2, net_name=default_net)

        os_help.check_connection_vms({vm1_fip: [vm2_ip], vm2_fip: [vm1_ip]})

        self.show_step(5)  # Disable port attached to instance in nova az
        port = os_conn.neutron.list_ports(device_id=vm1.id)['ports'][0]['id']
        os_conn.neutron.update_port(port, {'port': {'admin_state_up': False}})

        # Check that instances can't communicate with each other
        self.show_step(6)
        os_help.check_connection_vms({vm2_fip: [vm1_ip]}, result_of_command=1)

        self.show_step(7)  # Enable port attached to instance in nova az
        os_conn.neutron.update_port(port, {'port': {'admin_state_up': True}})

        # Check that instances can communicate with each other
        self.show_step(8)
        os_help.check_connection_vms({vm1_fip: [vm2_ip], vm2_fip: [vm1_ip]})

        self.show_step(9)  # Disable port attached to instance in vcenter az
        port = os_conn.neutron.list_ports(device_id=vm2.id)['ports'][0]['id']
        os_conn.neutron.update_port(port, {'port': {'admin_state_up': False}})

        # Check that instances can't communicate with each other
        self.show_step(10)
        os_help.check_connection_vms({vm1_fip: [vm2_ip]}, result_of_command=1)

        self.show_step(11)  # Enable port attached to instance in vcenter az
        os_conn.neutron.update_port(port, {'port': {'admin_state_up': True}})

        # Check that instances can communicate with each other
        self.show_step(12)
        os_help.check_connection_vms({vm1_fip: [vm2_ip], vm2_fip: [vm1_ip]})

        self.show_step(13)  # Delete created instances
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
            5. Attach (add interface) net_01 to default router. Check that
               instances can't communicate with each other.
            6. Attach net_02 to default router.
            7. Check that instances can communicate with each other via router.
            8. Detach (delete interface) net_01 from default router.
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
        sg = os_conn.create_sec_group_for_ssh().name
        vm1 = os_help.create_instance(os_conn, net=net1, sg_names=[sg])
        vm2 = os_help.create_instance(os_conn, net=net2, sg_names=[sg],
                                      az='vcenter')

        vm1_ip = os_conn.get_nova_instance_ip(vm1, net_name=net1['name'])
        vm2_ip = os_conn.get_nova_instance_ip(vm2, net_name=net2['name'])

        # Attach (add interface) net_01 to default router. Check that
        # instances can't communicate with each other.
        self.show_step(5)
        router_id = os_conn.get_router(os_conn.get_network(
            self.default.ADMIN_NET))['id']

        os_conn.add_router_interface(router_id=router_id,
                                     subnet_id=subnet1['id'])
        vm1_fip = os_conn.assign_floating_ip(vm1).ip

        os_help.check_connection_vms({vm1_fip: [vm2_ip]},
                                     result_of_command=1)

        self.show_step(6)  # Attach net_02 to default router.
        os_conn.add_router_interface(router_id=router_id,
                                     subnet_id=subnet2['id'])
        vm2_fip = os_conn.assign_floating_ip(vm2).ip

        # Check that instances can communicate with each other via router
        self.show_step(7)
        os_help.check_connection_vms({vm2_fip: [vm1_ip]})

        # Detach (delete interface) net_01 from default router.
        self.show_step(8)
        vm1.remove_floating_ip(vm1_fip)
        os_help.remove_router_interface(os_conn, router_id, subnet1['id'])

        # Check that instances can't communicate with each other
        self.show_step(9)
        os_help.check_connection_vms({vm2_fip: [vm1_ip]}, result_of_command=1)

        self.show_step(10)  # Delete created instances
        vm2.remove_floating_ip(vm2_fip)
        os_help.remove_router_interface(os_conn, router_id, subnet2['id'])

        os_conn.delete_instance(vm1)
        os_conn.delete_instance(vm2)
        os_conn.verify_srv_deleted(vm1)
        os_conn.verify_srv_deleted(vm2)

        self.show_step(11)  # Delete created networks
        os_conn.neutron.delete_network(net1['id'])
        os_conn.neutron.delete_network(net2['id'])

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_public_network_availability'])
    @log_snapshot_after_test
    def nsxt_public_network_availability(self):
        """Check connectivity from VMs to public network.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Launch two instances in default network. Instances should belong
               to different az (nova and vcenter).
            4. Send ping from each instance to 8.8.8.8.

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

        # Launch two instances in default network. Instances should belong to
        # different az (nova and vcenter)
        self.show_step(3)
        sg = os_conn.create_sec_group_for_ssh().name
        vm1 = os_help.create_instance(os_conn, sg_names=[sg], az='vcenter')
        vm2 = os_help.create_instance(os_conn, sg_names=[sg])

        # Send ping from each instance to 8.8.8.8
        self.show_step(4)
        vm1_fip, vm2_fip = \
            os_help.create_and_assign_floating_ips(os_conn, [vm1, vm2])

        os_help.check_connection_vms({vm1_fip: ['8.8.8.8'],
                                      vm2_fip: ['8.8.8.8']})

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_connectivity_diff_networks'])
    @log_snapshot_after_test
    def nsxt_connectivity_diff_networks(self):
        """Check connection between VMs from different nets through the router.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Add two private networks (net01 and net02).
            4. Add one subnet  to each network
                 net01_subnet01: 192.168.101.0/24,
                 net02_subnet01, 192.168.102.0/24.
               Disable gateway for both subnets.
            5. Launch 1 instance in each network. Instances should belong to
               different az (nova and vcenter).
            6. Create new router (Router_01), set gateway and add interface
               to external network.
            7. Enable gateway on subnets. Attach private networks to created
               router.
            8. Verify that VMs of different networks communicate between
               each other.
            9. Add one more router (Router_02), set gateway and add interface
               to external network.
            10. Detach net_02 from Router_01 and attach it to Router_02.
            11. Assign floating IPs for all created VMs.
            12. Check that default security group allows the ICMP.
            13. Verify that VMs of different networks communicate between
                each other by FIPs.
            14. Delete instances.
            15. Detach created networks from routers.
            16. Delete created networks.
            17. Delete created routers.

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

        # Add one subnet to each network: net01_subnet01 (192.168.101.0/24) and
        # net02_subnet01 (192.168.102.0/24). Disable gateway for both subnets
        self.show_step(4)
        subnet1 = os_conn.create_subnet(
            subnet_name='net01_subnet01',
            network_id=net1['id'],
            cidr='192.168.101.0/24',
            allocation_pools=[
                {'start': '192.168.101.2','end': '192.168.101.254'}
            ],
            ip_version=4,
            gateway_ip=None)

        subnet2 = os_conn.create_subnet(
            subnet_name='net02_subnet01',
            network_id=net2['id'],
            cidr='192.168.102.0/24',
            allocation_pools=[
                {'start': '192.168.102.2', 'end': '192.168.102.254'}
            ],
            ip_version=4,
            gateway_ip=None)

        # Launch 1 instance in each network. Instances should belong to
        # different az (nova and vcenter)
        self.show_step(5)
        sg = os_conn.create_sec_group_for_ssh().name
        vm1 = os_help.create_instance(os_conn, net=net1, sg_names=[sg],
                                      az='vcenter')
        vm2 = os_help.create_instance(os_conn, net=net2, sg_names=[sg])

        # Create new router (Router_01), set gateway and add interface to
        # external network
        self.show_step(6)
        tenant = os_conn.get_tenant(SERVTEST_TENANT)
        rout1 = os_conn.create_router('Router_01', tenant)

        # Enable gateway on subnets. Attach private networks to created router
        self.show_step(7)
        os_help.add_gateway_ip(os_conn, subnet1['id'], '192.168.101.1')
        os_conn.add_router_interface(router_id=rout1['id'],
                                     subnet_id=subnet1['id'])

        os_help.add_gateway_ip(os_conn, subnet2['id'], '192.168.102.1')
        os_conn.add_router_interface(router_id=rout1['id'],
                                     subnet_id=subnet2['id'])

        # Verify that VMs of different networks communicate between each other
        self.show_step(8)
        vm1_ip = os_conn.get_nova_instance_ip(vm1, net_name=net1['name'])
        vm2_ip = os_conn.get_nova_instance_ip(vm2, net_name=net2['name'])

        vm1_fip, vm2_fip = \
            os_help.create_and_assign_floating_ips(os_conn, [vm1, vm2])

        os_help.check_connection_vms({vm1_fip: [vm2_ip], vm2_fip: [vm1_ip]})

        # Add one more router (Router_02), set gateway and add interface
        # to external network
        self.show_step(9)
        rout2 = os_conn.create_router('Router_02', tenant)

        # Detach net_02 from Router_01 and attach it to Router_02
        self.show_step(10)
        vm2.remove_floating_ip(vm2_fip)
        os_help.remove_router_interface(os_conn, rout1['id'], subnet2['id'])
        os_conn.add_router_interface(router_id=rout2['id'],
                                     subnet_id=subnet2['id'])

        self.show_step(11)  # Assign floating IPs for all created VMs
        vm2_fip = os_help.create_and_assign_floating_ips(os_conn, [vm2])[0]

        self.show_step(12)  # Check that default security group allow the ICMP

        # Verify that VMs of different networks communicate between each
        # other by FIPs
        self.show_step(13)
        os_help.check_connection_vms({vm1_fip: [vm2_fip], vm2_fip: [vm1_fip]})

        self.show_step(14)  # Delete instances
        vm1.remove_floating_ip(vm1_fip)
        vm2.remove_floating_ip(vm2_fip)
        os_conn.delete_instance(vm1)
        os_conn.delete_instance(vm2)

        self.show_step(15)  # Detach created networks from routers
        os_help.remove_router_interface(os_conn, rout1['id'], subnet1['id'])
        os_help.remove_router_interface(os_conn, rout2['id'], subnet2['id'])

        os_conn.verify_srv_deleted(vm2)
        os_conn.verify_srv_deleted(vm1)

        self.show_step(16)  # Delete created networks
        os_conn.neutron.delete_network(net1['id'])
        os_conn.neutron.delete_network(net2['id'])

        self.show_step(17)  # Delete created routers
        os_conn.neutron.delete_router(rout1['id'])
        os_conn.neutron.delete_router(rout2['id'])

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
        # self.env.revert_snapshot('nsxt_setup_system')

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
        sg = os_conn.create_sec_group_for_ssh().name
        net_name = self.default.PRIVATE_NET
        net = os_conn.get_network(net_name)
        flavors = os_conn.nova.flavors.list()
        micro_flavor = [f for f in flavors if f.name == 'm1.micro'][0]

        image = os_conn.get_image(os_help.zone_image_maps['vcenter'])
        os_conn.nova.servers.create(
            name='VM_1',
            image=image,
            flavor=micro_flavor,
            min_count=5,
            availability_zone='vcenter',
            nics=[{'net-id': net['id']}],
            security_groups=[sg])
        os_help.verify_instance_state(os_conn)

        # Launch 5 instances VM_2 simultaneously. Image TestVM,
        # flavor: m1.tiny, az: nova, net: default
        self.show_step(4)
        image = os_conn.get_image(os_help.zone_image_maps['nova'])
        os_conn.nova.servers.create(
            name='VM_2',
            image=image,
            flavor=micro_flavor,
            min_count=5,
            availability_zone='nova',
            nics=[{'net-id': net['id']}],
            security_groups=[sg])
        os_help.verify_instance_state(os_conn)

        self.show_step(5)  # Check connection between VMs (ping, ssh)
        instances = os_conn.nova.servers.list()
        fips = os_help.create_and_assign_floating_ips(os_conn, instances)

        ips = [os_conn.get_nova_instance_ip(i, net_name=net_name)
               for i in instances]

        os_help.check_connection_vms({fip: ips for fip in fips})
        os_help.ping_each_other(fips)

        self.show_step(6)  # Delete all VMs simultaneously
        for instance in instances:
            instance.delete()
        for instance in instances:
            os_conn.verify_srv_deleted(instance)

    @test(depends_on=[nsxt_setup_system],
          groups=['nsxt_batch_instance_creation'])
    @log_snapshot_after_test
    def nsxt_batch_instance_creation(self):
        """Check instance creation in the one group simultaneously.

        Scenario:
            1. Set up for system tests.
            2. Get access to OpenStack.
            3. Launch 5 instances VM_1 simultaneously in vcenter az in
               default net. Verify that creation was successful.
            4. Launch 5 instances VM_2 simultaneously in nova az in default
               net. Verify that creation was successful.
            5. Delete all VMs simultaneously.

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

        # Launch 5 instances VM_1 simultaneously in vcenter az in default
        # net. Verify that creation was successful
        self.show_step(3)
        net_name = self.default.PRIVATE_NET
        net = os_conn.get_network(net_name)
        flavors = os_conn.nova.flavors.list()
        micro_flavor = [f for f in flavors if f.name == 'm1.micro'][0]

        image = os_conn.get_image(os_help.zone_image_maps['vcenter'])
        os_conn.nova.servers.create(
            name='VM_1',
            image=image,
            flavor=micro_flavor,
            min_count=5,
            availability_zone='vcenter',
            nics=[{'net-id': net['id']}])
        os_help.verify_instance_state(os_conn)

        # Launch 5 instances VM_2 simultaneously in nova az in default net.
        # Verify that creation was successful
        self.show_step(4)
        image = os_conn.get_image(os_help.zone_image_maps['nova'])
        os_conn.nova.servers.create(
            name='VM_2',
            image=image,
            flavor=micro_flavor,
            min_count=5,
            availability_zone='nova',
            nics=[{'net-id': net['id']}])
        os_help.verify_instance_state(os_conn)

        self.show_step(5)  # Delete all VMs simultaneously
        instances = os_conn.nova.servers.list()
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
