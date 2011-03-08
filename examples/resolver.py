#! /usr/bin/env python

"""
Resolve a bunch of IP addresses using a pool of resolver actors.

Based on example contributed by Kristian Klette <klette@klette.us>.

Either run without arguments:

    ./resolver.py

Or specify pool size and IPs to resolve:

    ./resolver.py 3 129.240.2.{1,2,3,4,5,6,7,8,9}
"""

from pykka.actor import ThreadingActor
from pykka.future import get_all
from pykka.registry import ActorRegistry

from pprint import pprint
import random
import socket
import sys

class Resolver(ThreadingActor):
    def resolve(self, ip):
        try:
            info = socket.gethostbyaddr(ip)
            print "Finished resolving %s" % ip
            return info[0]
        except:
            print "Failed resolving %s" % ip
            return None

def run(pool_size, *ips):
    # Start resolvers
    resolvers = [Resolver.start().proxy() for _ in range(pool_size)]

    # Distribute work by mapping IPs to resolvers (not blocking)
    hosts = []
    for i, ip in enumerate(ips):
        hosts.append(resolvers[i % len(resolvers)].resolve(ip))

    # Gather results (blocking)
    ip_to_host = zip(ips, get_all(hosts))
    pprint(ip_to_host)

    # Clean up
    ActorRegistry.stop_all()

if __name__ == '__main__':
    if len(sys.argv[1:]) >= 2:
        run(int(sys.argv[1]), *sys.argv[2:])
    else:
        ips = ['129.241.93.%s' % i for i in range(1, 50)]
        run(10, *ips)
