#!/usr/bin/python
import os
import sys


#params = {
#    'bw':          -1, # input bottleneck bw in Mbit/sec; required
#    'rtt':         -1, # RTT in ms; required
#    'buf':         -1, # input bottleneck buffer in packets; required
#    'loss':         0, # input bottleneck loss rate in percent; optional
#    'interval':     0, # interval between flow starts, in secs; optional
#    'dur':         -1, # length of test in secs: required
#    'outdir':      '', # output directory for results
#    'qdisc':       '', # qdisc at downstream bottleneck (empty for FIFO)
#    'cmd':         '', # command to run (e.g. set sysctl values)
#    'pcap':         0, # bytes per packet to capture; 0 for no tracing
#}

def bdp_pkts(bw, rtt, bdp_of_buf):
	return int(bw*1000*1000*rtt/1000.0 / (1514 * 8) * bdp_of_buf) 

default = {
    'bw':          50, # input bottleneck bw in Mbit/sec; required
    'rtt':         30, # RTT in ms; required
    'buf':         bdp_pkts(50, 30, 7), # input bottleneck buffer in packets; required
    'loss':         0, # input bottleneck loss rate in percent; optional
    'interval':     0, # interval between flow starts, in secs; optional
    'dur':         180, # length of test in secs: required
    'outdir':      '', # output directory for results
    'qdisc':       '', # qdisc at downstream bottleneck (empty for FIFO)
    'cmd':         '', # command to run (e.g. set sysctl values)
    'pcap':         0, # bytes per packet to capture; 0 for no tracing
}

random_loss = {
    'bw':          1000, # input bottleneck bw in Mbit/sec; required
    'rtt':         100, # RTT in ms; required
    'buf':         bdp_pkts(1000, 100, 1), # input bottleneck buffer in packets; required
    'loss':         0.1, # input bottleneck loss rate in percent; optional
    'interval':     0, # interval between flow starts, in secs; optional
    'dur':         60, # length of test in secs: required
    'outdir':      '', # output directory for results
    'qdisc':       '', # qdisc at downstream bottleneck (empty for FIFO)
    'cmd':         '', # command to run (e.g. set sysctl values)
    'pcap':         0, # bytes per packet to capture; 0 for no tracing
}

bufferbloat = {
    'bw':          50, # input bottleneck bw in Mbit/sec; required
    'rtt':         30, # RTT in ms; required
    'buf':         bdp_pkts(50, 30, 8), # input bottleneck buffer in packets; required
    'loss':         0, # input bottleneck loss rate in percent; optional
    'interval':     0, # interval between flow starts, in secs; optional
    'dur':         120, # length of test in secs: required
    'outdir':      '', # output directory for results
    'qdisc':       '', # qdisc at downstream bottleneck (empty for FIFO)
    'cmd':         '', # command to run (e.g. set sysctl values)
    'pcap':         0, # bytes per packet to capture; 0 for no tracing
}

shallow = {
    'bw':          1000, # input bottleneck bw in Mbit/sec; required
    'rtt':         100, # RTT in ms; required
    'buf':         bdp_pkts(1000, 100, 0.02), # input bottleneck buffer in packets; required
    'loss':         0, # input bottleneck loss rate in percent; optional
    'interval':     0, # interval between flow starts, in secs; optional
    'dur':         200, # length of test in secs: required
    'outdir':      '', # output directory for results
    'qdisc':       '', # qdisc at downstream bottleneck (empty for FIFO)
    'cmd':         '', # command to run (e.g. set sysctl values)
    'pcap':         0, # bytes per packet to capture; 0 for no tracing
}


params = default 
