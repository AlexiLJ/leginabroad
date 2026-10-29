# Docker first milestone

This milestone containerizes Django and Gunicorn only. Keep PostgreSQL and Nginx
on the host until the container has been tested and observed behind the existing
proxy. Do not switch to Caddy during this milestone.

## 1. Create the local environment file

PowerShell:

```powershell
Copy-Item .env.docker.example .env.docker
```

Linux:

```bash
cp .env.docker.example .env.docker
```

Replace every placeholder in `.env.docker`. This file is ignored by Git. For a
local HTTP test, leave the three security switches set to `false`. Production
behind Nginx must use HTTPS and set them to `true`.

## 2. Build the image

```bash
docker compose build
```

The build uses Python 3.14, installs dependencies from `uv.lock`, and runs the
application as the unprivileged user `app` with UID 10001.

## 3. Check Django configuration

```bash
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py check --deploy
```

Review deployment-check warnings. Some HTTPS warnings are expected only when the
local `.env.docker` deliberately disables HTTPS for direct testing.

## 4. Verify database reachability

```bash
docker compose run --rm web python manage.py showmigrations --plan
```

If this fails, do not expose PostgreSQL publicly. Verify its `listen_addresses`,
the Docker network rule in `pg_hba.conf`, the firewall, and the values in
`.env.docker`. On the Linux VPS, host networking can be evaluated later as a
short transitional option if the database is intentionally bound only to
`127.0.0.1`.

## 5. Collect static files into the named volume

```bash
docker compose run --rm web python manage.py collectstatic --noinput
```

The `static_data` volume is shared with the running web container. WhiteNoise
can serve these files during local testing. The production Nginx static-file
strategy remains unchanged until the proxy cutover is planned.

## 6. Start and verify the service

```bash
docker compose up -d
docker compose ps
docker compose logs --tail=100 web
curl http://127.0.0.1:8000/healthz/
```

Expected health response:

```json
{"status": "ok"}
```

Open <http://127.0.0.1:8000/> and check the homepage, an article, search, static
CSS, and an S3-hosted image.

## 7. Stop without deleting data

```bash
docker compose down
```

Do not add `--volumes` unless you intentionally want to delete the collected
static volume.

## Next milestone

After the container passes these checks:

1. Prepare the same `.env.docker` values on the VPS using a server-only secret
   file with permissions `600`.
2. Start the container on `127.0.0.1:8000` while the current Gunicorn service is
   still available for rollback.
3. Point the existing Nginx upstream to the container.
4. Observe logs, errors, health checks, article pages, admin uploads, and search.
5. Update GitHub Actions only after the manual Docker cutover is proven.
6. Replace Nginx with Caddy in a separate, later change.

See `DOCKER_CADDY_MIGRATION.md` for the complete production plan and rollback
procedures.

The exact milestone-two server commands, hardened Compose overlay, Nginx change,
and rollback sequence are documented in `DOCKER_SERVER_CUTOVER.md`.
