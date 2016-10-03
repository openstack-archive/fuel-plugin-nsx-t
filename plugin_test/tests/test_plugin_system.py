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


@test(groups=["plugins", "nsxt_plugin", 'nsxt_system'])
class TestNSXtSystem(TestNSXtBase):
    """Tests from test plan that have been marked as 'Automated'."""

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=['nsxt_ha_mode'])
    @log_snapshot_after_test
    def nsxt_ha_mode(self):
        """Setup for system tests.

        Scenario:
            1. Log in to the Fuel web UI with preinstalled NSX-T plugin.
            2. Create a new environment with following parameters:
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
            5. Configure network settings.
            6. Enable and configure NSX-T plugin.
            7. Configure VMware vCenter Settings. Add 1 vSphere cluster and
               configure Nova Compute instance on conrollers.
            8. Verify networks.
            9. Deploy cluster.
            10. Run OSTF.

        Duration: 120 min
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
        self.fuel_web.vcenter_configure(cluster_id)

        self.show_step(8)
        self.fuel_web.verify_network(cluster_id)

        self.show_step(9)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.show_step(10)
        self.fuel_web.run_ostf(cluster_id)
