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
# Authors:
#  Neal Cardwell
#  Soheil Hassas Yeganeh
#  Kevin (Yudong) Yang
#  Arjun Roy

import os
import os.path
import socket
import sys
import threading
import time


def run(cmd, verbose=True):
    if verbose:
        print('running: |%s|' % (cmd))
    status = os.system(cmd)
    if status != 0:
        sys.stderr.write('error %d executing: %s' % (status, cmd))

def netem_limit(rate, delay, buf):
    """Get netem limit in packets.

    Needs to hold the packets in emulated pipe and emulated buffer.
    """
    bdp_bits = (rate * 1000000.0) * (delay / 1000.0)
    bdp_bytes = bdp_bits / 8.0
    bdp = int(bdp_bytes / 1500.0)
    limit = bdp + buf
    return limit

def get_params():
    # Invocations of this tool should set the following parameters as
    # environment variables.
    params = {
        'bw':          -1, # input bottleneck bw in Mbit/sec; required
        'rtt':         -1, # RTT in ms; required
        'buf':         -1, # input bottleneck buffer in packets; required
        'loss':         0, # input bottleneck loss rate in percent; optional
        'interval':     0, # interval between flow starts, in secs; optional
        'dur':         -1, # length of test in secs: required
        'outdir':      '', # output directory for results
        'qdisc':       '', # qdisc at downstream bottleneck (empty for FIFO)
        'cmd':         '', # command to run (e.g. set sysctl values)
        'pcap':         0, # bytes per packet to capture; 0 for no tracing
    }

    for key in params.keys():
        print('parsing key %s' % key)
        if key in os.environ:
           print('looking at env var with key %s, val %s' % (key, os.environ[key]))
        else:
           print('no env var with key %s' % (key))
        if key not in os.environ:
            if params[key] != 0:
              sys.stderr.write('missing %s in environment variables\n' % key)
              sys.exit(1)
        elif type(params[key]) == str:
            params[key] = os.environ[key]
        else:
            params[key] = float(os.environ[key])

    print(params)
    params['netperf'] = netperf()
    params['receiver_ip'] = '192.168.3.11'
    # 10Gbit/sec * 100ms is 125MBytes, so to tolerate
    # high loss rates and lots of SACKed data, we use
    # 512MByte socket send and receive buffers:
    params['mem'] = 536870912
    return params

def setup_netem(params):
    """Set up netem on the crt (client router) host."""

    d = {}

    # Parameters for data direction.
    d['IRATE']   = params['bw']      # Mbit/sec
    d['IDELAY']  = params['rtt'] / 2 # ms
    d['IBUF']    = params['buf']     # packets
    d['ILOSS']   = params['loss']
    d['IREO']    = 0  # TODO: not implemented yet
    d['ILIMIT'] = netem_limit(rate=d['IRATE'], delay=d['IDELAY'], buf=d['IBUF'])

    # Parameters for ACK direction.
    d['ORATE']  = 1000 # Mbit/sec; TODO: not implemented yet
    d['ODELAY'] = params['rtt'] / 2 # ms
    d['OBUF']   = 1000 # packets; TODO: not implemented yet
    d['OLOSS']  = 0  # TODO: not implemented yet
    d['OREO']   = 0  # TODO: not implemented yet
    d['OLIMIT'] = netem_limit(rate=d['ORATE'], delay=d['ODELAY'], buf=d['OBUF'])

    d['tc'] = TC_PATH

    c = ''

    d['INETEM_RATE'] = 'rate %(IRATE)sMbit' % d

    # Inbound from sender -> receiver. Downstream rate limiting is on mid.l.
    d['host'] = 'mid'
    c += ('ip netns exec %(host)s '
          '%(tc)s qdisc add dev %(host)s.r root netem '
          'limit %(ILIMIT)s delay %(IDELAY)sms %(IREO)sms '
          'loss random %(ILOSS)s%% %(INETEM_RATE)s\n') % d

    # Outbound from receiver -> sender.
    d['host'] = 'mid'
    c += ('ip netns exec %(host)s '
          '%(tc)s qdisc add dev %(host)s.l root netem '
          'limit %(OLIMIT)s delay %(ODELAY)sms %(OREO)sms '
          'loss random %(OLOSS)s%% '
          'rate %(ORATE)sMbit\n') % d

    c += ('ip netns exec %(host)s %(tc)s -stat qdisc show\n') % d

    run(c)

def main():
    params = get_params()
    setup_netem(params)
    return 0


if __name__ == '__main__':
    sys.exit(main())
