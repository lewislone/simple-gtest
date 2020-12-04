#!/usr/bin/python
import os
import os.path
import socket
import sys
import threading
import time

params={}
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

def iperf():
    return '/usr/bin/iperf3'

def run(cmd, verbose=True):
    if verbose:
        print('running: |%s|' % (cmd))
    status = os.system(cmd)
    if status != 0:
        sys.stderr.write('error %d executing: %s' % (status, cmd))

def ss_log_thread(params):
    """Repeatedly run ss command and append log to file."""
    ss_log_path = "out/ss-%s_coexist-%s-rtt.log" % (params['cc'],params['type'])
    receiver_ip = params['receiver_ip']
    dur = params['dur']

    t0 = time.time()
    t = t0
    f = open(ss_log_path, 'w')
    f.truncate()
    f.close()
    ss_cmd = ('ip netns exec h1 '
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
    CC=["bbr", "testbbr"]
    
    for cc in CC:
    	# Set up output directory.
    	run('mkdir -p out')

    	run('sysctl -w net.ipv4.tcp_congestion_control=%s' % cc)

    	# Set up receiver process.
    	run('pkill -f iperf3')
    	run('ip netns exec h2 %s -s -i 1 -p 2222 > out/%s_coexist_little-rtt_server.log &' % (iperf(), cc))
    	run('ip netns exec h2 %s -s -i 1 -p 3333 > out/%s_coexist_large-rtt_server.log &' % (iperf(), cc))
    	#run('ip netns exec h1 tcpdump -i any tcp -w rtt.pcap&')

        params['receiver_ip'] = '10.0.5.2'
        params['dur'] = 60
        params['cc'] = cc 
        params['senter_ip'] = '10.0.1.1'
        params['type'] = 'little' 
        params['port'] = 2222 
        params['outfile'] = "out/%s_coexist-litte-client.log" % (cc)
        ss1 = launch_ss(params)

        run('ip netns exec h1 iperf3 '
            '-B %(senter_ip)s -c %(receiver_ip)s -p %(port)d -t %(dur)d'
            ' > %(outfile)s &' % params)


        params['senter_ip'] = '10.0.3.1'
        params['port'] = 3333 
        params['outfile'] = "out/%s_coexist-large-rtt-client.log" % (params['cc'])
        params['type'] = 'large' 
        ss2 = launch_ss(params)

        run('ip netns exec h1 iperf3 '
            '-B %(senter_ip)s -c %(receiver_ip)s -p %(port)d -t %(dur)d'
            ' > %(outfile)s' % params)

        ss1.join()
        ss2.join()

    	run('pkill -f iperf3')

if __name__ == '__main__':
    sys.exit(bbr_coexist())
