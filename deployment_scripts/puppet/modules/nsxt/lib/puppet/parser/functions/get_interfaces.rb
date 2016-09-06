module Puppet::Parser::Functions
  newfunction(:get_interfaces, :type => :rvalue, :doc => <<-EOS
Returns the array of interface names for nsx-t manager VTEPs.
EOS
  ) do |args|
    pnics = args[0]
    vtep_interfaces = []
    pnics.each do |pnic_pair|
      device,uplink = pnic_pair.split(':')
      vtep_interfaces.push(device.strip)
    end
    return vtep_interfaces
  end
end
