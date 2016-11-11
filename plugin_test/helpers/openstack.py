"""Copyright 2016 Mirantis, Inc.
Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
"""
import time

import paramiko
from proboscis.asserts import assert_true
from devops.helpers.helpers import icmp_ping
from devops.helpers.helpers import tcp_ping
from devops.helpers.helpers import wait

from fuelweb_test import logger
from fuelweb_test.helpers.ssh_manager import SSHManager
from fuelweb_test.helpers.utils import pretty_log
from helpers import settings


# Defaults
external_net_name = settings.ADMIN_NET
zone_image_maps = {
    'vcenter': 'TestVM-VMDK',
    'nova': 'TestVM',
    'vcenter-cinder': 'TestVM-VMDK'
}
instance_creds = (settings.VM_USER, settings.VM_PASS)


def create_instance(os_conn, net=None, az='nova', sg_names=None,
                    flavor_name='m1.micro', timeout=180, **kwargs):
    """Create instance with specified az and flavor.

    :param os_conn: OpenStack
    :param net: network object (default is private net)
    :param az: availability zone name
    :param sg_names: list of security group names
    :param flavor_name: name of flavor
    :param timeout: seconds to wait creation
    :return: vm
    """
    sg_names = sg_names if sg_names else ['default']

    def find_by_name(objects, name):
        for obj in objects:
            if obj.name == name:
                return obj

    image = find_by_name(os_conn.nova.images.list(), zone_image_maps[az])
    flavor = find_by_name(os_conn.nova.flavors.list(), flavor_name)

    net = net if net else os_conn.get_network(settings.PRIVATE_NET)
    sg = [os_conn.get_security_group(name) for name in sg_names]

    vm = os_conn.create_server(availability_zone=az,
                               timeout=timeout,
                               image=image,
                               net_id=net['id'],
                               security_groups=sg,
                               flavor_id=flavor.id,
                               **kwargs)
    return vm


def check_instances_state(os_conn):
    """Check that instances were not deleted and have 'active' status."""
    instances = os_conn.nova.servers.list()
    for inst in instances:
        assert_true(not os_conn.is_srv_deleted(inst))
        assert_true(os_conn.get_instance_detail(inst).status == 'ACTIVE')


def check_connection_vms(ip_pair, command='pingv4', result_of_command=0,
                         timeout=30, interval=5):
    """Check network connectivity between instances.

    :param ip_pair: type dict, {ip_from: [ip_to1, ip_to2, etc.]}
    :param command: type string, key 'pingv4', 'pingv6' or 'arping'
    :param result_of_command: type integer, exit code of command execution
    :param timeout: wait to get expected result
    :param interval: interval of executing command
    """
    commands = {
        'pingv4': 'ping -c 5 {}',
        'pingv6': 'ping6 -c 5 {}',
        'arping': 'sudo arping -I eth0 {}'
    }

    msg = 'Command "{0}", Actual exit code is NOT {1}'
    for ip_from in ip_pair:
        with get_ssh_connection(ip_from, *instance_creds, timeout=60*5) as ssh:
            for ip_to in ip_pair[ip_from]:
                logger.info('Check connection from {0} to {1}'.format(
                    ip_from, ip_to))
                cmd = commands[command].format(ip_to)

                wait(lambda:
                     execute(ssh, cmd)['exit_code'] == result_of_command,
                     interval=interval,
                     timeout=timeout,
                     timeout_msg=msg.format(cmd, result_of_command))


def check_connection_through_host(remote, ip_pair, command='pingv4',
                                  result_of_command=0, timeout=30,
                                  interval=5):
    """Check network connectivity between instances.

    :param ip_pair: type list, ips of instances
    :param remote: access point IP
    :param command: type string, key 'pingv4', 'pingv6' or 'arping'
    :param result_of_command: type integer, exit code of command execution
    :param timeout: wait to get expected result
    :param interval: interval of executing command
    """
    commands = {
        'pingv4': 'ping -c 5 {}',
        'pingv6': 'ping6 -c 5 {}',
        'arping': 'sudo arping -I eth0 {}'
    }

    msg = 'Command "{0}", Actual exit code is NOT {1}'

    for ip_from in ip_pair:
        for ip_to in ip_pair[ip_from]:
            logger.info('Check ping from {0} to {1}'.format(ip_from, ip_to))
            cmd = commands[command].format(ip_to)
            wait(lambda:
                 remote_execute_command(
                     remote,
                     ip_from,
                     cmd,
                     wait=timeout)['exit_code'] == result_of_command,
                 interval=interval,
                 timeout=timeout,
                 timeout_msg=msg.format(cmd, result_of_command))


def ping_each_other(ips, command='pingv4', expected_ec=0,
                    timeout=30, interval=5, access_point_ip=None):
    """Check network connectivity between instances.

    :param ips: list, list of ips
    :param command: type string, key 'pingv4', 'pingv6' or 'arping'
    :param expected_ec: type integer, exit code of command execution
    :param timeout: wait to get expected result
    :param interval: interval of executing command
    :param access_point_ip: It is used if check via host
    """
    ip_pair = {key: [ip for ip in ips if ip != key] for key in ips}
    if access_point_ip:
        check_connection_through_host(remote=access_point_ip,
                                      ip_pair=ip_pair,
                                      command=command,
                                      result_of_command=expected_ec,
                                      timeout=timeout,
                                      interval=interval)
    else:
        check_connection_vms(ip_pair=ip_pair,
                             command=command,
                             result_of_command=expected_ec,
                             timeout=timeout,
                             interval=interval)


def create_and_assign_floating_ips(os_conn, instances):
    """Associate floating ips with specified instances.

    :param os_conn: type object, openstack
    :param instances: type list, instances
    """
    fips = []
    for instance in instances:
        ip = os_conn.assign_floating_ip(instance).ip
        fips.append(ip)
        wait(lambda: icmp_ping(ip), timeout=60 * 5, interval=5)
    return fips


def get_ssh_connection(ip, username, userpassword, timeout=30, port=22):
    """Get ssh to host.

    :param ip: string, host ip to connect to
    :param username: string, a username to use for authentication
    :param userpassword: string, a password to use for authentication
    :param timeout: timeout (in seconds) for the TCP connection
    :param port: host port to connect to
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, port=port, username=username,
                password=userpassword, timeout=timeout)
    return ssh


def execute(ssh_client, command):
    """Execute command on remote host.

    :param ssh_client: SSHClient to instance
    :param command: type string, command to execute
    """
    channel = ssh_client.get_transport().open_session()
    channel.exec_command(command)
    result = {
        'stdout': channel.recv(1024),
        'stderr': channel.recv_stderr(1024),
        'exit_code': channel.recv_exit_status()
    }
    return result


def remote_execute_command(instance1_ip, instance2_ip, command, wait=30):
    """Check execute remote command.

    :param instance1_ip: string, instance ip connect from
    :param instance2_ip: string, instance ip connect to
    :param command: string, remote command
    :param wait: integer, time to wait available ip of instances
    """
    with get_ssh_connection(instance1_ip, *instance_creds) as ssh:
        interm_transp = ssh.get_transport()
        try:
            logger.info('Opening channel between VMs {0} and {1}'.format(
                instance1_ip, instance2_ip))
            interm_chan = interm_transp.open_channel('direct-tcpip',
                                                     (instance2_ip, 22),
                                                     (instance1_ip, 0))
        except Exception as e:
            message = '{} Wait to update sg rules. Try to open channel again'
            logger.info(message.format(e))
            time.sleep(wait)
            interm_chan = interm_transp.open_channel('direct-tcpip',
                                                     (instance2_ip, 22),
                                                     (instance1_ip, 0))
        transport = paramiko.Transport(interm_chan)
        transport.start_client()

        logger.info("Passing authentication to VM")
        transport.auth_password(*instance_creds)
        channel = transport.open_session()
        channel.get_pty()
        channel.fileno()
        channel.exec_command(command)

        logger.debug("Receiving exit_code, stdout, stderr")
        result = {
            'stdout': channel.recv(1024),
            'stderr': channel.recv_stderr(1024),
            'exit_code': channel.recv_exit_status()
        }
        logger.debug('Command: {}'.format(command))
        logger.debug(pretty_log(result))

        logger.debug('Closing channel''')
        channel.close()

        return result


def get_role(os_conn, role_name):
    """Get role by name."""
    role_list = os_conn.keystone.roles.list()
    for role in role_list:
        if role.name == role_name:
            return role


def add_role_to_user(os_conn, user_name, role_name, tenant_name):
    """Assign role to user.

    :param os_conn: type object
    :param user_name: type string,
    :param role_name: type string
    :param tenant_name: type string
    """
    tenant_id = os_conn.get_tenant(tenant_name).id
    user_id = os_conn.get_user(user_name).id
    role_id = get_role(os_conn, role_name).id
    os_conn.keystone.roles.add_user_role(user_id, role_id, tenant_id)


def check_service(ip, commands):
    """Check that required nova services are running on controller.

    :param ip: ip address of node
    :param commands: type list, nova commands to execute on controller,
                     example of commands:
                     ['nova-manage service list | grep vcenter-vmcluster1']
    """
    ssh_manager = SSHManager()
    ssh_manager.check_call(ip=ip, command='source openrc')

    for cmd in commands:
        wait(lambda:
             ':-)' in ssh_manager.check_call(ip=ip, command=cmd).stdout[-1],
             timeout=200)


def create_instances(os_conn, nics, vm_count=1,
                     security_groups=None, available_hosts=None,
                     flavor_name='m1.micro'):
    """Create VMs on available hypervisors.

    :param os_conn: type object, openstack
    :param vm_count: type integer, count of VMs to create
    :param nics: type dictionary, neutron networks to assign to instance
    :param security_groups: list of security group names
    :param available_hosts: available hosts for creating instances
    :param flavor_name: name of flavor
    """
    def find_by_name(objects, name):
        for obj in objects:
            if obj.name == name:
                return obj

    # Get list of available images, flavors and hypervisors
    instances = []
    images = os_conn.nova.images.list()
    flavor = find_by_name(os_conn.nova.flavors.list(), flavor_name)

    if not available_hosts:
        available_hosts = os_conn.nova.services.list(binary='nova-compute')

    for host in available_hosts:
        image = find_by_name(images, zone_image_maps[host.zone])

        instance = os_conn.nova.servers.create(
            flavor=flavor,
            name='test_{0}'.format(image.name),
            image=image,
            min_count=vm_count,
            availability_zone='{0}:{1}'.format(host.zone, host.host),
            nics=nics, security_groups=security_groups)

        instances.append(instance)
    return instances


def verify_instance_state(os_conn, instances=None, expected_state='ACTIVE',
                          boot_timeout=300):
    """Verify that current state of each instance/s is expected.

    :param os_conn: type object, openstack
    :param instances: type list, list of created instances
    :param expected_state: type string, expected state of instance
    :param boot_timeout: type int, time in seconds to build instance
    """
    if not instances:
        instances = os_conn.nova.servers.list()
    for instance in instances:
        wait(lambda:
             os_conn.get_instance_detail(instance).status == expected_state,
             timeout=boot_timeout,
             timeout_msg='Timeout is reached. '
                         'Current state of VM {0} is {1}.'
                         'Expected state is {2}'.format(
                             instance.name,
                             os_conn.get_instance_detail(instance).status,
                             expected_state))


def create_access_point(os_conn, nics, security_groups, host_num=0):
    """Create access point.

    Creating instance with floating ip as access point to instances
    with private ip in the same network.

    :param os_conn: type object, openstack
    :param nics: type dictionary, neutron networks to assign to instance
    :param security_groups: list of security group names
    :param host_num: index of the host
    """
    # Get the host
    host = os_conn.nova.services.list(binary='nova-compute')[host_num]

    access_point = create_instances(  # create access point server
        os_conn=os_conn, nics=nics,
        vm_count=1,
        security_groups=security_groups,
        available_hosts=[host]).pop()

    verify_instance_state(os_conn)

    access_point_ip = os_conn.assign_floating_ip(
        access_point, use_neutron=True)['floating_ip_address']
    wait(lambda: tcp_ping(access_point_ip, 22), timeout=60 * 5, interval=5)
    return access_point, access_point_ip


def add_gateway_ip(os_conn, subnet_id, ip):
    """Add gateway ip for subnet."""
    os_conn.neutron.update_subnet(subnet_id, {'subnet': {'gateway_ip': ip}})


def remove_router_interface(os_conn, router_id, subnet_id):
    """Remove subnet interface from router."""
    os_conn.neutron.remove_interface_router(
        router_id, {"router_id": router_id, "subnet_id": subnet_id})
