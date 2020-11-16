#!/usr/bin/python
import os
import os.path
import sys
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

    run('pkill -f netserver')
    run('pkill -f netperf')
if __name__ == '__main__':
    sys.exit(cleanup())
