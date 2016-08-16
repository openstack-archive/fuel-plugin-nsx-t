Puppet::Type.newtype(:nsxt_add_to_fabric) do

  @doc = "Add kvm node to NSX-T fabric."

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

end
