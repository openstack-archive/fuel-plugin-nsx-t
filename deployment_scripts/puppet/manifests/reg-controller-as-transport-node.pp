notice('fuel-plugin-nsx-t: reg-controller-as-transport-node.pp')

include ::nsxt::params

$settings            = hiera($::nsxt::params::hiera_key)
$managers            = $settings['nsx_api_managers']
$user                = $settings['nsx_api_user']
$password            = $settings['nsx_api_password']
$uplink_profile_uuid = $settings['uplink_profile_uuid']
$static_ip_pool_uuid = $settings['static_ip_pool_uuid']
$transport_zone_uuid = $settings['transport_zone_uuid']
$pnics_pairs         = $settings['pnics_pairs']

nsxt_create_transport_node { 'Add transport node':
  ensure            => present,
  managers          => $managers,
  username          => $user,
  password          => $password,
  uplink_profile_id => $uplink_profile_uuid,
  pnics             => $pnics_pairs,
  static_ip_pool_id => $static_ip_pool_uuid,
  transport_zone_id => $transport_zone_uuid,
}
 
if !$settings['insecure'] {
  $ca_filename = try_get_value($settings['ca_file'],'name','')
  if empty($ca_filename) {
    # default path to ca for Ubuntu 14.0.4
    $ca_file = "/etc/ssl/certs/ca-certificates.crt"
  } else {
    $ca_file = "${::nsxt::params::nsx_plugin_dir}/${ca_filename}"
  }
  Nsxt_create_transport_node { ca_file => $ca_file }
}

firewall {'0000 Accept STT traffic':
  proto  => 'tcp',
  dport  => ['7471'],
  action => 'accept',
  before => Nsxt_create_transport_node['Add transport node'],
}
