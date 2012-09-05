#!/usr/bin/python

# Written by Stephen Fromm <stephenf nero net>
# (C) 2012 University of Oregon
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import xmlrpclib
from optparse import OptionParser, OptionValueError
import sys
import getpass
import socket

__version__ = '0.2'

# References
# https://github.com/cobbler/cobbler/wiki/XMLRPC
# http://jmrodri.fedorapeople.org/cobbler-integration.pdf

def system_exists(name, server):
    try:
        system = server.find_system({'name': name})
        if len(system) > 0:
            return True
        else:
            return False
    except xmlrpclib.Fault, e:
        sys.stderr.write("Failed to lookup system %s: %s\n" % (name, str(e)))
        return False

def profile_exists(name, server):
    try:
        p = server.find_profile({'name': name})
        if len(p) > 0:
            return True
        else:
            return False
    except xmlrpclib.Fault, e:
        sys.stderr.write("Failed to lookup profile %s: %s\n" % (name, str(e)))
        return False

def cobbler_register_system(host, server):
    netinfo = {}
    reg_info = {}
    netinfo['eth0'] = {
        'ip_address'  : host['ipaddress'],
        'mac_address' : host['macaddress']
    }
    reg_info['name'] = host['hostname']
    reg_info['hostname'] = host['hostname']
    reg_info['profile'] = host['profile']
    reg_info['interfaces'] = netinfo
    sys.stderr.write("Unable to set netboot_enabled due to unauthenticated session.\n")
    try:
        server.register_new_system(reg_info)
        return True
    except xmlrpclib.Fault, e:
        sys.stderr.write("Failed to register system %s: %s\n" % (host['hostname'], str(e)))
        return False

def cobbler_modify(host, server, token):
    try:
        sys_id = server.get_system_handle(host['hostname'], token)
        server.modify_system(sys_id, 'netboot_enabled', True, token)
        server.modify_system(sys_id, 'modify_interface', {
            'dnsname-eth0'    : host['hostname'],
            'ipaddress-eth0'  : host['ipaddress'],
            'macaddress-eth0' : host['macaddress']
            }, token)
        server.modify_system(sys_id, 'profile', host['profile'], token)
        server.save_system(sys_id, token)
        return True
    except xmlrpclib.Fault, e:
        sys.stderr.write("Failed to modify system %s: %s\n" % (host['hostname'], str(e)))
        return False

def cobbler_create(host, server, token=None):
    if token is None:
        return cobbler_register_system(host, server)
    if not profile_exists(host['profile'], server):
        sys.stderr.write("Failed to lookup profile %s\n" % profile)
        return False
    if system_exists(host['hostname'], server):
        sys.stderr.write("System %s already registered; will modify existing system.\n" % host['hostname'])
        return cobbler_modify(host, server, token)
    try:
        sys_id = server.new_system(token)
        server.modify_system(sys_id, 'name', host['hostname'], token)
        server.modify_system(sys_id, 'hostname', host['hostname'], token)
        server.modify_system(sys_id, 'netboot_enabled', True, token)
        server.modify_system(sys_id, 'modify_interface', {
            'dnsname-eth0'    : host['hostname'],
            'ipaddress-eth0'  : host['ipaddress'],
            'macaddress-eth0' : host['macaddress']
            }, token)
        server.modify_system(sys_id, 'profile', host['profile'], token)
        server.save_system(sys_id, token)
        server.sync(token)
        return True
    except xmlrpclib.Fault, e:
        sys.stderr.write("Failed to create system %s: %s\n" % (host['hostname'], str(e)))
        return False

def cobbler_rename(server, token, host):
    if token is None:
        sys.stderr.write("Cannot rename without authenticated session")
        return False
    try:
        sys_id = server.get_system_handle(host['hostname'], token)
        server.rename_system(sys_id, host['newname'], token)
        sys_id = server.get_system_handle(host['newname'], token)
        server.modify_system(sys_id, 'hostname', host['newname'], token)
        server.modify_system(sys_id, 'modify_interface', {
            'dnsname-eth0'    : host['newname'],
            }, token)
        r = server.sync(token)
        return True
    except xmlrpclib.Fault, e:
        sys.stderr.write("Failed to rename system %s: %s\n" % (host['hostname'], str(e)))
        return False

def cobbler_export(server, token, host):
    pass

def cobbler_import(server, token, host):
    pass

def cobbler_remove(host, server, token):
    if host['hostname'] is None:
        sys.stderr.write("Require hostname argument.\n")
        return False
    if not system_exists(host['hostname'], server):
        sys.stderr.write("System %s does not exist in cobbler.\n" % host['hostname'])
        return False
    try:
        server.remove_system(host['hostname'], token)
        server.sync(token)
        return True
    except xmlrpclib.Fault, e:
        sys.stderr.write("Failed to remove system %s: %s\n" % (host['hostname'], str(e)))
        return False

def connect(url):
    try:
        server = xmlrpclib.Server(url)
        server.ping()
        return server
    except:
        traceback.print_exc()
        return None

def cobbler_login(remote, user, passwd):
    protos = ['http', 'https']
    server = None
    token = None
    for p in protos:
        cobbler_url = '%s://%s/cobbler_api' % (p, remote)
        server = connect(cobbler_url)
        if server is not None:
            break
    if server is None:
        sys.stderr.write("Failed to connect to %s\n" % cobbler_url)
        return (None, None)
    if user is not None:
        try:
            token = server.login(user, passwd)
        except xmlrpclib.Fault, e:
            sys.stderr.write("Login to %s failed: %s\n" % (cobbler_url, str(e)))
            return (None, None)
        except TypeError, e:
            sys.stderr.write("Login to %s failed: %s\n" % (cobbler_url, str(e)))
            return (None, None)
    return (server, token)

def cobbler_getks(server, **kwargs):
    profile = kwargs['profile']
    system = kwargs['system']
    if profile:
        if not profile_exists(profile, server):
            sys.stderr.write("Failed to lookup profile %s\n" % profile)
            return False
    if system:
        if not system_exists(system, server):
            sys.stderr.write("Failed to lookup system %s\n" % system)
            return False
    try:
        print server.generate_kickstart(profile, system)
    except xmlrpclib.Fault, e:
        sys.stderr.write("Failed to generate kickstart: %s\n" % (str(e)))
        return False
    return True

def main(args):
    parser = OptionParser(version=__version__)
    parser.add_option('-v', '--verbose', action='store_true',
                      help='Be verbose')
    parser.add_option('-x', '--action', metavar='ACTION',
                      choices=['create', 'rename', 'backup', 'restore', 'remove', 'getks'],
                      help='cobbler action')
    parser.add_option('-s', '--server', type='string',
                      help='cobbler server to connect to')
    parser.add_option('-H', '--hostname', type='string',
                      help='Name of system')
    parser.add_option('-N', '--newname', type='string',
                      help='New name of system in case of rename action')
    parser.add_option('-i', '--ipaddress', type='string',
                      metavar='IPADDR', default='',
                      help='ip address of host')
    parser.add_option('-m', '--macaddress', type='string', metavar='MACADDR',
                      help='macaddress of host')

    parser.add_option('-P', '--profile', type='string', metavar='PROFILE',
                      help='cobbler profile')
    parser.add_option('-u', '--username', type='string', metavar='USER',
                      help='Cobbler user.  '
                          + 'If no user argument provided, will try '
                          + 'to register system.  This requires register_new_installs'
                          + ' set to true in cobbler settings.')
    parser.add_option('-p', '--password', type='string', metavar='PASSWORD',
                      help='Cobbler user password')
    (options, args) = parser.parse_args(args)
    if not options.server:
        sys.stderr.write("Need cobbler server to connect to.\n")
        return 1
    if options.username and not options.password:
        options.password = getpass.getpass()
    cobbler, token = cobbler_login(options.server, options.username, options.password)
    if cobbler is None:
        return 1
    host = { 'hostname': options.hostname,
            'macaddress': options.macaddress,
            'profile': options.profile,
            'ipaddress': options.ipaddress }
    r = True
    if options.action == 'create':
        r = cobbler_create(host, cobbler, token)
    elif options.action == 'rename':
        host['newname'] = options.newname
        r = cobbler_rename(host, cobbler, token)
    elif options.action == 'export':
        print "Not supported"
    elif options.action == 'import':
        print "Not supported"
    elif options.action == 'remove':
        r = cobbler_remove(host, cobbler, token)
    elif options.action == 'getks':
        kwargs = { 'system': '', 'profile': '' }
        if options.hostname:
            kwargs['system'] = options.hostname
        elif options.profile:
            kwargs['profile'] = options.profile
        else:
            parser.error("Require --hostname or --profile when used with getks action")
        r = cobbler_getks(cobbler, **kwargs)
    return int(not r)

if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt, e:
        print >> sys.stderr, "Exit on user request."
        sys.exit(1)
