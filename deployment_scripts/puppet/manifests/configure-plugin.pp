notice('fuel-plugin-nsx-t: configure-plugin.pp')

include ::nsxt::params

file { $::nsxt::params::nsx_plugin_dir:
  ensure => directory,
}

file { $::nsxt::params::nsx_plugin_config:
  ensure  => present,
  content => template("nsxt/nsx.ini")
}


$settings     = hiera($::nsxt::params::hiera_key)
$managers     = $settings['nsx_api_managers']
$user         = $settings['nsx_api_user']
$password     = $settings['nsx_api_password']
$overlay_tz   = $settings['default_overlay_tz_uuid']
$vlan_tz      = $settings['default_vlan_tz_uuid']
$tier0_router = $settings['default_tier0_router_uuid']
$edge_cluster = $settings['default_edge_cluster_uuid']

nsx_config {
  'nsx_v3/nsx_api_managers':          value => $managers;
  'nsx_v3/nsx_api_user':              value => $user;
  'nsx_v3/nsx_api_password':          value => $password;
  'nsx_v3/default_overlay_tz_uuid':   value => $overlay_tz;
  'nsx_v3/default_vlan_tz_uuid':      value => $vlan_tz;
  'nsx_v3/default_tier0_router_uuid': value => $tier0_router;
  'nsx_v3/default_edge_cluster_uuid': value => $edge_cluster;
}

file { '/etc/neutron/plugin.ini':
  ensure  => link,
  target  => $::nsxt::params::nsx_plugin_config,
  replace => true,
  require => File[$::nsxt::params::nsx_plugin_dir]
}

File[$::nsxt::params::nsx_plugin_dir]->
File[$::nsxt::params::nsx_plugin_config]->
Nsx_config<||>
