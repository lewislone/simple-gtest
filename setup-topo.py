#!/usr/bin/python
#
# Use netem, network namespaces, and veth virtual NICs
# to run a multi-flow TCP test on a single Linux machine.
#
# There is one network namespace for each emulated host.
# The emulated hosts are as follows:
#
#   srv: server (sender)
#   srt: server router
#   mid: middle host to emulate delays and bandwidth constraints
#   crt: client router
#   cli: client (receiver)
#   cli2: client2 (receiver)
#
# Most hosts have both a left ("l") and right ("r") virtual NIC.
# The server has only an "r" NIC and the client has only an "l" NIC.
#
# The topology is as follows:
#
#   +-------+ +-------+ +-------+ +-------+ +-------+
#   |  srv  | |  srt  | |  mid  | |  crt  | |  cli  |
#   |     r +-+ l   r +-+ l   r +-+ l   r +-+ l     |
#   +-------+ +-------+ +-------+ +-------+ +-------+
#

import os
import os.path
import socket
import sys
import threading
import time

HOSTS = ['cli', 'cli2', 'crt', 'mid', 'srt', 'srv']


def run(cmd, verbose=True):
    if verbose:
        print('running: |%s|' % (cmd))
    status = os.system(cmd)
    if status != 0:
        sys.stderr.write('error %d executing: %s' % (status, cmd))

def cleanup():
    """Delete all veth pairs and all network namespaces."""
    for host in HOSTS:
        run('( ip netns exec %(host)s ip link del dev %(host)s.l; '
            '  ip netns exec %(host)s ip link del dev %(host)s.r; '
            '  ip netns del %(host)s ) 2> /dev/null'  % {'host' : host})

def setup_logging():
    """Set up all logging."""
    # Zero out /var/log/kern-debug.log so that we only get our test logs.
    run('logrotate -f /etc/logrotate.conf')
    # Set up BBR to log with printk to /var/log/kern-debug.log.
    run('echo Y > /sys/module/tcp_bbr2/parameters/debug_with_printk')
    run('echo 3 > /sys/module/tcp_bbr2/parameters/flags')

def setup_namespaces():
    """Set up all network namespaces."""
    for host in HOSTS:
        run('ip netns add %(host)s'  % {'host' : host})

def setup_loopback():
    """Set up loopback devices for all namespaces."""
    for host in HOSTS:
        run('ip netns exec %(host)s ifconfig lo up' % {'host' : host})

def setup_veth():
    """Set up all veth interfaces."""
    c = ''
    c += 'ip link add srv.r type veth peer name srt.l\n'
    c += 'ip link add srt.r type veth peer name mid.l\n'
    c += 'ip link add mid.r type veth peer name crt.l\n'
    c += 'ip link add crt.r type veth peer name cli.l\n'
    c += 'ip link add crt2.r type veth peer name cli2.l\n'

    c += 'ip link set dev srv.r netns srv\n'
    c += 'ip link set dev srt.r netns srt\n'
    c += 'ip link set dev srt.l netns srt\n'
    c += 'ip link set dev mid.r netns mid\n'
    c += 'ip link set dev mid.l netns mid\n'
    c += 'ip link set dev crt.l netns crt\n'
    c += 'ip link set dev crt.r netns crt\n'
    c += 'ip link set dev cli.l netns cli\n'
    c += 'ip link set dev crt2.r netns crt\n'
    c += 'ip link set dev cli2.l netns cli2\n'

    c += 'ip netns exec srv ip link set srv.r up\n'
    c += 'ip netns exec srt ip link set srt.r up\n'
    c += 'ip netns exec srt ip link set srt.l up\n'
    c += 'ip netns exec mid ip link set mid.r up\n'
    c += 'ip netns exec mid ip link set mid.l up\n'
    c += 'ip netns exec crt ip link set crt.r up\n'
    c += 'ip netns exec crt ip link set crt.l up\n'
    c += 'ip netns exec crt ip link set crt2.r up\n'
    c += 'ip netns exec cli ip link set cli.l up\n'
    c += 'ip netns exec cli2 ip link set cli2.l up\n'

    # Disable TSO, GSO, GRO, or else netem limit is interpreted per
    # multi-MSS skb, not per packet on the emulated wire.
    c += 'ip netns exec srt ethtool -K srt.r tso off gso off gro off\n'
    c += 'ip netns exec mid ethtool -K mid.l tso off gso off gro off\n'
    c += 'ip netns exec mid ethtool -K mid.r tso off gso off gro off\n'
    c += 'ip netns exec crt ethtool -K crt.l tso off gso off gro off\n'

    # server
    c += 'ip netns exec srv ip addr add 192.168.0.1/24 dev srv.r\n'

    # server router
    c += 'ip netns exec srt ip addr add 192.168.0.11/24 dev srt.l\n'
    c += 'ip netns exec srt ip addr add 192.168.1.1/24   dev srt.r\n'

    # mid
    c += 'ip netns exec mid ip addr add 192.168.1.11/24 dev mid.l\n'
    c += 'ip netns exec mid ip addr add 192.168.2.1/24   dev mid.r\n'

    # client router
    c += 'ip netns exec crt ip addr add 192.168.2.11/24 dev crt.l\n'
    c += 'ip netns exec crt ip addr add 192.168.3.1/24   dev crt.r\n'
    c += 'ip netns exec crt ip addr add 192.168.3.2/24   dev crt2.r\n'

    # client
    c += 'ip netns exec cli ip addr add 192.168.3.11/24 dev cli.l\n'
    # client2
    c += 'ip netns exec cli2 ip addr add 192.168.3.12/24 dev cli2.l\n'

    run(c)

def setup_routes():
    """Set up all routes."""
    c = ''

    # server
    c += 'h=srv\n'
    c += 'ip netns exec $h tc qdisc add dev $h.r root fq\n'
    c += 'ip netns exec $h ip route add default via 192.168.0.11 dev $h.r\n'

    # server router
    c += 'h=srt\n'
    c += 'ip netns exec $h ip route add default via 192.168.1.11 dev $h.r\n'

    # mid
    c += 'h=mid\n'
    c += 'ip netns exec $h ip route add 192.168.3.0/24 via 192.168.2.11\n'
    c += 'ip netns exec $h ip route add default via 192.168.1.1 dev $h.l\n'

    # client router
    c += 'h=crt\n'
    c += 'ip netns exec $h ip route add default via 192.168.2.1 dev $h.l\n'
    c += 'ip netns exec crt ip route add 192.168.3.12 via 192.168.3.2 dev crt2.r\n'

    # cli
    c += 'h=cli\n'
    c += 'ip netns exec $h ip route add default via 192.168.3.1 dev $h.l\n'

    # cli2
    c += 'h=cli2\n'
    c += 'ip netns exec $h ip route add default via 192.168.3.2 dev $h.l\n'

    run(c)

def setup_forwarding():
    """Enable forwarding in each namespace."""
    for host in HOSTS:
        run('ip netns exec %(host)s sysctl -q -w '
            'net.ipv4.ip_forward=1 '
            'net.ipv6.conf.all.forwarding=1'  % {'host' : host})

def main():
    """Main function to run everything."""
    cleanup()
    setup_namespaces()
    setup_loopback()
    setup_veth()
    setup_routes()
    setup_forwarding()
    return 0


if __name__ == '__main__':
    sys.exit(main())
