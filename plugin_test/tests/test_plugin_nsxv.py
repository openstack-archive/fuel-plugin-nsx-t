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
import paramiko
import time

from devops.error import TimeoutError
from devops.helpers.helpers import wait
from proboscis import test

from proboscis.asserts import assert_false
from proboscis.asserts import assert_true

from fuelweb_test import logger

from fuelweb_test.helpers import os_actions
from fuelweb_test.helpers import utils

from fuelweb_test.helpers.common import Common
from fuelweb_test.helpers.decorators import log_snapshot_after_test
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.settings import NEUTRON_SEGMENT_TYPE
from fuelweb_test.settings import SERVTEST_PASSWORD
from fuelweb_test.settings import SERVTEST_TENANT
from fuelweb_test.settings import SERVTEST_USERNAME
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic
from helpers import settings as pt_settings  # Plugin Tests Settings

from helpers.openstack import HopenStack


@test(groups=["plugins", "nsxt_plugin"])
class TestNSXtPlugin(TestBasic):
    """Here are automated tests from test plan that has mark 'Automated'."""

    _common = None
    plugin_name = 'nsx-t'
    plugin_version = '1.0.0'

    def install_nsxt_plugin(self):
        """Install plugin on fuel node."""
        utils.upload_tarball(
            ip=self.ssh_manager.admin_ip,
            tar_path=pt_settings.NSXT_PLUGIN_PATH,
            tar_target='/var')

        utils.install_plugin_check_code(
            ip=self.ssh_manager.admin_ip,
            plugin=os.path.basename(pt_settings.NSXT_PLUGIN_PATH))

    def enable_plugin(self, cluster_id, settings={}):
        """Fill the necessary fields with required values.

        :param cluster_id: cluster id to use with Common
        :param settings: dict that will be merged with default settings
        """
        assert_true(
            self.fuel_web.check_plugin_exists(cluster_id, self.plugin_name),
            "Test aborted")

        # Update plugin settings
        self.fuel_web.update_plugin_settings(
            cluster_id,
            self.plugin_name,
            self.plugin_version,
            dict(pt_settings.plugin_configuration, **settings))

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

        self.install_nsxt_plugin()

        # Configure cluster
        settings = self.get_settings()
        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=settings,
            configure_ssl=False)

        # Assign roles to nodes
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'], })

        # Configure VMWare vCenter settings
        self.fuel_web.vcenter_configure(cluster_id)

        self.enable_plugin(cluster_id=cluster_id)

        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['smoke'])
