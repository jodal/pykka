# Benchmarks

Use these benchmarks before a release to find out if the new code is slower
than the last release. The benchmarks use [pyperf](https://pyperf.readthedocs.io/).

## How to run a benchmark

Run the benchmark by hand, on one machine. Run the last release and the new
code one after the other, with the same Python version.

Do not store the results in this repo. Timings from different machines, or
from the same machine at different times, cannot be compared.

1. Run the last release from PyPI, for example Pykka 4.4.2:

   ```sh
   uv run --no-project --python 3.14 --with pykka==4.4.2 --with pyperf \
       python benchmarks/threading_actors.py \
       --rigorous --affinity=2 -o old.json
   ```

2. Run the new code from this repo:

   ```sh
   uv run --python 3.14 --group benchmark \
       python benchmarks/threading_actors.py \
       --rigorous --affinity=2 -o new.json
   ```

3. Compare the two results:

   ```sh
   uv run --group benchmark python -m pyperf compare_to old.json new.json
   ```

## How to get stable results

Pin the benchmark to one CPU core with `--affinity`. On two cores, most of a
round trip is the time it takes to wake a sleeping core, and that changes from
run to run by up to 3x.

Use `--rigorous` to get more runs and values.

Trust a result only if the spread (`std dev`) is about 1% or less for the
cases that have a limit. The docstring of each benchmark tells which cases
have a limit.

## CI

CI does not run the benchmarks. It only runs the `test_*.py` files in this
directory. These run each case a few times to make sure that the benchmarks
still work.
