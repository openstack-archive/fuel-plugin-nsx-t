require 'yaml'

module Puppet::Parser::Functions
  newfunction(:hiera_overrides, :doc => <<-EOS
Custom function to override hiera parameters, the first argument -
file name, where write new parameters in yaml format, ex:
   hiera_overrides('/etc/hiera/test.yaml')
EOS
  ) do |args|
    filename = args[0]
    hiera_overrides = {}

    # override neutron_advanced_configuration
    neutron_advanced_configuration = {}
    neutron_advanced_configuration['neutron_dvr'] = false
    neutron_advanced_configuration['neutron_l2_pop'] = false
    neutron_advanced_configuration['neutron_l3_ha'] = false
    neutron_advanced_configuration['neutron_qos'] = false
    hiera_overrides['neutron_advanced_configuration'] = neutron_advanced_configuration

    # write to hiera override yaml file
    File.open(filename, 'w') { |file| file.write(hiera_overrides.to_yaml) }
  end
end
