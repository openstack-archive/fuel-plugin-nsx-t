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

from fuelweb_test.settings import get_var_as_bool
from fuelweb_test.settings import iface_alias
from fuelweb_test.settings import NEUTRON_SEGMENT_TYPE


HALF_MIN_WAIT = 30  # 30 seconds
WAIT_FOR_COMMAND = 60 * 3  # 3 minutes
WAIT_FOR_LONG_DEPLOY = 60 * 180  # 180 minutes

EXT_IP = '8.8.8.8'  # Google DNS ^_^
PRIVATE_NET = os.environ.get('PRIVATE_NET', "admin_internal_net")
ADMIN_NET = os.environ.get('ADMIN_NET', 'admin_floating_net')
DEFAULT_ROUTER_NAME = os.environ.get('DEFAULT_ROUTER_NAME', 'router04')
METADATA_IP = os.environ.get('METADATA_IP', '169.254.169.254')
VM_USER = 'cirros'
VM_PASS = 'cubswin:)'
AZ_VCENTER1 = 'vcenter'
AZ_VCENTER2 = 'vcenter2'
FLAVOR_NAME = 'm1.micro128'

PLUGIN_NAME = os.environ.get('NSXT_PLUGIN_VERSION', 'nsx-t')
NSXT_PLUGIN_PATH = os.environ.get('NSXT_PLUGIN_PATH')
NSXT_PLUGIN_VERSION = os.environ.get('NSXT_PLUGIN_VERSION', '1.0.0')


assigned_networks = {
    iface_alias('eth0'): ['fuelweb_admin', 'private'],
    iface_alias('eth1'): ['public'],
    iface_alias('eth2'): ['storage'],
    iface_alias('eth4'): ['management']
}

cluster_settings = {
    'net_provider': 'neutron',
    'assign_to_all_nodes': True,
    'net_segment_type': NEUTRON_SEGMENT_TYPE
}

plugin_configuration = {
    'insecure/value': get_var_as_bool(os.environ.get('NSXT_INSECURE'), True),
    'nsx_api_managers/value': os.environ.get('NSXT_MANAGERS_IP'),
    'nsx_api_user/value': os.environ.get('NSXT_USER'),
    'nsx_api_password/value': os.environ.get('NSXT_PASSWORD'),
    'default_overlay_tz_uuid/value': os.environ.get('NSXT_OVERLAY_TZ_UUID'),
    'default_vlan_tz_uuid/value': os.environ.get('NSXT_VLAN_TZ_UUID'),
    'default_tier0_router_uuid/value': os.environ.get(
        'NSXT_TIER0_ROUTER_UUID'),
    'default_edge_cluster_uuid/value': os.environ.get(
        'NSXT_EDGE_CLUSTER_UUID'),
    'uplink_profile_uuid/value': os.environ.get('NSXT_UPLINK_PROFILE_UUID'),
    'controller_ip_pool_uuid/value': os.environ.get(
        'NSXT_CONTROLLER_IP_POOL_UUID'),
    'controller_pnics_pairs/value': os.environ.get(
        'NSXT_CONTROLLER_PNICS_PAIRS'),
    'compute_ip_pool_uuid/value': os.environ.get('NSXT_COMPUTE_IP_POOL_UUID'),
    'compute_pnics_pairs/value': os.environ.get('NSXT_COMPUTE_PNICS_PAIRS'),
    'floating_ip_range/value': os.environ.get('NSXT_FLOATING_IP_RANGE'),
    'floating_net_cidr/value': os.environ.get('NSXT_FLOATING_NET_CIDR'),
    'internal_net_cidr/value': os.environ.get('NSXT_INTERNAL_NET_CIDR'),
    'floating_net_gw/value': os.environ.get('NSXT_FLOATING_NET_GW'),
    'internal_net_dns/value': os.environ.get('NSXT_INTERNAL_NET_DNS')
}
