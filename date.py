#!/usr/bin/python
import os
import os.path
import socket
import sys
import time
import re
#from matplotlib.pyplot import *


def parse_data():
    buffer=[1, 7]
    rtt2=[0,  40]
    CC=["orgbbr"]
    tp={}
    tp["orgbbr-litter-rtt"] = {}
    tp["orgbbr-long-rtt"] = {}

    for cc in CC:
        for rtt in rtt2:
            for buf in buffer:
                tp["orgbbr-litter-rtt"][str(rtt)] = {}
                #tp["bbr-litter-rtt"][str(rtt)][str(buf)] = {}
                tp["orgbbr-long-rtt"][str(rtt)] = {}
                #tp["bbr-long-rtt"][str(rtt)][str(buf)] = {}
    print tp
    
    for cc in CC:
        for rtt in rtt2:
            for buf in buffer:
                outfile = "out/%s_coexist-litte-rtt-%d-buf-%.1f.log" % (cc, rtt, buf)
                print outfile
                fp = open(outfile, "r")
                next(fp)
                for line in fp:
                    tp["orgbbr-litter-rtt"][str(rtt)][str(buf)]=float(line.split('=')[1])
                    break

                outfile = "out/%s_coexist-largh-rtt-%d-buf-%.1f.log" % (cc, rtt, buf)
                print outfile
                fp = open(outfile, "r")
                next(fp)
                for line in fp:
                    tp["orgbbr-long-rtt"][str(rtt)][str(buf)]=float(line.split('=')[1])
                    break
    print tp
    return tp


if __name__ == '__main__':

    data = parse_data()
    print len(data)
    for item in data:
        #cwnd = [int(cwnd) for cwnd in stream['cwnd']]
        #ssthresh = [int(ssthresh) for ssthresh in stream['ssthresh']]
        #rtt = [float(rtt) for rtt in stream['rtt']]
        #ca_state = [int(ca_state) for ca_state in stream['ca_state']]
        #reordering = [int(reordering) for reordering in stream['reordering']]
        print item 

        ###cwnd 
        #grid(True)
        #ylabel('cwnd', fontdict={'fontsize':20})
        #xlabel('time(s)', fontdict={'fontsize':20})
        #plot(range(len(cwnd)), ssthresh, 'go:', linewidth=2, label='ssh')
        #plot(range(len(cwnd)), cwnd, 'ro:', linewidth=2, label='cwnd')
        ##plot(range(len(rtt)), rtt, 'yo:', linewidth=2, label='rtt')
        #plot(range(len(ca_state)), ca_state, 'bo:', linewidth=2, label='ca_state')
        #plot(range(len(reordering)), reordering, 'co:', linewidth=2, label='reordering')
        #legend(title=cap_file + "(cwnd)", loc='best')
        ##savefig('ack_timestamp.png')
        #show()

