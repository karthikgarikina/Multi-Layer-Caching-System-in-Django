# Multi-Layer Caching System in Django

## 1. Project overview

This is a Dockerized Django news application that demonstrates three caching layers backed by Redis:

- **Per-view caching** for the article list, separated safely by `Vary: Cookie` for anonymous and authenticated users.
- **Low-level caching** for the expensive top-five trending-articles query, protected by a Redis atomic lock to prevent cache stampedes.
- **Template fragment caching** for article bodies, versioned with `updated_at` so an updated article receives a new fragment key.

It also demonstrates cache invalidation after normal `Article.save()` calls (a Django signal) and after a bulk view-count update (explicit service invalidation). PostgreSQL is seeded automatically with 10 articles and two test users: `admin` / `admin` and `reporter` / `reporter`.

## 2. Set up and run

1. Ensure Docker Desktop and Docker Compose are running.
2. Copy `.env.example` to `.env` if you want to change the supplied development values.
3. From the repository root, start the stack:

   ```bash
   docker compose up --build -d
   docker compose ps
   ```

   All three services (`app`, `db`, and `cache`) should show `healthy`. The Django site is then available at `http://localhost:8000` and check `http://localhost:8000/health`.

4. Run the automated contract checks:

   ```bash
   docker compose exec -T app python manage.py test news
   ```

## 3. Check endpoints and requirements

| Requirement | Check |
| --- | --- |
| Container health and seed data | Run `docker compose ps`, then `docker compose exec -T app python manage.py shell -c "from news.models import Article; from django.contrib.auth.models import User; print(Article.objects.count(), User.objects.count())"`. Expected: `10 2`. |
| Per-view cache and cookie variation | Run `curl -i http://localhost:8000/articles/`. Expect `200`, `Vary: Cookie`, and `Cache-Control: max-age=900`. Log into `/admin/` as `admin`, revisit `/articles/`, and confirm `Welcome, admin` instead of `Welcome, anonymous`. |
| Trending low-level cache | Run `docker compose exec -T cache redis-cli FLUSHDB`, then request `http://localhost:8000/articles/trending/` twice. The first request takes about two seconds; the second is returned from Redis. |
| Stampede demonstration and final lock | Run `docker compose exec -T app python manage.py stampede_check --unsafe --workers 10` to observe 10 computations, then run `docker compose exec -T app python manage.py stampede_check --workers 10` to observe exactly 1. |
| Save invalidation | Populate `/articles/trending/`, edit and save an article in `/admin/`, then inspect `docker compose exec -T cache redis-cli KEYS '*trending_articles*'`; the main key is removed. |
| Bulk invalidation | Populate `/articles/trending/`, run `curl -X POST -i http://localhost:8000/articles/bulk-view-increment/`, expect `204`, then inspect Redis with the command above. |
| Versioned fragment cache | Run `curl -i http://localhost:8000/articles/1/`. `X-Fragment-Cache-Key` is the exact Django fragment key. Save article 1 in `/admin/`, repeat the request, and verify the header changed. |
| Benchmarks | Read [benchmarks/report.md](benchmarks/report.md). It includes real Locust results, p95 latency, and Redis hit rate. |

---
### Demo Video

https://youtu.be/1ZSzlD2M9p4

---
### Optional benchmark commands

The report was generated with `locustfile.py`. To reproduce the no-cache baseline, start the app with the supplied temporary environment and run Locust; then restore the final configuration.

```bash
docker compose --env-file .env.nocache up -d --force-recreate app
docker compose exec -T app locust -f /app/locustfile.py --host http://127.0.0.1:8000 --headless -u 10 -r 10 -t 15s
docker compose up -d --force-recreate app
```
