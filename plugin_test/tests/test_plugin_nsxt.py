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

from fuelweb_test.helpers.decorators import log_snapshot_after_test
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.tests.base_test_case import SetupEnvironment
from tests.base_plugin_test import TestNSXtBase


@test(groups=["plugins", "nsxt_plugin", 'nsxt_smoke_scenarios'])
class TestNSXtSmoke(TestNSXtBase):
    """Tests from test plan that have been marked as 'Automated'."""

    @test(depends_on=[SetupEnvironment.prepare_slaves_1],
          groups=["nsxt_install", 'nsxt_smoke'])
    @log_snapshot_after_test
    def nsxt_install(self):
        """Check that plugin can be installed.

        Scenario:
            1. Connect to the Fuel master node via ssh.
            2. Upload NSX-T plugin.
            3. Install NSX-T plugin.
            4. Run command 'fuel plugins'.
            5. Check name, version and package version of plugin.

        Duration 30 min

        """
        self.env.revert_snapshot('ready_with_1_slaves')

        self.show_step(1)
        self.show_step(2)
        self.show_step(3)
        self.install_nsxt_plugin()

        self.show_step(4)
        output = self.ssh_manager.execute_on_remote(
            ip=self.ssh_manager.admin_ip, cmd='fuel plugins list'
        )['stdout'].pop().split(' ')

        self.show_step(5)
        msg = "Plugin '{0}' is not installed.".format(self.default.PLUGIN_NAME)
        # check name
        assert_true(self.default.PLUGIN_NAME in output, msg)
        # check version
        assert_true(self.default.NSXT_PLUGIN_VERSION in output, msg)

        self.env.make_snapshot("nsxt_install", is_make=True)

    @test(depends_on=[nsxt_install],
          groups=["nsxt_uninstall", 'nsxt_smoke'])
    @log_snapshot_after_test
    def nsxt_uninstall(self):
        """Check that NSX-T plugin can be removed.

        Scenario:
            1. Revert to snapshot nsxt_install
            2. Remove NSX-T plugin.
            3. Run command 'fuel plugins' to ensure the NSX-T plugin has
               been removed.

        Duration: 5 min
        """
        self.show_step(1)
        self.env.revert_snapshot("nsxt_install")

        self.show_step(2)
        cmd = 'fuel plugins --remove {0}=={1}'.format(
            self.default.PLUGIN_NAME, self.default.NSXT_PLUGIN_VERSION)

        self.ssh_manager.execute_on_remote(
            ip=self.ssh_manager.admin_ip,
            cmd=cmd,
            err_msg='Can not remove plugin.')

        self.show_step(3)
        self.delete_nsxt_plugin()

    @test(depends_on=[nsxt_install],
          groups=['nsxt_kvm_smoke', 'nsxt_smoke'])
    @log_snapshot_after_test
    def nsxt_kvm_smoke(self):
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
        self.show_step(1)
        self.env.revert_snapshot('nsxt_install')

        self.show_step(2)
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=self.default.cluster_settings,
            configure_ssl=False)

        self.show_step(3)
        self.fuel_web.update_nodes(cluster_id, {'slave-01': ['controller']})

        self.reconfigure_cluster_interfaces(cluster_id)

        self.show_step(4)
        self.enable_plugin(cluster_id)

        self.show_step(5)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(6)
        self.fuel_web.run_ostf(cluster_id=cluster_id, test_sets=['smoke'])


@test(groups=["plugins", "nsxt_plugin", 'nsxt_bvt_scenarios'])
class TestNSXtBVT(TestNSXtBase):
    """NSX-t BVT scenarios"""

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
        self.install_nsxt_plugin()

        self.show_step(2)
        settings = self.default.cluster_settings
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
        target_node_2 = \
            self.fuel_web.get_nailgun_node_by_name('slave-07')['hostname']
        self.fuel_web.vcenter_configure(cluster_id,
                                        multiclusters=True,
                                        target_node_2=target_node_2)
        self.show_step(5)
        self.enable_plugin(cluster_id)

        self.show_step(6)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(7)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity', 'ha'])
