#!/usr/bin/python
#coding: UTF-8
import os
import re
import sys
from matplotlib.pyplot import *

def find_item(source, item_name, default):
    filter = item_name+':(\d*) '
    value = re.findall(filter, source, re.S)
    if len(value) > 0:
        return value[0]
    else:
        return default

def search_stream(streams, local, peer):
    for stream in streams:
        if stream['local'] == local and stream['peer'] == peer:
            return stream
    return False

'''
# 1606181833.158366
State Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
ESTAB 0      315788   192.168.0.1:10000 192.168.3.11:10000
         skmem:(r0,rb425984,t0,tb425984,f110452,w340108,o0,bl0,d0) bbr wscale:2,2 rto:214 rtt:13.188/0.389 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:226 bytes_sent:460588 bytes_acked:254849 segs_out:321 segs_in:95 data_segs_out:319 bbr:(bw:90785848bps,mrtt:10.451,pacing_gain:2.88672,cwnd_gain:2.88672) send 198512587bps lastrcv:47 pacing_rate 259452480bps delivery_rate 90786304bps delivered:177 busy:47ms rwnd_limited:7ms(14.9%) unacked:143 rcv_space:14480 rcv_ssthresh:65535 notsent:110048 minrtt:10.451
'''

def parse_file(f):
        set = 1 
        sp = '/'
        one_case = 0 
        streams = []
        line = f.readline()
        while line:
            ##one set
            if len(line) == 20:#time: # 1606181833.158366 
                time = line[2:]
            
                line = f.readline() #skip title:State Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
                line = f.readline()
                if len(line) == 20:#time: # 1606181833.158366 
                    one_case = 0
                    continue

                while line and len(line) != 20:
                    new = 0 
                    one_case = one_case + 1
                    if one_case == 1:#ESTAB 0      315788   192.168.0.1:10000 192.168.3.11:10000
                        '''ID'''
                        value = line.split()
                        (stat, recvq, sendq, local, peer) = value 
                        print local,peer
                        stream = search_stream(streams, local, peer)
                        if stream is False:
                            stream = {}
                            stream['id'] = 0
                            stream['local'] = local
                            stream['peer'] = peer
                            stream['recvq'] = [] 
                            stream['sendq'] = [] 
                            stream['recvq'].append(recvq)
                            stream['sendq'].append(sendq) 
                            stream['cwnd'] = []
                            stream['bw'] = []
                            stream['rto'] = []
                            stream['rtt'] = []
                            stream['mrtt'] = []
                            stream['minrtt'] = []
                            stream['delivery_rate'] = []
                            stream['pacing_rate'] = []
                            stream['reordering'] = []
                            new = 1
                        else:
                            stream['id'] += 1 
                            stream['recvq'].append(recvq)
                            stream['sendq'].append(sendq) 
                    elif one_case == 2: 
                    #skmem:(r0,rb425984,t0,tb425984,f110452,w340108,o0,bl0,d0) bbr wscale:2,2 rto:214 rtt:13.188/0.389 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:226 bytes_sent:460588 bytes_acked:254849 segs_out:321 segs_in:95 data_segs_out:319 bbr:(bw:90785848bps,mrtt:10.451,pacing_gain:2.88672,cwnd_gain:2.88672) send 198512587bps lastrcv:47 pacing_rate 259452480bps delivery_rate 90786304bps delivered:177 busy:47ms rwnd_limited:7ms(14.9%) unacked:143 rcv_space:14480 rcv_ssthresh:65535 notsent:110048 minrtt:10.451
                        items = line.split()
                        one_case = 0
                        reordering = 0
                        for i,item in enumerate(items):
                            if item.find(":") > 0:
                                if item[:3] == "bbr":
                                    if len(item) > 35:
                                        (bw,mrtt,pacing_gain,cwnd_gain) = item.split(",")
                                        stream['bw'].append(bw.split(":")[2][:-3])
                                        stream['mrtt'].append(mrtt.split(":")[1])
                                else:
                                    (key,value) = item.split(":")
                            else:
                                key = item
                            if(key == "skmem"):
                                stream['cc'] = items[i+1]
                            if(key == "rto"):
                                stream['rto'].append(value) 
                            if(key == "cwnd"):
                                stream['cwnd'].append(value)
                            if(key == "pacing_rate"):
                                stream['pacing_rate'].append(items[i+1][:-3])
                            if(key == "delivery_rate"):
                                stream['delivery_rate'].append(items[i+1][:-3])
                            if(key == "minrtt"):
                                stream['minrtt'].append(value)
                            if(key == "rtt"):
                                (rtt,mdevrtt) = value.split("/")
                                stream['rtt'].append(rtt)
                            if(key == "reordering"):
                                reordering = value
                        stream['reordering'].append(reordering)

                    if new == 1:
                        streams.append(stream)
                    line = f.readline()

        f.close()
        return streams

if __name__ == '__main__':

    log_file = sys.argv[1]
    if not os.path.exists(log_file):
        print log_file + " not exist"
        exit() 

    f = file(log_file)
    streams = parse_file(f)
    stream = {}
    for stream in streams:
        cwnd = [int(cwnd) for cwnd in stream['cwnd']]
        minrtt = [float(minrtt) for minrtt in stream['minrtt']]
        rtt = [float(rtt) for rtt in stream['rtt']]
        mrtt = [float(mrtt) for mrtt in stream['mrtt']]
        bw = [int(bw)/8.0/1024/1024 for bw in stream['bw']]
        pacing_rate = [int(pacing_rate)/8.0/1024/1024 for pacing_rate in stream['pacing_rate']]
        delivery_rate = [int(delivery_rate)/8.0/1024/1024 for delivery_rate in stream['delivery_rate']]
        reordering = [int(reordering) for reordering in stream['reordering']]

        ##cwnd 
        grid(True)
        ylabel('cwnd', fontdict={'fontsize':20})
        xlabel('time(s)', fontdict={'fontsize':20})
        #plot(range(len(mrtt)), mrtt, 'go:', linewidth=2, label='mrtt')
        #plot(range(len(cwnd)), cwnd, 'ro:', linewidth=2, label='cwnd')
        #plot(range(len(rtt)), rtt, 'yo:', linewidth=2, label='rtt')
        #plot(range(len(bw)), bw, 'bo:', linewidth=2, label='bw')
        #plot(range(len(reordering)), reordering, 'co:', linewidth=2, label='reordering')
        #plot(range(len(pacing_rate)), pacing_rate, 'co:', linewidth=2, label='pacing_rate')
        plot(range(len(delivery_rate)), delivery_rate, 'go:', linewidth=2, label='delivery_rate')
        legend(title=log_file + "(cwnd)", loc='best')
        #savefig('ack_timestamp.png')
        show()
