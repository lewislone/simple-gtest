#!/bin/bash
#
#   +-------+   +--------+    +--------+    +--------+    +-------+
#   |  srv  |   |  srt   |    |  mid   |    |  crt   |    |  cli  |
#   |     r <---> l    r <----> l   r  <----> l   r  <----> l     |
#   |    0.1|   |0.11 1.1|    |1.11 2.1|    |2.11 3.1|    |3.11   |
#   +-------+   +--------+    +--------+    +---^----+    +-------+
#                                              r2|3.2       
#                                                |        +-------+
#                                                |        |  cli  |
#                                                 ------> |l      |
#                                                         |3.12   |
#                                                         +-------+

outdir=out
mkdir $outdir 


first_port=10000         # first TCP port to use
second_port=10001
server='/usr/local/bin/netserver'
client='/usr/local/bin/netperf'

dur=`./getconf.py dur`
receiver_ip=192.168.3.11
receiver_ip2=192.168.3.12
mem=536870912

dur=600

#netserver
pkill -f netserver
ip netns exec cli $server -N
ip netns exec cli2 $server -N


#netperf
ip netns exec srv $client -l $dur -H $receiver_ip -- -k THROUGHPUT -s $mem,$mem -S $mem,$mem -K bbr2 -P $first_port >> out/bbr2-0.5bdp-minirtt.log &
ip netns exec srv $client -l $dur -H $receiver_ip2 -- -k THROUGHPUT -s $mem,$mem -S $mem,$mem -K bbr2 -P $second_port >> out/bbr2-0.5bdp.log &
