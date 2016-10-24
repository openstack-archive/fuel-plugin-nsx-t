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

from fuelweb_test.helpers.decorators import log_snapshot_after_test
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.tests.base_test_case import SetupEnvironment
from tests.base_plugin_test import TestNSXtBase


@test(groups=['nsxt_plugin', 'nsxt_integration'])
class TestNSXtIntegration(TestNSXtBase):
    """Tests from test plan that have been marked as 'Automated'."""

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=['nsxt_ceilometer'])
    @log_snapshot_after_test
    def nsxt_ceilometer(self):
        """Check environment deployment with Fuel NSX-T plugin and Ceilometer.

        Scenario:
            1. Install NSX-T plugin to Fuel Master node with 5 slaves.
            2. Create new environment with the following parameters:
                * Compute: KVM/QEMU with vCenter
                * Networking: Neutron with NSX-T plugin
                * Storage: default
                * Additional services: Ceilometer
            3. Add nodes with the following roles:
                * Controller + Mongo
                * Controller + Mongo
                * Controller + Mongo
                * Compute-vmware
                * Compute
            4. Configure interfaces on nodes.
            5. Enable plugin and configure network settings.
            6. Configure VMware vCenter Settings.
               Add 2 vSphere clusters and configure Nova Compute instances on
               controllers and compute-vmware.
            7. Verify networks.
            8. Deploy cluster.
            9. Run OSTF.

        Duration: 180
        """
        # Install NSX-T plugin to Fuel Master node with 5 slaves
        self.show_step(1)
        self.env.revert_snapshot('ready_with_5_slaves')
        self.install_nsxt_plugin()

        self.show_step(2)  # Create new environment with Ceilometer
        settings = self.default.cluster_settings
        settings['ceilometer'] = True

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=settings)

        self.show_step(3)  # Add nodes
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-01': ['controller', 'mongo'],
                                    'slave-02': ['controller', 'mongo'],
                                    'slave-03': ['controller', 'mongo'],
                                    'slave-04': ['compute-vmware'],
                                    'slave-05': ['compute']})

        self.show_step(4)  # Configure interfaces on nodes
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(5)  # Enable plugin and configure network settings
        self.enable_plugin(cluster_id)

        # Configure VMware settings. 2 clusters, 2 Nova Compute instances:
        # 1 on controllers and 1 on compute-vmware
        self.show_step(6)
        target_node = self.fuel_web.get_nailgun_node_by_name('slave-04')
        self.fuel_web.vcenter_configure(cluster_id,
                                        target_node_2=target_node['hostname'],
                                        multiclusters=True)
        self.show_step(7)  # Verify networks
        self.fuel_web.verify_network(cluster_id)

        self.show_step(8)  # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(9)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id, timeout=3600,
                               test_sets=['smoke', 'sanity', 'ha',
                                                      'tests_platform'])

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=['nsxt_ceph'])
    @log_snapshot_after_test
    def nsxt_ceph(self):
        """Check environment deployment with Fuel NSX-T plugin and Ceph.

        Scenario:
            1. Install NSX-T plugin to Fuel Master node with 5 slaves.
            2. Create new environment with the following parameters:
                * Compute: KVM/QEMU with vCenter
                * Networking: Neutron with NSX-T plugin
                * Storage: Ceph
                * Additional services: default
            3. Add nodes with the following roles:
                * Controller
                * Ceph-OSD
                * Ceph-OSD
                * Ceph-OSD
                * Compute
            4. Configure interfaces on nodes.
            5. Enable plugin and configure network settings.
            6. Configure VMware vCenter Settings. Add 1 vSphere cluster and
               configure Nova Compute instance on controller.
            7. Verify networks.
            8. Deploy cluster.
            9. Run OSTF.

        Duration: 180
        """
        # Install NSX-T plugin to Fuel Master node with 5 slaves
        self.show_step(1)
        self.env.revert_snapshot('ready_with_5_slaves')
        self.install_nsxt_plugin()

        self.show_step(2)  # Create new environment with Ceph
        settings = self.default.cluster_settings
        settings['volumes_lvm'] = False
        settings['volumes_ceph'] = True
        settings['images_ceph'] = True
        settings['ephemeral_ceph'] = True
        settings['objects_ceph'] = True
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=settings)

        self.show_step(3)  # Add nodes
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-01': ['controller'],
                                    'slave-02': ['ceph-osd'],
                                    'slave-03': ['ceph-osd'],
                                    'slave-04': ['ceph-osd'],
                                    'slave-05': ['compute']})

        self.show_step(4)  # Configure interfaces on nodes
        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(5)  # Enable plugin and configure network settings
        self.enable_plugin(cluster_id)

        # Configure VMware settings. 1 cluster, 1 Compute instance: controller
        self.show_step(6)
        self.fuel_web.vcenter_configure(cluster_id)

        self.show_step(7)  # Verify networks
        self.fuel_web.verify_network(cluster_id)

        self.show_step(8)  # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(9)  # Run OSTF
        self.fuel_web.run_ostf(cluster_id)
