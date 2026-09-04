# Multi-layer Django news cache

Run `docker compose up --build`. The app is at http://localhost:8000 and seeds 10 articles plus `admin` and `reporter` users (passwords match their usernames).

Endpoints: `GET /articles/`, `GET /articles/trending/`, `POST /articles/bulk-view-increment/`, and `GET /articles/<id>/`. The list response varies on `Cookie`; detail responses expose `X-Fragment-Cache-Key` for fragment-key verification.

Run contract tests with `docker compose exec app python manage.py test news`. Run the intentional race demonstration with `docker compose exec app python manage.py stampede_check --unsafe --workers 10`, then verify the final lock with the same command without `--unsafe`. `CACHE_ENABLED=0 docker compose up -d --force-recreate app` temporarily selects Django's dummy cache for a reproducible no-cache Locust baseline; restore with `docker compose up -d --force-recreate app`.

See `benchmarks/report.md` for measured results and commands.
