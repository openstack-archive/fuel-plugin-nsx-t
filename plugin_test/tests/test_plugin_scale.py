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


@test(groups=["plugins", "nsxt_plugin", 'nsxt_scale'])
class TestNSXtScale(TestNSXtBase):
    """Tests from test plan that have been marked as 'Automated'."""

    @test(depends_on=[SetupEnvironment.prepare_slaves_9],
          groups=['nsxt_add_delete_controller'])
    @log_snapshot_after_test
    def nsxt_add_delete_controller(self):
        """Check functionality when controller has been removed or added.

        Scenario:
            1. Log in to the Fuel with preinstalled NSX-T plugin.
            2. Create a new environment with following parameters:
                * Compute: KVM/QEMU with vCenter
                * Networking: Neutron with NSX-T plugin
                * Storage: default
            3. Add nodes with following roles:
                * Controller
                * Controller
                * Controller
                * Controller
                * Cinder-vmware
                * Compute-vmware
            4. Configure interfaces on nodes.
            5. Configure network settings.
            6. Enable and configure NSX-T plugin.
            7. Configure VMware vCenter Settings. Add 2 vSphere clusters and
            configure Nova Compute instances on conrollers and compute-vmware.
            8. Deploy cluster.
            9. Run OSTF.
            10. Launch 1 KVM and 1 vcenter VMs.
            11. Remove node with controller role.
            12. Redeploy cluster.
            13. Check that all instances are in place.
            14. Run OSTF.
            15. Add controller.
            16. Redeploy cluster.
            17. Check that all instances are in place.
            18. Run OSTF.

        Duration: 180 min
        """
        self.env.revert_snapshot('ready_with_9_slaves')
        self.install_nsxt_plugin()

        self.show_step(1)
        self.show_step(2)
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=self.default.cluster_settings,
            configure_ssl=False)

        self.show_step(3)
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['controller'],
             'slave-03': ['controller'],
             'slave-04': ['controller'],
             'slave-05': ['cinder-vmware'],
             'slave-06': ['compute-vmware']}
        )
        self.show_step(4)
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(5)
        self.show_step(6)
        self.enable_plugin(cluster_id)

        self.show_step(7)
        target_node_2 = self.fuel_web.get_nailgun_node_by_name('slave-06')
        target_node_2 = target_node_2['hostname']
        self.fuel_web.vcenter_configure(cluster_id,
                                        target_node_2=target_node_2,
                                        multiclusters=True)

        self.show_step(8)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(9)
        self.fuel_web.run_ostf(cluster_id)

        self.show_step(10)
        os_ip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            os_ip, SERVTEST_USERNAME, SERVTEST_PASSWORD, SERVTEST_TENANT)

        os_help.create_instance(os_conn)
        os_help.create_instance(os_conn, az='vcenter')

        self.show_step(11)
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-02': ['controller']},
                                   False, True)

        self.show_step(12)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(13)
        os_help.check_instances_state(os_conn)

        self.show_step(14)
        self.fuel_web.run_ostf(cluster_id)

        self.show_step(15)
        self.fuel_web.update_nodes(cluster_id, {'slave-07': ['controller']})

        self.show_step(16)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(17)
        os_help.check_instances_state(os_conn)

        self.show_step(18)
        self.fuel_web.run_ostf(cluster_id)

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=['nsxt_add_delete_compute_node'])
    @log_snapshot_after_test
    def nsxt_add_delete_compute_node(self):
        """Verify functionality when compute node has been removed or added.

        Scenario:
            1. Connect to the Fuel web UI with preinstalled NSX-T plugin.
            2. Create a new environment with following parameters:
                * Compute: KVM/QEMU
                * Networking: Neutron with NSX-T plugin
                * Storage: default
                * Additional services: default
            3. Add nodes with following roles:
                * Controller
                * Controller
                * Controller
                * Compute
            4. Configure interfaces on nodes.
            5. Configure network settings.
            6. Enable and configure NSX-T plugin.
            7. Deploy cluster.
            8. Run OSTF.
            9. Launch KVM vm.
            10. Add node with compute role.
            11. Redeploy cluster.
            12. Check that all instances are in place.
            13. Run OSTF.
            14. Remove node with compute role from base installation.
            15. Redeploy cluster.
            16. Check that all instances are in place.
            17. Run OSTF.

        Duration: 180min
        """
        self.env.revert_snapshot('ready_with_5_slaves')
        self.install_nsxt_plugin()
        self.show_step(1)
        self.show_step(2)
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=self.default.cluster_settings,
            configure_ssl=False)

        self.show_step(3)
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['controller'],
             'slave-03': ['controller'],
             'slave-04': ['compute']}
        )
        self.show_step(4)
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(5)
        self.show_step(6)
        self.enable_plugin(cluster_id)

        self.show_step(7)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(8)
        self.fuel_web.run_ostf(cluster_id)

        self.show_step(9)
        os_ip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            os_ip, SERVTEST_USERNAME, SERVTEST_PASSWORD, SERVTEST_TENANT)

        os_help.create_instance(os_conn)

        self.show_step(10)
        self.fuel_web.update_nodes(cluster_id, {'slave-05': ['compute']})

        self.show_step(11)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(12)
        os_help.check_instances_state(os_conn)

        self.show_step(13)
        self.fuel_web.run_ostf(cluster_id)

        self.show_step(14)
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-04': ['compute']},
                                   False, True)
        self.show_step(15)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(16)
        os_help.check_instances_state(os_conn)

        self.show_step(17)
        self.fuel_web.run_ostf(cluster_id)

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=['nsxt_add_delete_compute_vmware_node'])
    @log_snapshot_after_test
    def nsxt_add_delete_compute_vmware_node(self):
        """Verify functionality when compute-vmware has been removed or added.

        Scenario:
            1. Connect to the Fuel web UI with preinstalled NSX-T plugin.
            2. Create a new environment with following parameters:
                * Compute: KVM/QEMU with vCenter
                * Networking: Neutron with NSX-T plugin
                * Storage: default
                * Additional services: default
            3. Add nodes with following roles:
                * Controller
                * Controller
                * Controller
                * Compute-vmware
            4. Configure interfaces on nodes.
            5. Configure network settings.
            6. Enable and configure NSX-T plugin.
            7. Configure VMware vCenter Settings. Add 1 vSphere cluster and
            configure Nova Compute instance on compute-vmware.
            8. Deploy cluster.
            9. Run OSTF.
            10. Launch vcenter vm.
            11. Remove node with compute-vmware role.
            12. Reconfigure vcenter compute clusters.
            13. Redeploy cluster.
            14. Check vm instance has been removed.
            15. Run OSTF.
            16. Add node with compute-vmware role.
            17. Reconfigure vcenter compute clusters.
            18. Redeploy cluster.
            19. Run OSTF.

        Duration: 240 min
        """

        self.env.revert_snapshot('ready_with_5_slaves')
        self.install_nsxt_plugin()
        self.show_step(1)
        self.show_step(2)
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=self.default.cluster_settings,
            configure_ssl=False)

        self.show_step(3)
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['controller'],
             'slave-03': ['controller'],
             'slave-04': ['compute-vmware']}
        )
        self.show_step(4)
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(5)
        self.show_step(6)
        self.enable_plugin(self.fuel_web, cluster_id)

        self.show_step(7)
        target_node = self.fuel_web.get_nailgun_node_by_name('slave-04')
        target_node = target_node['hostname']
        self.fuel_web.vcenter_configure(cluster_id, target_node_1=target_node)

        self.show_step(8)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(9)
        self.fuel_web.run_ostf(cluster_id)

        self.show_step(10)
        os_ip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            os_ip, SERVTEST_USERNAME, SERVTEST_PASSWORD, SERVTEST_TENANT)

        vcenter_vm = os_help.create_instance(os_conn, az='vcenter')

        self.show_step(11)
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-04': ['compute-vmware']},
                                   False, True)

        self.show_step(12)
        self.fuel_web.vcenter_configure(cluster_id)

        self.show_step(13)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(14)
        assert_true(os_conn.is_srv_deleted(vcenter_vm))

        self.show_step(15)
        self.fuel_web.run_ostf(cluster_id)

        self.show_step(16)
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-05': ['compute-vmware']})

        self.show_step(14)
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-04': ['compute']},
                                   False, True)
        self.show_step(15)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(16)
        self.fuel_web.vcenter_configure(cluster_id, target_node_1=target_node)

        self.show_step(17)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(18)
        self.fuel_web.run_ostf(cluster_id)
