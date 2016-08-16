# require ruby-rest-client, ruby-json

require 'rest-client'
require 'json'
require 'socket'
require 'openssl'

class Puppet::Provider::Nsxtutils < Puppet::Provider

  def get_nsxt_api(api_url, username, password, ca_file, timeout=5)
    retry_count = 3
    begin
      if ca_file.to_s.empty?
        response = RestClient::Request.execute(method: :get, url: api_url, timeout: timeout, user: username, password: password, verify_ssl: OpenSSL::SSL::VERIFY_NONE)
      else
        response = RestClient::Request.execute(method: :get, url: api_url, timeout: timeout, user: username, password: password, verify_ssl: OpenSSL::SSL::VERIFY_PEER, ssl_ca_file: ca_file)
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

  def post_nsxt_api(api_url, username, password, request, ca_file, timeout=5)
    retry_count = 3
    begin
      if ca_file.to_s.empty?
        response = RestClient::Request.execute(method: :post, url: api_url, payload: request, timeout: timeout, user: username, password: password, verify_ssl: OpenSSL::SSL::VERIFY_NONE,headers: {'Content-Type' => 'application/json'})
      else
        response = RestClient::Request.execute(method: :post, url: api_url, payload: request, timeout: timeout, user: username, password: password, verify_ssl: OpenSSL::SSL::VERIFY_PEER, ssl_ca_file: ca_file, headers: {'Content-Type' => 'application/json'})
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

  def delete_nsxt_api(api_url, username, password, ca_file, timeout=5)
    retry_count = 3
    begin
      if ca_file.to_s.empty?
        response = RestClient::Request.execute(method: :delete, url: api_url, timeout: timeout, user: username, password: password, verify_ssl: OpenSSL::SSL::VERIFY_NONE)
      else
        response = RestClient::Request.execute(method: :delete, url: api_url, timeout: timeout, user: username, password: password, verify_ssl: OpenSSL::SSL::VERIFY_PEER, ssl_ca_file: ca_file)
      end
      # if http code not 20x - rest client raise exception
      return true
    rescue Errno::ECONNREFUSED
      notice("\nCan not get response from #{api_url} - 'Connection refused', try next if exist\n")
      return false
    rescue Errno::EHOSTUNREACH
      notice("\nCan not get response from #{api_url} - 'No route to host', try next if exist\n")
      return false
    rescue => error
      retry_count -= 1
      if retry_count > 0
        sleep 10
        retry
      else
        raise Puppet::Error,("\nCan not get response from #{api_url} :\n#{error.message}\n")
      end
    end
  end

  def get_node_id
    uuid = nsxtcli("get node-uuid")
    if uuid =~ /\A[\da-f]{32}\z/i or uuid =~ /\A(urn:uuid:)?[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}\z/i
      return uuid
    end
    notice("Cannot get node uuid")
    return ""
  end

  def get_transport_node_id(manager, node_id, ca_file)
    api_url = "https://#{manager}/api/v1/transport-nodes"
    response = get_nsxt_api(api_url, @resource[:username], @resource[:password], @resource[:ca_file])
    if not response.to_s.empty?
      response['results'].each do |node|
        if node['node_id'] == node_id
          return node['id']
        end
      end
    end
    notice("Cannot get transport node id")
    return ""
  end

  def nsxtcli(cmd)
    out_cli = nsxcli(['-c', cmd]).to_s.strip
    debug("cmd out:\n #{out_cli}")
    return out_cli
  end

  def get_manager_host_port(manager)
    # scheme does not take into account, NSX-T 1.0 supports only https
    manager =~ /(https:\/\/)?(?<host>[^:]+):?(?<port>\d+)?/
    manager_host_port = {}
    manager_host_port['host']= Regexp.last_match[:host]
    port = Regexp.last_match[:port]
    port = 443 if port.to_s.empty?
    manager_host_port['port'] = port
    return manager_host_port
  end

  def get_manager_thumbprint(manager, timeout=5, ca_file)
    manager_host_port = get_manager_host_port(manager)
    host = manager_host_port['host']
    port = manager_host_port['port']
    retry_count = 3
    begin
      tcp_client = TCPSocket.new(host, port, timeout)
      ssl_context = OpenSSL::SSL::SSLContext.new()
      if ca_file.to_s.empty?
        ssl_context.verify_mode = OpenSSL::SSL::VERIFY_NONE
      else
        ssl_context.verify_mode = OpenSSL::SSL::VERIFY_PEER
        ssl_context.ca_file = ca_file
      end
      ssl_client = OpenSSL::SSL::SSLSocket.new(tcp_client, ssl_context)
      ssl_client.connect
      cert = OpenSSL::X509::Certificate.new(ssl_client.peer_cert)
      ssl_client.sysclose
      tcp_client.close
      tp = OpenSSL::Digest::SHA256.new(cert.to_der)
      return OpenSSL::Digest::SHA256.new(cert.to_der).to_s
    rescue Errno::ECONNREFUSED
      notice("\nCan not get 'thumbprint' from #{host}:#{port} - 'Connection refused', try next if exist\n")
      return ""
    rescue Errno::EHOSTUNREACH
      notice("\nCan not get 'thumbprint' from #{host}:#{port} - 'No route to host', try next if exist\n")
      return ""
    rescue => error
      retry_count -= 1
      if retry_count > 0
        sleep 5
        retry
      else
        raise Puppet::Error,("\nCan not get thumbprint from #{host}:#{port} :\n#{error.message}\n")
      end
    end
  end

end
