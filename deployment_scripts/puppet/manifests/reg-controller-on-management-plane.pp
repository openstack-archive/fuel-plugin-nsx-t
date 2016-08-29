notice('fuel-plugin-nsx-t: reg-controller-on-management-plane.pp')

include ::nsxt::params

$settings     = hiera($::nsxt::params::hiera_key)
$managers     = $settings['nsx_api_managers']
$user         = $settings['nsx_api_user']
$password     = $settings['nsx_api_password']

nsxt_add_to_fabric { 'Register controller node on management plane':
  ensure   => present,
  managers => $managers,
  username => $user,
  password => $password,
}
