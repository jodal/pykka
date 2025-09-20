# Worker pool

This example shows how to use a pool of workers to fan out work to multiple
actors and then collect the result using [`get_all()`][pykka.get_all].

The example perform DNS lookups concurrently. It creates a pool of 4 workers and
distributes the work of resolving a list of IP addresses among them. Each worker
performs the DNS lookup and returns the result to the main thread, which
collects and prints the results.

## Example

```title="examples/worker_pool.py"
--8<-- "examples/worker_pool.py"
```

## Output

```console
$ uv run examples/worker_pool.py
Finished resolving 193.35.52.3
Finished resolving 193.35.52.2
Finished resolving 193.35.52.1
Finished resolving 193.35.52.4
Failed resolving 193.35.52.8
Failed resolving 193.35.52.6
Failed resolving 193.35.52.5
Failed resolving 193.35.52.7
Failed resolving 193.35.52.12
Failed resolving 193.35.52.9
Failed resolving 193.35.52.11
Failed resolving 193.35.52.10
Failed resolving 193.35.52.14
Failed resolving 193.35.52.13
Failed resolving 193.35.52.15
Failed resolving 193.35.52.16
Finished resolving 193.35.52.18
Finished resolving 193.35.52.19
Failed resolving 193.35.52.17
[(IPv4Address('193.35.52.1'), 'merete.samfundet.no'),
 (IPv4Address('193.35.52.2'), 'osl.samfundet.no'),
 (IPv4Address('193.35.52.3'), 'fnis.samfundet.no'),
 (IPv4Address('193.35.52.4'), 'trd.samfundet.no.52.35.193.in-addr.arpa'),
 (IPv4Address('193.35.52.5'), None),
 (IPv4Address('193.35.52.6'), None),
 (IPv4Address('193.35.52.7'), None),
 (IPv4Address('193.35.52.8'), None),
 (IPv4Address('193.35.52.9'), None),
 (IPv4Address('193.35.52.10'), None),
 (IPv4Address('193.35.52.11'), None),
 (IPv4Address('193.35.52.12'), None),
 (IPv4Address('193.35.52.13'), None),
 (IPv4Address('193.35.52.14'), None),
 (IPv4Address('193.35.52.15'), None),
 (IPv4Address('193.35.52.16'), None),
 (IPv4Address('193.35.52.17'), None),
 (IPv4Address('193.35.52.18'), 'bablefisk.samfundet.no'),
 (IPv4Address('193.35.52.19'), 'altostratus.samfundet.no')]
```
