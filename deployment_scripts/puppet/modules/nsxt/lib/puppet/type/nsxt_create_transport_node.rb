Puppet::Type.newtype(:nsxt_create_transport_node) do

  @doc = "Create from kvm node NSX-T transport node."

  ensurable

  newparam(:managers) do
    isnamevar
    desc 'IP address of one or more NSX-T managers separated by commas.'
    munge do |value|
      array = []
      value.split(',').each do |manager|
        manager.to_s.strip =~ /(https:\/\/)?(?<host>[^:]+):?(?<port>\d+)?/
        host= Regexp.last_match[:host]
        port = Regexp.last_match[:port]
        port = 443 if port.to_s.empty?
        # Suppression scheme, NSX-T 1.0 supports only https scheme
        array.push("#{host}:#{port}")
      end
      value = array
    end
  end

  newparam(:username) do
    desc 'The user name for login to NSX-T manager.'
  end

  newparam(:password) do
    desc 'The password for login to NSX-T manager.'
  end

  newparam(:ca_file) do
    desc 'CA certificate to verify NSX-T manager certificate.'
    defaultto ''
  end

  newparam(:host_switch_name) do
    desc 'HostSwitch name. Should coincide with host switch name in transport zone.'
  end

  newparam(:host_switch_profile_ids, :array_matching => :all) do
    desc 'Ids of HostSwitch profiles to be associated with this HostSwitch.'
  end

  newparam(:pnics, :array_matching => :all) do
    desc 'Array of "device_name : uplink_name" pairs.'
  end

  newparam(:static_ip_pool_id) do
    desc 'ID of already configured Static IP Pool.'
  end

  newparam(:transport_zone_id) do
    desc 'Transport zone ID.'
  end

  newparam(:transport_zone_profile_ids, :array_matching => :all) do
    desc 'Array of TransportZoneProfileTypeIdEntry .'
    defaultto ''
  end

end
