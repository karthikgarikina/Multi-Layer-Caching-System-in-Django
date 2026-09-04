# Benchmark report

The method was Locust headless mode against the Docker `app` service, using 10 users, spawn rate 10, and a 15-second run. The no-cache run used `CACHE_ENABLED=0`, which selects Django's `DummyCache`; the final run used the normal Redis configuration. Redis `INFO stats` was reset before the cached run, and hit rate is `keyspace_hits / (keyspace_hits + keyspace_misses)`.

| Scenario | Requests/s | Average response time (ms) | 95th percentile (ms) | Redis hit rate |
| --- | ---: | ---: | ---: | ---: |
| No cache | 18.07 | 346 | 2000 | 0% (DummyCache) |
| Full cache | 47.79 | 10 | 26 | 99.55% (1,096 hits / 5 misses) |

## Stampede checkpoint

Before the final lock was enabled, `python manage.py stampede_check --unsafe --workers 10` logged ten `COMPUTE_TRENDING_ARTICLES` invocations. The final `python manage.py stampede_check --workers 10` run logged exactly one invocation. This validates that `cache.add` elects one recomputing worker while the other nine wait for the cached result.

## Analysis

The cache-enabled scenario processed about 2.6 times as many requests per second and reduced mean latency from 346 ms to 10 ms. The intentionally two-second trending computation dominated the no-cache p95; after the first Redis-backed computation, nearly every read was a cache hit. Exact numbers are development-machine measurements and will vary by host.
