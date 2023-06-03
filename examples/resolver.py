#!/usr/bin/env python3

"""Resolve a bunch of IP addresses using a pool of resolver actors.

Based on example contributed by Kristian Klette <klette@klette.us>.

Either run without arguments:

    ./resolver.py

Or specify pool size and IPs to resolve:

    ./resolver.py 3 193.35.52.{1,2,3,4,5,6,7,8,9}
"""

import pprint
import socket
import sys

import pykka


class Resolver(pykka.ThreadingActor):
    def resolve(self, ip):
        try:
            info = socket.gethostbyaddr(ip)
            print(f"Finished resolving {ip}")
            return info[0]
        except Exception:
            print(f"Failed resolving {ip}")
            return None


def run(pool_size, *ips):
    # Start resolvers
    resolvers = [Resolver.start().proxy() for _ in range(pool_size)]

    # Distribute work by mapping IPs to resolvers (not blocking)
    hosts = []
    for i, ip in enumerate(ips):
        hosts.append(resolvers[i % len(resolvers)].resolve(ip))

    # Gather results (blocking)
    ip_to_host = zip(ips, pykka.get_all(hosts))
    pprint.pprint(list(ip_to_host))

    # Clean up
    pykka.ActorRegistry.stop_all()


if __name__ == "__main__":
    if len(sys.argv[1:]) >= 2:
        run(int(sys.argv[1]), *sys.argv[2:])
    else:
        ips = [f"193.35.52.{i}" for i in range(1, 50)]
        run(10, *ips)
