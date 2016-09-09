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

from proboscis.asserts import assert_true

from fuelweb_test.helpers import utils
from helpers import settings as vars


def install_nsxt_plugin(master_node_ip):
    """Download and instal NSX-T plugin on master node.

    :param master_node_ip: ip of master node in str format
    :return:
    """
    utils.upload_tarball(ip=master_node_ip,
                         tar_path=vars.NSXT_PLUGIN_PATH,
                         tar_target='/var')

    utils.install_plugin_check_code(
        ip=master_node_ip,
        plugin=os.path.basename(vars.NSXT_PLUGIN_PATH))


def enable_plugin(fuel_web_client, cluster_id, settings={}):
    """Enable NSX-T plugin on cluster.

    :param cluster_id: cluster id
    :param fuel_web_client: fuel_web
    :param settings: settings in dict format
    :return: None
    """
    msg = "Plugin couldn't be enabled. Check plugin version. Test aborted"
    checker = fuel_web_client.check_plugin_exists(cluster_id, vars.PLUGIN_NAME)
    assert_true(checker, msg)

    fuel_web_client.update_plugin_settings(
        cluster_id,
        vars.PLUGIN_NAME,
        vars.NSXT_PLUGIN_VERSION,
        dict(vars.plugin_configuration, **settings))