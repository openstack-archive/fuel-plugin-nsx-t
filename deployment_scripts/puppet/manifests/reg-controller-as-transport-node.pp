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
