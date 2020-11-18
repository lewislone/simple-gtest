#!/usr/bin/python
import os
import os.path
import socket
import sys
import threading
import time
import config
import setupnetem

params = config.params
SS_PATH = '/root/iproute2/misc/ss'
TC_PATH = '/root/iproute2/tc/tc'

def bdp_pkts(bw, rtt, bdp_of_buf):
    return int(bw*1000*1000*rtt/1000.0 / (1514 * 8) * bdp_of_buf) 

def netperf():
    if os.path.isfile('./netperf'):
        return './netperf'
    else:
        return '/usr/local/bin/netperf'

def netserver():
    if os.path.isfile('./netserver'):
        return './netserver'
    else:
        return '/usr/local/bin/netserver'

def run(cmd, verbose=True):
    if verbose:
        print('running: |%s|' % (cmd))
    status = os.system(cmd)
    if status != 0:
        sys.stderr.write('error %d executing: %s' % (status, cmd))

def setup():
    run('./clean.py')
    run('./setup-topo.py')


def prepare():
    # Set up receiver process.
    run('pkill -f netserver')
    run('pkill -f netserver')
    run('ip netns exec cli %s -N' % (netserver()))
    run('ip netns exec cli2 %s -N' % (netserver()))

    # Set up output directory.
    outdir = params['outdir']
    run('mkdir -p %s' % outdir)

def bbr_coexist():
    buffer=[0.5, 1, 1.5, 2, 3, 4, 5, 7]
    rtt2=[10, 20, 30, 40, 50, 60, 70, 100]
    CC=["bbrv2", "oldbbr"]
    
    for cc in CC:
        for rtt in rtt2:
            for buf in buffer:
                params['cc'] = cc 
                params['mem']=536870912
                params['rtt2'] = rtt
                params['buf'] = bdp_pkts(params['bw'], params['rtt'], buf)
                params['netperf'] = netperf()

                setup()
                prepare()
                setupnetem.netem(params)

                params['receiver_ip'] = '192.168.3.11'
                params['port'] = 10000 
                params['outfile'] = "out/%s_coexist-litte-rtt-%d-buf-%.1f.log" % (params['cc'], rtt, buf)

                run('ip netns exec srv %(netperf)s '
                    '-l %(dur)d -H %(receiver_ip)s -- -k THROUGHPUT '
                    '-s %(mem)s,%(mem)s -S %(mem)s,%(mem)s '
                    '-K %(cc)s -P %(port)s '
                    '> %(outfile)s &' % params)

                params['receiver_ip'] = '192.168.3.12'
                params['port'] = 10001
                params['outfile'] = "out/%s_coexist-largh-rtt-%d-buf-%.1f.log" % (params['cc'], rtt, buf)

                run('ip netns exec srv %(netperf)s '
                    '-l %(dur)d -H %(receiver_ip)s -- -k THROUGHPUT '
                    '-s %(mem)s,%(mem)s -S %(mem)s,%(mem)s '
                    '-K %(cc)s -P %(port)s '
                    '> %(outfile)s' % params)

if __name__ == '__main__':
    sys.exit(bbr_coexist())
