require File.join(File.dirname(__FILE__),'..', 'nsxtutils')

Puppet::Type.type(:nsxt_add_to_fabric).provide(:nsxt_add_to_fabric, :parent => Puppet::Provider::Nsxtutils) do

  # need this for work nsxtcli method, otherwise not work
  commands :nsxcli => 'nsxcli'

  def create
    debug("Attempting to register a node")
    # need define for return error from cycle
    out_reg = ''
    @resource[:managers].each do |manager|
      thumbprint = get_manager_thumbprint(manager, ca_file = @resource[:ca_file])
      if not thumbprint.empty?
        # 12 retry x 15 sleep time = 3 minutes timeout
        retry_count = 12
        while retry_count > 0
          out_reg = nsxtcli("join management-plane #{manager} username #{@resource[:username]} thumbprint #{thumbprint} password #{@resource[:password]}")
          if exists?
            notice("Node added to NSX-T fabric")
            return true
          else
            retry_count -= 1
            sleep 15
          end
        end
      end
    end
    raise Puppet::Error,("\nNode not add to NSX-t fabric:\n #{out_reg}\n")
  end

  def exists?
    connected_managers = nsxtcli("get managers")
    if connected_managers.include? "Connected"
      node_id = get_node_id
      if not node_id.empty?
        @resource[:managers].each do |manager|
          if check_node_registered(manager, node_id)
            debug("Node '#{node_id}' connected and registered on '#{manager}'")
            return true
          end
        end
      end
    end
    debug("Node NOT registered on NSX-T manager")
    return false
  end

  def destroy
    debug("Attempting to unregister a node")
    # need define for return error from cycle
    out_unreg = ''
    @resource[:managers].each do |manager|
      thumbprint = get_manager_thumbprint(manager, ca_file = @resource[:ca_file])
      if not thumbprint.empty?
        # 12 retry x 15 sleep time = 3 minutes timeout
        retry_count = 12
        while retry_count > 0
          out_unreg = nsxtcli("detach management-plane #{manager} username #{@resource[:username]} thumbprint #{thumbprint} password #{@resource[:password]}")
          if not exists?
            notice("Node deleted from NSX-T fabric")
            return true
          else
            retry_count -= 1
            sleep 15
          end
        end
      end
    end
    raise Puppet::Error,("\nNode not deleted from NSX-t fabric: \n #{out_unreg}\n")
  end

  def check_node_registered(manager, node_id)
    api_url = "https://#{manager}/api/v1/fabric/nodes/#{node_id}/state"
    response = get_nsxt_api(api_url, @resource[:username], @resource[:password], @resource[:ca_file])
    if not response.to_s.empty?
      if response['state'] == 'success'
        debug("Node '#{node_id}' registered on '#{manager}'")
        return true
      else
        debug("Node NOT registered on '#{manager}', details:\n#{response['details']}")
      end
    else
      debug("Node NOT registered on '#{manager}'")
    end
    return false
  end

end
