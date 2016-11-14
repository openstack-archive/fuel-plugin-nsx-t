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

from fuelweb_test.helpers import os_actions
from fuelweb_test.helpers.decorators import log_snapshot_after_test
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.settings import SERVTEST_PASSWORD
from fuelweb_test.settings import SERVTEST_TENANT
from fuelweb_test.settings import SERVTEST_USERNAME
from fuelweb_test.tests.base_test_case import SetupEnvironment
from helpers import openstack as os_help
from tests.base_plugin_test import TestNSXtBase


@test(groups=['nsxt_plugin', 'nsxt_scale'])
class TestNSXtScale(TestNSXtBase):
    """Tests from test plan that have been marked as 'Automated'."""

    @test(depends_on=[SetupEnvironment.prepare_slaves_9],
          groups=['nsxt_add_delete_controller'])
    @log_snapshot_after_test
    def nsxt_add_delete_controller(self):
        """Check functionality when controller has been removed or added.

        Scenario:
            1. Install NSX-T plugin to Fuel Master node with 9 slaves.
            2. Create new environment with the following parameters:
                * Compute: KVM/QEMU with vCenter
                * Networking: Neutron with NSX-T plugin
                * Storage: default
            3. Add nodes with the following roles:
                * Controller
                * Compute
            4. Configure interfaces on nodes.
            5. Enable plugin and configure network settings.
            6. Configure VMware vCenter Settings. Add vSphere cluster and
               configure Nova Compute instance on conrollers.
            7. Deploy cluster.
            8. Run OSTF.
            9. Launch 1 vcenter instance and 1 KVM instance.
            10. Add 2 controller nodes.
            11. Redeploy cluster.
            12. Check that all instances are in place.
            13. Run OSTF.
            14. Remove 2 controller nodes.
            15. Redeploy cluster.
            16. Check that all instances are in place.
            17. Run OSTF.

        Duration: 180 min
        """
        # Install NSX-T plugin to Fuel Master node with 9 slaves
        self.show_step(1)
        self.env.revert_snapshot('ready_with_9_slaves')
        self.install_nsxt_plugin()

        self.show_step(2)  # Create new environment
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=self.default.cluster_settings,
            configure_ssl=False)

        self.show_step(3)  # Add nodes
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-01': ['controller'],
                                    'slave-04': ['compute']})

        self.show_step(4)  # Configure interfaces on nodes
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(5)  # Enable plugin and configure network settings
        self.enable_plugin(cluster_id)

        # Configure VMware settings. 1 cluster, 1 Nova Compute on controllers
        self.show_step(6)
        self.fuel_web.vcenter_configure(cluster_id)

        self.show_step(7)  # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(8)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)

        # Launch 1 vcenter instance and 1 KVM instance
        self.show_step(9)
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        os_help.create_instance(os_conn)
        os_help.create_instance(os_conn, az='vcenter')

        self.show_step(10)  # Add 2 controller nodes
        self.fuel_web.update_nodes(cluster_id, {'slave-02': ['controller'],
                                                'slave-03': ['controller']})
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(11)  # Redeploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(12)  # Check that all instances are in place
        os_help.check_instances_state(os_conn)

        self.show_step(13)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)

        self.show_step(14)  # Remove 2 controller nodes
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-01': ['controller'],
                                    'slave-02': ['controller']},
                                   False, True)

        self.show_step(15)  # Redeploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(16)  # Check that all instances are in place
        os_help.check_instances_state(os_conn)

        self.show_step(17)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=['nsxt_add_delete_compute_node'])
    @log_snapshot_after_test
    def nsxt_add_delete_compute_node(self):
        """Verify functionality when compute node has been removed or added.

        Scenario:
            1. Install NSX-T plugin to Fuel Master node with 5 slaves.
            2. Create new environment with the following parameters:
                * Compute: KVM/QEMU
                * Networking: Neutron with NSX-T plugin
                * Storage: default
                * Additional services: default
            3. Add nodes with the following roles:
                * Controller
                * Controller
                * Controller
                * Compute
            4. Configure interfaces on nodes.
            5. Enable plugin and configure network settings.
            6. Deploy cluster.
            7. Run OSTF.
            8. Launch KVM vm.
            9. Add node with compute role.
            10. Redeploy cluster.
            11. Check that instance is in place.
            12. Run OSTF.
            13. Remove node with compute role.
            14. Redeploy cluster.
            15. Check that instance is in place.
            16. Run OSTF.

        Duration: 180min
        """
        # Install NSX-T plugin to Fuel Master node with 5 slaves
        self.show_step(1)
        self.env.revert_snapshot('ready_with_5_slaves')
        self.install_nsxt_plugin()

        self.show_step(2)  # Create new environment
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

        self.show_step(5)  # Enable plugin and configure network settings
        self.enable_plugin(cluster_id)

        self.show_step(6)  # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(7)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)

        self.show_step(8)  # Launch KVM vm
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        os_help.create_instance(os_conn)

        self.show_step(9)  # Add node with compute role
        self.fuel_web.update_nodes(cluster_id, {'slave-05': ['compute']})
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(10)  # Redeploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(11)  # Check that instance is in place
        os_help.check_instances_state(os_conn)

        self.show_step(12)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)

        self.show_step(13)  # Remove node with compute role
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-04': ['compute']},
                                   False, True)

        self.show_step(14)  # Redeploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(15)  # Check that instance is in place
        os_help.check_instances_state(os_conn)

        self.show_step(16)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=['nsxt_add_delete_compute_vmware_node'])
    @log_snapshot_after_test
    def nsxt_add_delete_compute_vmware_node(self):
        """Verify functionality when compute-vmware has been removed or added.

        Scenario:
            1. Install NSX-T plugin to Fuel Master node with 5 slaves.
            2. Create new environment with the following parameters:
                * Compute: KVM/QEMU with vCenter
                * Networking: Neutron with NSX-T plugin
                * Storage: default
                * Additional services: default
            3. Add nodes with the following roles:
                * Controller
                * Controller
                * Controller
                * Compute-vmware
            4. Configure interfaces on nodes.
            5. Enable plugin and configure network settings.
            6. Configure VMware vCenter Settings. Add 1 vSphere cluster and
            configure Nova Compute instance on compute-vmware.
            7. Deploy cluster.
            8. Run OSTF.
            9. Launch vcenter vm.
            10. Add node with compute-vmware role.
            11. Reconfigure vcenter compute clusters.
            12. Redeploy cluster.
            13. Check that instance has been removed.
            14. Run OSTF.
            15. Remove node with compute-vmware role.
            16. Reconfigure vcenter compute clusters.
            17. Redeploy cluster.
            18. Run OSTF.

        Duration: 240 min
        """
        # Install NSX-T plugin to Fuel Master node with 5 slaves
        self.show_step(1)
        self.env.revert_snapshot('ready_with_5_slaves')
        self.install_nsxt_plugin()

        self.show_step(2)  # Create new environment
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
                                    'slave-04': ['compute-vmware']})

        self.show_step(4)  # Configure interfaces on nodes
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(5)  # Enable plugin and configure network settings
        self.enable_plugin(cluster_id)

        # Configure VMware settings. 1 cluster, 1 Nova Compute: compute-vmware
        self.show_step(6)
        target_node1 = self.fuel_web.get_nailgun_node_by_name('slave-04')
        self.fuel_web.vcenter_configure(cluster_id,
                                        target_node_1=target_node1['hostname'])

        self.show_step(7)  # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(8)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)

        self.show_step(9)  # Launch vcenter vm
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            SERVTEST_USERNAME,
            SERVTEST_PASSWORD,
            SERVTEST_TENANT)

        vcenter_vm = os_help.create_instance(os_conn, az='vcenter')

        self.show_step(10)  # Add node with compute-vmware role
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-05': ['compute-vmware']})
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(11)  # Reconfigure vcenter compute clusters
        target_node2 = self.fuel_web.get_nailgun_node_by_name('slave-05')
        self.fuel_web.vcenter_configure(cluster_id,
                                        target_node_1=target_node1['hostname'],
                                        target_node_2=target_node2['hostname'],
					multiclusters=True)

        self.show_step(12)  # Redeploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(13)  # Check that instance has been removed
        assert_true(os_conn.is_srv_deleted(vcenter_vm))

        self.show_step(14)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)

        self.show_step(15)  # Remove node with compute-vmware role
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-04': ['compute-vmware']},
                                   False, True)

        self.show_step(16)  # Reconfigure vcenter compute clusters
        target_node2 = self.fuel_web.get_nailgun_node_by_name('slave-04')
        self.fuel_web.vcenter_configure(cluster_id,
                                        target_node_1=target_node2['hostname'])

        self.show_step(17)    # Redeploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(18)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)
