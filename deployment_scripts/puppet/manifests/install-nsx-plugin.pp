notice('fuel-plugin-nsx-t: install-nsx-plugin.pp')

include ::nsxt::params

apt::pin { 'nsx-t':
  ensure   => present,
  priority => 2000,
  label    => 'nsx-t',
  before   => Package['python-neutron-lib'],
}

package { $::nsxt::params::plugin_package:
  ensure => present,
}

package { 'python-neutron-lib':
  ensure  => latest,
}
