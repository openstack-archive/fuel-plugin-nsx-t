require 'yaml'

module Puppet::Parser::Functions
  newfunction(:skip_provider_network, :doc => <<-EOS
Custom function to override hiera parameters, the first argument -
file name, where write new parameters in yaml format, ex:
   hiera_overrides('/etc/hiera/test.yaml')
EOS
  ) do |args|
    filename = args[0]

    begin
      yaml_string = File.read filename
      hiera_overrides = YAML.load yaml_string
    rescue Errno::ENOENT
      hiera_overrides = {}
    end

    hiera_overrides['skip_provider_network'] = true

    # write to hiera override yaml file
    File.open(filename, 'w') { |file| file.write(hiera_overrides.to_yaml) }
  end
end
