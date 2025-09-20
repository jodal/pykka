#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pykka",
# ]
# ///

import pprint
import socket
from ipaddress import IPv4Address

import pykka


class Resolver(pykka.ThreadingActor):
    def resolve(self, ip: IPv4Address) -> str | None:
        try:
            info = socket.gethostbyaddr(str(ip))
            print(f"Finished resolving {ip}")
            return info[0]
        except Exception:
            print(f"Failed resolving {ip}")
            return None


if __name__ == "__main__":
    ip_addresses = [IPv4Address(f"193.35.52.{i}") for i in range(1, 20)]
    pool_size = 4

    # Start resolvers
    pool = [Resolver.start().proxy() for _ in range(pool_size)]

    # Distribute work by mapping IPs to resolvers (not blocking)
    hosts: list[pykka.Future[str]] = []
    for i, ip in enumerate(ip_addresses):
        resolver = pool[i % len(pool)]
        hosts.append(resolver.resolve(ip))

    # Gather results (blocking)
    result = list(zip(ip_addresses, pykka.get_all(hosts), strict=True))
    pprint.pprint(result)

    # Stop all actors
    pykka.ActorRegistry.stop_all()
