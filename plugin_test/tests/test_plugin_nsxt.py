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
from fuelweb_test.tests.base_test_case import TestBasic
from helpers import settings as pt_settings  # Plugin Tests Settings
from helpers import plugin


@test(groups=["plugins", "nsxt_plugin"])
class TestNSXtPlugin(TestBasic):
    """Tests from test plan that have been marked as 'Automated'."""

    _common = None

    def node_name(self, name_node):
        """Return name of node."""
        return self.fuel_web.get_nailgun_node_by_name(name_node)['hostname']

    def reconfigure_cluster_interfaces(self, cluster_id):
        # clear network mapping enp0s6 for all deployed nodes
        nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in nodes:
            self.fuel_web.update_node_networks(
                node['id'], pt_settings.assigned_networks)

    @test(depends_on=[SetupEnvironment.prepare_slaves_1],
          groups=["nsxt_smoke"])
    @log_snapshot_after_test
    def nsxt_smoke(self):
        """Deploy a cluster with NSXt Plugin.

        Scenario:
            1. Upload the plugin to master node.
            2. Create cluster.
            3. Provision one controller node.
            4. Configure NSXt for that cluster.
            5. Deploy cluster with plugin.
            6. Run 'smoke' OSTF.

        Duration 90 min

        """
        self.env.revert_snapshot('ready_with_1_slaves')
        self.show_step(1)
        plugin.install_nsxt_plugin(self.ssh_manager.admin_ip)

        self.show_step(2)
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=pt_settings.cluster_settings,
            configure_ssl=False)

        self.show_step(3)
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'], })

        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(4)
        plugin.enable_plugin(self.fuel_web, cluster_id)

        self.show_step(5)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(6)
        self.fuel_web.run_ostf(cluster_id=cluster_id, test_sets=['smoke'])

    @test(depends_on=[SetupEnvironment.prepare_slaves_1],
          groups=["nsxt_vcenter_smoke"])
    @log_snapshot_after_test
    def nsxt_vcenter_smoke(self):
        """Deploy a cluster with NSXt Plugin.

        Scenario:
            1. Upload the plugin to master node.
            2. Create cluster.
            3. Provision one controller node.
            4. Configure vcenter.
            5. Configure NSXt for that cluster.
            6. Deploy cluster with plugin.
            7. Run 'smoke' OSTF.

        Duration 90 min

        """
        self.env.revert_snapshot('ready_with_1_slaves')

        self.show_step(1)
        plugin.install_nsxt_plugin(self.ssh_manager.admin_ip)

        self.show_step(2)
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=pt_settings.cluster_settings,
            configure_ssl=False)

        self.show_step(3)
        self.fuel_web.update_nodes(cluster_id,
                                   {'slave-01': ['controller'], })

        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(4)
        self.fuel_web.vcenter_configure(cluster_id)

        self.show_step(5)
        plugin.enable_plugin(self.fuel_web, cluster_id)

        self.show_step(6)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(7)
        self.fuel_web.run_ostf(cluster_id=cluster_id, test_sets=['smoke'])

    @test(depends_on=[SetupEnvironment.prepare_slaves_9],
          groups=["nsxt_bvt"])
    @log_snapshot_after_test
    def nsxt_bvt(self):
        """Deploy cluster with plugin and vmware datastore backend.

        Scenario:
            1. Upload plugins to the master node.
            2. Create cluster with vcenter.
            3. Add 3 node with controller role, 3 ceph,
               compute-vmware + cinder-vmware, compute.
            4. Configure vcenter.
            5. Configure NSXt for that cluster.
            6. Deploy cluster.
            7. Run OSTF.

        Duration 3 hours

        """
        self.env.revert_snapshot("ready_with_9_slaves")

        self.show_step(1)
        plugin.install_nsxt_plugin(self.ssh_manager.admin_ip)

        self.show_step(2)
        settings = pt_settings.cluster_settings
        settings["images_ceph"] = True

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=settings,
            configure_ssl=False)

        self.show_step(3)
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['controller'],
             'slave-03': ['controller'],
             'slave-04': ['ceph-osd'],
             'slave-05': ['ceph-osd'],
             'slave-06': ['ceph-osd'],
             'slave-07': ['compute-vmware', 'cinder-vmware'],
             'slave-08': ['compute']}
        )

        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(4)
        target_node_1 = self.node_name('slave-07')
        self.fuel_web.vcenter_configure(cluster_id,
                                        multiclusters=True,
                                        target_node_1=target_node_1)
        self.show_step(5)
        plugin.enable_plugin(self.fuel_web, cluster_id)

        self.show_step(6)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(7)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity', 'ha'])
