#!/usr/bin/python

import xmlrpclib
from optparse import OptionParser, OptionValueError
import sys
import getpass
import socket

# Reference
# http://jmrodri.fedorapeople.org/cobbler-integration.pdf

def cobbler_create(server, token, host):
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
        r = server.sync(token)
        print r
        return True
    except xmlrpclib.Fault, e:
        print "Failed to create system %s: %s" % (host['hostname'], str(e))
        return False

def cobbler_rename(server, token, host):
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
        print "Failed to rename system %s: %s" % (host['hostname'], str(e))
        return False

def cobbler_export(server, token, host):
    pass

def cobbler_import(server, token, host):
    pass

def cobbler_remove(server, token, host):
    try:
        server.remove_system(host['hostname'], token)
        return True
    except xmlrpclib.Fault, e:
        print "Failed to remove system %s: %s" % (host['hostname'], str(e))
        return False

def connect(url):
    try:
        server = xmlrpclib.Server(url)
        server.ping()
        return server
    except:
        traceback.print_exc()
        return None

def cobbler_login(server, user, passwd):
    protos = ['http', 'https']
    for p in protos:
        cobbler_url = '%s://%s/cobbler_api' % (p, server)
        server = connect(cobbler_url)
        if server is not None:
            break
    if server is None:
        print "Failed to connect to %s" % cobbler_url
        return (None, None)
    try:
        token = server.login(user, passwd)
    except xmlrpclib.Fault, e:
        print "Login to %s failed: %s" % (cobbler_url, str(e))
        return (None, None)
    return (server, token)

def main(args):
    parser = OptionParser()
    parser.add_option('-v', '--verbose', action='store_true',
                      help='Be verbose')
    parser.add_option('-x', '--action', metavar='ACTION',
                      choices=['create', 'rename', 'backup', 'restore', 'remove'],
                      help='cobbler action')
    parser.add_option('-s', '--server', type='string',
                      help='cobbler server to connect to')
    parser.add_option('-H', '--hostname', type='string',
                      help='Name of system')
    parser.add_option('-N', '--newname', type='string',
                      help='New name of system in case of rename action')
    parser.add_option('-m', '--macaddress', type='string', metavar='MACADDR',
                      help='macaddress of host')

    parser.add_option('-P', '--profile', type='string', metavar='PROFILE',
                      help='cobbler profile')
    parser.add_option('-u', '--username', type='string', metavar='USER',
                      help='cobbler user')
    parser.add_option('-p', '--password', type='string', metavar='PASSWORD',
                      help='cobbler user password')
    (options, args) = parser.parse_args(args)
    if not options.server:
        print "Need cobbler server to connect to"
        return 1
    if not options.username:
        options.username = getpass.getuser()
    if not options.password:
        options.password = getpass.getpass()
    cobbler, token = cobbler_login(options.server, options.username, options.password)
    if cobbler is None:
        return 1
    host = { 'hostname': options.hostname,
            'macaddress': options.macaddress,
            'profile': options.profile,
            'ipaddress': '' }
    r = True
    if options.action == 'create':
        r = cobbler_create(cobbler, token, host)
    elif options.action == 'rename':
        host['newname'] = options.newname
        r = cobbler_rename(cobbler, token, host)
    elif options.action == 'export':
        print "Not supported"
    elif options.action == 'import':
        print "Not supported"
    elif options.action == 'remove':
        r = cobbler_remove(cobbler, token, host)
    return int(not r)

if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt, e:
        print >> sys.stderr, "Exit on user request."
        sys.exit(1)
