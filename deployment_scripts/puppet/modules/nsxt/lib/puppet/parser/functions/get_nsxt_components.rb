require 'rest-client'
require 'json'
require 'openssl'
require 'open-uri'

module Puppet::Parser::Functions
  newfunction(:get_nsxt_components, :type => :rvalue, :doc => <<-EOS
Returns the address of nsx-t manager, on which enable install-upgrade service
example:
  get_nsxt_components('172.16.0.1,172.16.0.2,172.16.0.3', username, password)
EOS
  ) do |args|
    managers = args[0]
    username = args[1]
    password = args[2]
    managers.split(',').each do |manager|
      # Suppression scheme, NSX-T 1.0 supports only https scheme
      manager.to_s.strip =~ /(https?:\/\/)?(?<manager>.+)/
      manager = Regexp.last_match[:manager]
      service_enabled = check_service_enabled(manager, username, password)
      if service_enabled == 'error'
        next
      elsif service_enabled == 'disabled'
        service_enabled_on_manager = enable_upgrade_service(manager, username, password)
      else
        service_enabled_on_manager = service_enabled
      end
      if check_service_running(service_enabled_on_manager, username, password)
        return get_component(service_enabled_on_manager, username, password)
      else
        service_enabled_on_manager = enable_upgrade_service(service_enabled_on_manager, username, password)
        if check_service_running(service_enabled_on_manager, username, password)
          return get_component(service_enabled_on_manager, username, password)
        end
      end
      raise Puppet::Error,("\nCan not enable install-upgrade service on nsx-t manager\n")
    end
  end
end

def disable_upgrade_service(manager, username, password)
  debug("Try disable install-upgrade service on #{manager}")
  request = {'service_name' => 'install-upgrade', 'service_properties' => {'enabled' => false }}
  api_url = "https://#{manager}/api/v1/node/services/install-upgrade"
  response = nsxt_api(api_url, username, password, 'put', request.to_json)
  if response['service_properties']['enabled'] == false
    return
  end
  raise Puppet::Error,("\nCannot disable install-upgrade service on nsx-t manager #{manager}\n")
end

def get_component(manager, username, password)
  file_path = '/tmp/nsxt-components.tgz'
  component_url = get_component_url(manager, username, password)
  begin
    File.open(file_path, 'wb') do |saved_file|
      open(component_url, 'rb') do |read_file|
        saved_file.write(read_file.read)
      end
    end
  rescue => error
    raise Puppet::Error,("\nCan not get file from #{url}:\n#{error.message}\n")
  end
  disable_upgrade_service(manager, username, password)
  return file_path
end

def get_component_url(manager, username, password)
  node_version = get_node_version(manager, username, password)
  begin
    manifest = open("http://#{manager}:8080/repository/#{node_version}/metadata/manifest").read
  rescue => error
    raise Puppet::Error,("\nCan not get url for nsx-t components from #{url}:\n#{error.message}\n")
  end
  manifest.split(/\n/).each do |str|
    if str.include? 'NSX_HOST_COMPONENT_UBUNTU_1404_TAR'
      url = str.split('=')[1]
      return "http://#{manager}:8080#{url}"
    end
  end
end

def get_node_version(manager, username, password)
  debug("Try get nsx-t node version from #{manager}")
  api_url = "https://#{manager}/api/v1/node"
  response = nsxt_api(api_url, username, password, 'get')
  if not response.to_s.empty?
    return response['node_version']
  end
  raise Puppet::Error,("\nCan not get node version from #{manager}\n")
end

def check_service_enabled(manager, username, password)
  debug("Check install-upgrade service enabled on #{manager}")
  api_url = "https://#{manager}/api/v1/node/services/install-upgrade"
  response = nsxt_api(api_url, username, password, 'get')
  if not response.to_s.empty?
    if response['service_properties']['enabled'] == true
      return response['service_properties']['enabled_on']
    end
    return 'disabled'
  end
  return 'error'
end

def check_service_running(manager, username, password)
  debug("Check install-upgrade service running on #{manager}")
  api_url = "https://#{manager}/api/v1/node/services/install-upgrade/status"
  response = nsxt_api(api_url, username, password, 'get')
  if not response.to_s.empty?
    if response['runtime_state'] == 'running'
      return true
    end
  end
  return false
end

def enable_upgrade_service(manager, username, password)
  debug("Try enable install-upgrade service on #{manager}")
  request = {'service_name' => 'install-upgrade', 'service_properties' => {'enabled' => true }}
  api_url = "https://#{manager}/api/v1/node/services/install-upgrade"
  response = nsxt_api(api_url, username, password, 'put', request.to_json)
  if response['service_properties']['enabled'] == true
    return response['service_properties']['enabled_on']
  end
  raise Puppet::Error,("\nCannot enable install-upgrade service on nsx-t manager #{manager}\n")
end

def nsxt_api(api_url, username, password, method, request='', timeout=5)
  retry_count = 3
  begin
    if method == 'get'
      response = RestClient::Request.execute(method: :get, url: api_url, timeout: timeout, user: username, password: password, verify_ssl: OpenSSL::SSL::VERIFY_NONE)
    elsif method == 'put'
      response = RestClient::Request.execute(method: :put, url: api_url, payload: request, timeout: timeout, user: username, password: password, verify_ssl: OpenSSL::SSL::VERIFY_NONE, headers: {'Content-Type' => 'application/json'})
    end
    response_hash = JSON.parse(response.body)
    return response_hash
  rescue Errno::ECONNREFUSED
    notice("\nCan not get response from #{api_url} - 'Connection refused', try next if exist\n")
    return ""
  rescue Errno::EHOSTUNREACH
    notice("\nCan not get response from #{api_url} - 'No route to host', try next if exist\n")
    return ""
  rescue => error
    retry_count -= 1
    if retry_count > 0
      sleep 10
      retry
    else
      raise Puppet::Error,("\nCan not get response from #{api_url} :\n#{error.message}\n#{JSON.parse(error.response)['error_message']}\n")
    end
  end
end
