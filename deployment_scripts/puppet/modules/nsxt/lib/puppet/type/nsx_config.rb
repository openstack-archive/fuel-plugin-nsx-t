Puppet::Type::newtype(:nsx_config) do

  ensurable

  newparam(:name, :namevar => true) do
    desc 'Section name to manage from nsx.ini'
    newvalues(/\S+\/\S+/)
  end

  newparam(:secret, :boolean => true) do
    newvalues(:true, :false)

    defaultto false
  end

  newparam(:ensure_absent_val) do
    defaultto('<DEFAULT>')
  end

  newproperty(:value) do
    munge do |value|
      value = value.to_s.strip
      value
    end
    newvalues(/^[\S ]*$/)

  end
end
