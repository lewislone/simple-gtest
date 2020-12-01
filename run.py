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
SS_INTERVAL_SECONDS = 0.1  # gather 'ss' stats each X seconds

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
    run('ip netns exec cli tcpdump -i any tcp and port 10000 -w little-rtt.pcap&')
    run('ip netns exec cli2 tcpdump -i any tcp and port 10001 -w largh-rtt.pcap&')

    # Set up output directory.
    outdir = params['outdir']
    run('mkdir -p %s' % outdir)

def ss_log_thread(params):
    """Repeatedly run ss command and append log to file."""
    ss_log_path = "out/ss-%s_coexist-%s-rtt-%d-buf-%.1f.log" % (params['cc'],params['type'], params['rtt2'], params['bdp'])
    receiver_ip = params['receiver_ip']
    dur = params['dur']

    t0 = time.time()
    t = t0
    f = open(ss_log_path, 'w')
    f.truncate()
    f.close()
    ss_cmd = ('ip netns exec srv '
              '%s -tinm "dport == :%d and dst %s" >> %s' % (
                  SS_PATH, params['port'], params['receiver_ip'], ss_log_path))

    while t < t0 + dur:
        f = open(ss_log_path, 'a')
        f.write('# %f\n' % (time.time(),))
        f.close()
        run(ss_cmd, verbose=False)
        t += SS_INTERVAL_SECONDS
        to_sleep = t - time.time()
        if to_sleep > 0:
            time.sleep(to_sleep)

def launch_ss(params):
    t = threading.Thread(target=ss_log_thread, args=(params,))
    t.start()
    return t

def bbr_coexist():
    buffer=[1, 2, 10]
    rtt2=[10, 30, 60]
    CC=["bbr"]
    
    for cc in CC:
        for rtt in rtt2:
            for buf in buffer:
                params['cc'] = cc 
                params['mem']=536870912
                params['rtt2'] = rtt
                params['buf'] = bdp_pkts(params['bw'], params['rtt'], buf)
                params['netperf'] = netperf()
                params['bdp'] = buf 

                setup()
                prepare()
                setupnetem.netem(params)

                params['receiver_ip'] = '192.168.3.11'
                params['type'] = 'litte' 
                params['port'] = 10000 
                params['outfile'] = "out/%s_coexist-litte-rtt-%d-buf-%.1f.log" % (params['cc'], rtt, buf)
                ss1 = launch_ss(params)

                run('ip netns exec srv %(netperf)s '
                    '-l %(dur)d -H %(receiver_ip)s -- -k THROUGHPUT '
                    '-s %(mem)s,%(mem)s -S %(mem)s,%(mem)s '
                    '-K %(cc)s -P %(port)s '
                    '> %(outfile)s &' % params)

                time.sleep(3)

                params['receiver_ip'] = '192.168.3.12'
                params['port'] = 10001
                params['outfile'] = "out/%s_coexist-largh-rtt-%d-buf-%.1f.log" % (params['cc'], rtt, buf)
                params['type'] = 'largh' 
                ss2 = launch_ss(params)

                run('ip netns exec srv %(netperf)s '
                    '-l %(dur)d -H %(receiver_ip)s -- -k THROUGHPUT '
                    '-s %(mem)s,%(mem)s -S %(mem)s,%(mem)s '
                    '-K %(cc)s -P %(port)s '
                    '> %(outfile)s' % params)
                ss1.join()
                ss2.join()
                run('cat out/%s_coexist-litte-rtt-%d-buf-%.1f.log' % (params['cc'], rtt, buf))
                run('cat out/%s_coexist-largh-rtt-%d-buf-%.1f.log' % (params['cc'], rtt, buf))

if __name__ == '__main__':
    sys.exit(bbr_coexist())
