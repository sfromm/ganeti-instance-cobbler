ganeti-instance-cobbler
=======================

This is a guest OS definition for [Ganeti][].  It will communicate with [Cobbler][]
to create an instance based on a profile defined in [Cobbler][].  This
only works if you already have [Cobbler][] already installed and
accessible from the node where the [Ganeti][] instance will run.

Installation
------------

In order to install this package from source, you need to determine what
options ganeti itself has been configured with. If ganeti was built
directly from source, then the only place it looks for OS definitions is
*/srv/ganeti/os*, and you need to install the OS under it:

    ./configure --prefix=/usr --localstatedir=/var \
        --sysconfdir=/etc \
        --with-os-dir=/srv/ganeti/os
    make && make install

If ganeti was installed from a package, its default OS path should
already include /usr/share/ganeti/os, so you can just run::

    ./configure -prefix=/usr --localstatedir=/var \
        --sysconfdir=/etc
    make && make install

Note that you need to repeat this procedure on all nodes of the cluster.

The actual path that ganeti has been installed with can be determined by
looking for a file named *_autoconf.py* under a ganeti directory in the
python modules tree (e.g.  */usr/lib/python2.4/site-packages/ganeti/_autoconf.py*).
In this file, a variable named *OS_SEARCH_PATH* will list all the directories in
which ganeti will look for OS definitions.

Configuration of instance creation
----------------------------------

The kind of instance created can be customized via a settings file. This
file may or may not be installed by default, as the instance creation will work
without it. The creation scripts will look for it in
*$sysconfdir/default/ganeti-instance-cobbler*, so if you have run
configure with the parameter *--sysconfdir=/etc*, the final filename
will be */etc/default/ganeti-instance-cobbler*.

The following settings will be examined in this file (see also the file
named 'defaults' in the source distribution for more details):

- COBBLER_SERVER:  The name of the server that cobbler runs on.  The URL
                   http://<servername>/cobbler_api must be accessible
                   from the node the instance will be created on.
- COBBLER_PROFILE: The name of the [Cobbler][] profile to base the
                   instance on.
- COBBLER_USER:    The name of the user to authenticate as for XMLRPC
                   interaction with cobler.  You can opt to not
                   authenticate as a user, but you will be unable to set
                   the netboot_enabled flag for a new system.  This
                   means the instance will not pxeboot and kickstart.
                   If you do not want to authenticate, you must set
                   *register_new_installs: 1* in
                   */etc/cobbler/settings*.
- COBBLER_PASS:    The password for the cobbler user to authenticate as.

Note that the settings file is important on the node that the instance
is installed on, not the cluster master. This is indeed not a very good
model of using this OS but currently the OS interface in ganeti is
limiting.

Further, please note that installation via cobbler will require that the
instance boot from the network for the first time.  The hypervisor's
*boot_order* can be set accordingly when creating the instance or
changed after install.

### Customization of the instance

All customization of the instance should be configured in [Cobbler][].
This ganeti os definition does not support direct customization of the
instance.  There are other tools better suited for that job, including
[Cobbler][].

Instance notes
--------------

All customization of the instance is done by [Cobbler][].  [Cobbler][]
accomplishes this with templating, snippets, and other measures.  When
creating the instance, the hypervisor parameter *boot_order* should be
set so that the instance will boot from the network.  One possible
configuration would be:  *boot_order=cn*.  This would try to boot from
the disk first and then from the network.


[Ganeti]: http://code.google.com/p/ganeti
[Cobbler]: http://cobbler.github.com/

<!-- vim: set textwidth=72 filetype=markdown -->
