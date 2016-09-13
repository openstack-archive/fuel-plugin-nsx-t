require 'socket'
require File.join(File.dirname(__FILE__),'..', 'nsxtutils')

Puppet::Type.type(:nsxt_create_transport_node).provide(:nsxt_create_transport_node, :parent => Puppet::Provider::Nsxtutils) do

  # need this for work nsxtcli method, otherwise not work
  commands :nsxcli => 'nsxcli'

  def create
    host_switch_profile_ids = [{'key' => 'UplinkHostSwitchProfile', 'value' => @resource[:uplink_profile_id] }]
    pnics = create_pnics_array(@resource[:pnics])
    node_id = get_node_id
    display_name = Socket.gethostname
    # the host switch name of the transport zone must match the host switch name to create transport nodes
    host_switch_name = get_host_switch_name(@resource[:managers], @resource[:transport_zone_id])
    request = {'display_name' => display_name,
               'node_id' => node_id,
               'host_switches' => [{'host_switch_name' => host_switch_name,
                                    'static_ip_pool_id' => @resource[:static_ip_pool_id],
                                    'host_switch_profile_ids' => host_switch_profile_ids,
                                    'pnics' => pnics}],
               'transport_zone_endpoints' => [{'transport_zone_id' => @resource[:transport_zone_id]}]
              }
    # puppet retrun string if provide array parametr with single element
    # https://projects.puppetlabs.com/issues/9850
    transport_zone_profile_ids = @resource[:transport_zone_profile_ids]
    if not transport_zone_profile_ids.instance_of? Array
      transport_zone_profile_ids = [transport_zone_profile_ids]
    end
    if not transport_zone_profile_ids[0].to_s.empty?
      request['transport_zone_endpoints'].push(transport_zone_profile_ids)
    end
    debug("Attempting to create a transport node")
    @resource[:managers].each do |manager|
      api_url = "https://#{manager}/api/v1/transport-nodes"
      begin
        response = post_nsxt_api(api_url, @resource[:username], @resource[:password], request.to_json, @resource[:ca_file])
      rescue => error
        raise Puppet::Error,("\nFailed to create the transport node: #{error.message}\n")
      end
      if not response.to_s.empty?
        # 12 retry x 15 sleep time = 3 minutes timeout
        retry_count = 12
        while retry_count > 0
          if exists?
            notice("Node '#{node_id}' added to NSX-T as transport node")
            return true
          else
            retry_count -= 1
            sleep 15
          end
        end
      end
    end
    raise Puppet::Error,("\nFailed to create the transport node, status in NSX-T manager not updated\n")
  end

  def exists?
    connected_managers = nsxtcli("get controllers")
    if connected_managers.include? "connected"
      node_id = get_node_id
      if not node_id.empty?
        @resource[:managers].each do |manager|
          if check_node_lcp_connected(manager, node_id)
            debug("Node '#{node_id}' connected to controllers and LCP connectivity status UP on '#{manager}'")
            return true
          end
        end
      else
        raise Puppet::Error,("\nFailed to create the transport node:\nNode not registered in management plane\n")
      end
    end
    debug("Node NOT connected to NSX-T controllers")
    return false
  end

  def destroy
    debug("Attempting to delete a transport node")
    node_id = get_node_id
    @resource[:managers].each do |manager|
      transport_node_id = get_transport_node_id(manager, node_id, @resource[:ca_file])
      if not transport_node_id.empty?
        api_url = "https://#{manager}/api/v1/transport-nodes/#{transport_node_id}"
        begin
          response = delete_nsxt_api(api_url, @resource[:username], @resource[:password], @resource[:ca_file])
        rescue => error
          raise Puppet::Error,("\nFailed to delete the transport node: #{error.message}\n")
        end
        if response
          # 12 retry x 15 sleep time = 3 minutes timeout
          retry_count = 12
            while retry_count > 0
              if not exists?
                notice("Transport node '#{node_id}' delete from NSX-T")
                return true
              else
                retry_count -= 1
                sleep 15
              end
          end
        end
      end
    end
    raise Puppet::Error,("\nFailed to delete the transport node.\n")
  end

  def check_node_lcp_connected(manager, node_id)
    api_url = "https://#{manager}/api/v1/fabric/nodes/#{node_id}/status"
    response = get_nsxt_api(api_url, @resource[:username], @resource[:password], @resource[:ca_file])
    if not response.to_s.empty?
      if response['lcp_connectivity_status'] == 'UP'
        debug("Node '#{node_id}' LCP status UP on '#{manager}'")
        return true
      else
        debug("Node LCP status '#{response['lcp_connectivity_status']}' on '#{manager}'")
        if not response['lcp_connectivity_status_details'].empty?
          response['lcp_connectivity_status_details'].each do |details|
            debug("On #{details['control_node_ip']} status: #{details['status']} failure_status: #{details['failure_status']}")
          end
        end
      end
    else
      debug("Node LCP status NOT UP on '#{manager}'")
    end
    return false
  end

  def get_host_switch_name(managers, transport_zone_id)
    managers.each do |manager|
      debug("Attempt to get host_switch_name for '#{transport_zone_id}' transport zone from '#{manager}' manager")
      api_url = "https://#{manager}/api/v1/transport-zones/#{transport_zone_id}"
      response = get_nsxt_api(api_url, @resource[:username], @resource[:password], @resource[:ca_file])
      if not response.to_s.empty?
        return response['host_switch_name']
      end
    end
    raise Puppet::Error,("\nCannot get host_switch_name for '#{transport_zone_id}' transport zone.\n")
  end

  def create_pnics_array(pnics)
    result_pnic_pairs = []
    pnics.each_line do |pnic_pair|
      device,uplink = pnic_pair.split(':')
      result_pnic_pairs.push({'device_name' => device.strip, 'uplink_name' => uplink.strip})
    end
    return result_pnic_pairs
  end

end
