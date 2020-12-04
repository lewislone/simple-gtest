#!/usr/bin/python
#coding: UTF-8
import os
import re
import sys
from matplotlib.pyplot import *

def search_stream(streams, id):
    for stream in streams:
        if stream['id'] == id:
            return stream
    return False

'''
-----------------------------------------------------------
Server listening on 3333
-----------------------------------------------------------
Accepted connection from 10.0.3.1, port 55241
[  5] local 10.0.5.2 port 3333 connected to 10.0.3.1 port 53551
[ ID] Interval           Transfer     Bandwidth
[  5]   0.00-1.00   sec   156 KBytes  1.27 Mbits/sec                  
[  5]   1.00-2.00   sec  1.19 MBytes  9.96 Mbits/sec 
[  5]  48.00-49.00  sec  1.42 MBytes  11.9 Mbits/sec
[  5]  60.00-60.18  sec   315 KBytes  14.1 Mbits/sec                  
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth
[  5]   0.00-60.18  sec  0.00 Bytes  0.00 bits/sec                  sender
[  5]   0.00-60.18  sec  94.1 MBytes  13.1 Mbits/sec                  receiver
iperf3: interrupt - the server has terminated
'''

def parse_file(f):
        set = 1 
        sp = '/'
        one_case = 0 
        streams = []
        line = f.readline()
        while line:
            ##one set
            if line[0] != '[':
                line = f.readline()
                continue
            elif line[:14] == '[ ID] Interval':
                if one_case == 1:
                    break
                line = f.readline()
                one_case += 1
            else:
                #[  5]   0.00-1.00   sec   156 KBytes  1.27 Mbits/sec                  
                value = line.split(']')
                id = int(value[0][1:])
                stream = search_stream(streams, id)
                if stream is False:
                    stream = {}
                    stream['id'] = id
                    stream['rate'] = []
                    streams.append(stream)
                items = value[1].split()
                if items[0] == "local":
                    stream["title"] = value[1:]
                    line = f.readline()
                    continue
                if items[5][0] == "K":
                	rate = float(items[4])/1024
                elif items[5][0] == "b":
                	rate = float(items[4])/1024/1024
                else:
                	rate = float(items[4])
                stream["rate"].append(rate)
                line = f.readline()
                continue

        f.close()
        return streams

if __name__ == '__main__':

    log_files = sys.argv[1:]
    items=[]
    for log_file in log_files:
        if not os.path.exists(log_file):
            print log_file + " not exist"
            continue

        f = file(log_file)
        streams = parse_file(f)
        stream = {}
        for stream in streams:
            stream["file"] = log_file
            items.append(stream)
    item = {}
    index=0
    color=['go:', 'ro:', 'bo:', 'yo:']
    grid(True)
    ylabel('rate', fontdict={'fontsize':20})
    xlabel('time(s)', fontdict={'fontsize':20})
    for item in items:
        print item 
        rate = [float(rate) for rate in item['rate']]
        plot(range(len(rate)), rate, color[index], linewidth=2, label=item["file"])
        index += 1
    legend(title="(rate)", loc='best')
    #savefig('ack_timestamp.png')
    show()
