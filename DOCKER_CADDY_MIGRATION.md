# Legin' Abroad: Docker and Caddy Migration Runbook

This document describes a low-risk migration of `leginabroad.com` from the current
Nginx + systemd + Gunicorn deployment to:

```text
Internet
   |
   v
Caddy on the VPS (TLS, redirects, compression, reverse proxy)
   |
   v
Django + Gunicorn in Docker (127.0.0.1:8000)
   |
   v
PostgreSQL on the VPS
```

The database stays on the host during the first migration. Uploaded media continues
to use AWS S3. This keeps the highest-risk stateful component out of the initial
container migration.

> **Do not migrate Docker and Caddy in the same production cutover.** First run the
> Django container behind the existing Nginx proxy. Replace Nginx with Caddy only
> after the container has completed several successful deployments.

---

## 1. Goals and non-goals

### Goals

- Reproducible Python and dependency versions using `pyproject.toml` and `uv.lock`.
- A stateless, replaceable Django application container.
- An explicit health check before traffic reaches a new deployment.
- Automatic HTTPS and certificate renewal through Caddy.
- A deployment that is easy to roll back.
- No production credentials inside Git or Docker image layers.
- Continued availability of `/ads.txt`, static files, admin, articles, search, and S3 media.

### Non-goals for the first migration

- Moving PostgreSQL into Docker.
- Moving uploaded media away from AWS S3.
- Introducing Kubernetes, Docker Swarm, or multiple application servers.
- Achieving zero-downtime database schema migrations.
- Replacing the existing server or DNS provider.

---

## 2. Current project facts

The runbook assumes the current repository has these characteristics:

- Django WSGI application: `legin_abroad_base.wsgi:application`
- Gunicorn dependency: `gunicorn>=23.0.0`
- Python requirement: `>=3.14`
- Dependency lock file: `uv.lock`
- Static root: `<repository>/static`
- Uploaded media: AWS S3 through `django-storages`
- Production database: PostgreSQL
- Current proxy: Nginx
- Current application process: systemd Gunicorn socket/service
- Current deployment: GitHub Actions connects over SSH and runs `restart.sh`
- Deployment branch: `master`

### Critical blocker: branch-based secrets loader

`legin_abroad_base/env_handler.py` currently:

1. Finds the repository `.git` directory.
2. Reads `.git/HEAD` to determine the active branch.
3. Reads `pathes.json`.
4. Uses that file to locate another JSON file containing production secrets.

This is incompatible with a secure Docker image because `.git`, `pathes.json`, and
secret JSON files should not be copied into the image. Refactor settings to use
normal environment variables before building the production image.

### Critical blocker: file logging

Production settings write errors to `django_error.log` inside the repository. A
container should log to standard output/error so Docker can collect and rotate the
logs. Remove the required file handler or make it explicitly optional before running
as a non-root container user.

---

## 3. Required access and prerequisites

Before starting, confirm that you have:

- SSH and `sudo` access to the VPS.
- Access to the DNS provider for `leginabroad.com`.
- Access to GitHub repository secrets.
- PostgreSQL credentials and permission to create a backup.
- AWS credentials used by `django-storages`.
- Enough free disk space for Docker images and a database backup.
- Ports `80` and `443` open in the VPS and provider firewall.

Record the server distribution and architecture:

```bash
cat /etc/os-release
uname -m
df -h
free -h
```

Record the current service state:

```bash
sudo systemctl status nginx --no-pager
sudo systemctl status gunicorn.service gunicorn.socket --no-pager
sudo nginx -t
```

Record installed versions:

```bash
python3 --version
uv --version
nginx -v
psql --version
```

---

## 4. Phase 0: back up and document the working deployment

Do not continue until this phase is complete.

### 4.1 Save the current Nginx configuration

```bash
mkdir -p "$HOME/migration-backups"
sudo nginx -T > "$HOME/migration-backups/nginx-full-$(date +%F-%H%M%S).txt" 2>&1
sudo tar -C /etc -czf "$HOME/migration-backups/nginx-directory-$(date +%F-%H%M%S).tar.gz" nginx
```

Verify both files exist and are non-empty:

```bash
ls -lh "$HOME/migration-backups"
```

### 4.2 Save the Gunicorn systemd definitions

```bash
sudo systemctl cat gunicorn.service > "$HOME/migration-backups/gunicorn.service.txt"
sudo systemctl cat gunicorn.socket > "$HOME/migration-backups/gunicorn.socket.txt"
```

### 4.3 Back up PostgreSQL

Use the real production database name and user. Do not put the password directly in
shell history.

```bash
read -r -p "Database name: " DB_NAME
read -r -p "Database user: " DB_USER
pg_dump --format=custom --no-owner --file="$HOME/migration-backups/${DB_NAME}-$(date +%F-%H%M%S).dump" --username="$DB_USER" "$DB_NAME"
```

Verify that PostgreSQL can read the backup catalogue:

```bash
LATEST_DUMP="$(ls -1t "$HOME"/migration-backups/*.dump | head -n 1)"
pg_restore --list "$LATEST_DUMP" > /dev/null
echo "Verified: $LATEST_DUMP"
```

Copy the backup off the VPS before changing production services.

### 4.4 Record the current public behavior

```bash
curl -fsS -o /dev/null -w 'home: %{http_code}\n' https://leginabroad.com/
curl -fsS -o /dev/null -w 'topics: %{http_code}\n' https://leginabroad.com/sections
curl -fsS https://leginabroad.com/ads.txt
```

Save a list of important URLs for post-migration verification:

- `/`
- `/sections`
- `/sections/tech`
- `/sections/search?query=`
- `/about`
- `/ads.txt`
- `/admin_LA/`
- one published article URL

---

## 5. Phase 1: make Django container-compatible

Complete and deploy these application changes while the site still runs through the
current systemd Gunicorn service. This separates application refactoring from the
container cutover.

### 5.1 Replace `var_getter()` with environment variables

Use a small strict helper in `settings.py` or a separate settings utility:

```python
import os


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value
```

Replace production secret lookups with environment variables:

```python
SECRET_KEY = env("DJANGO_SECRET_KEY")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRESQL_NAME"),
        "USER": env("POSTGRESQL_USER"),
        "PASSWORD": env("POSTGRESQL_PASSWORD"),
        "HOST": env("HOST_NAME", "127.0.0.1"),
        "PORT": env("PORT", "5432"),
    }
}

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_SIGNATURE_NAME = env("AWS_S3_SIGNATURE_NAME", "s3v4")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME")
```

Do not delete the existing JSON configuration until the environment-variable version
has been tested with the existing systemd service.

### 5.2 Move production logs to stdout

Docker captures stdout/stderr. A simple production handler is:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
```

### 5.3 Put WhiteNoise immediately after SecurityMiddleware

If WhiteNoise remains responsible for static files, middleware order should begin:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # remaining middleware...
]
```

For the first migration, Caddy can serve collected static files directly instead.
WhiteNoise is still useful as a fallback.

### 5.4 Add a health endpoint

Add a lightweight `/healthz` view that returns HTTP 200. It should verify the Django
process. A separate readiness endpoint may also perform a minimal database query.

Example response:

```text
ok
```

Do not expose secrets, environment details, package versions, or database errors in
the response.

### 5.5 Run Django deployment checks

With production environment variables loaded:

```bash
uv run python manage.py check --deploy
uv run python manage.py test
```

Resolve all security errors before containerization. Review warnings deliberately;
do not silence them only to obtain a clean command.

---

## 6. Phase 2: add Docker files

Create these files in the repository root:

```text
Dockerfile
.dockerignore
compose.yaml
.env.production.example
```

Never commit `.env.production`.

### 6.1 Example `.dockerignore`

```dockerignore
.git
.github
.idea
.ruff_cache
.venv
__pycache__
*.py[cod]
*.log
*.dump
*.sqlite3
.django_env.json
.env
.env.*
!.env.production.example
.ssh
branding
preview_media
static
media
```

Check that database dumps, SSH material, `.django_env.json`, and the local virtual
environment are excluded before the first build:

```bash
docker build --no-cache --progress=plain -t leginabroad:check .
docker history --no-trunc leginabroad:check
```

### 6.2 Example production `Dockerfile`

Pin the Python base image more precisely during implementation. Rebuild regularly to
receive operating-system security updates.

```dockerfile
# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd --gid 10001 django \
    && useradd --uid 10001 --gid django --create-home --no-log-init django

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=django:django . .

RUN mkdir -p /app/static \
    && chown -R django:django /app

USER django

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"

CMD ["gunicorn", "legin_abroad_base.wsgi:application", "--bind", "127.0.0.1:8000", "--workers", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
```

Notes:

- Do not copy `.git` merely to keep `env_handler.py` working. Refactor settings first.
- Pin the `uv` image to a version or digest instead of leaving `latest` in the final implementation.
- Two Gunicorn workers are a conservative starting point for a small VPS. Adjust after
  measuring memory and response time.
- The container runs as UID/GID `10001`, not root.

### 6.3 Example `.env.production.example`

Commit names only, never real values:

```dotenv
DJANGO_SECRET_KEY=
DJANGO_LOG_LEVEL=INFO
POSTGRESQL_NAME=
POSTGRESQL_USER=
POSTGRESQL_PASSWORD=
HOST_NAME=127.0.0.1
PORT=5432
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_SIGNATURE_NAME=s3v4
AWS_S3_REGION_NAME=
```

On the VPS:

```bash
cd "$HOME/leginabroad"
cp .env.production.example .env.production
chmod 600 .env.production
```

Edit `.env.production` on the server. Never print it in CI logs.

### 6.4 Transitional `compose.yaml`

For the first single-VPS migration, host networking lets the container connect to the
host PostgreSQL server at `127.0.0.1` without making PostgreSQL public or modifying
Docker bridge firewall rules.

```yaml
services:
  web:
    build:
      context: .
      target: runtime
    image: leginabroad-web:local
    env_file:
      - .env.production
    network_mode: host
    restart: unless-stopped
    init: true
    volumes:
      - ./static:/app/static
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"
```

Important consequences of `network_mode: host`:

- It is intended for this Linux VPS transition, not portable local development.
- Do not add a `ports:` section; it is ignored with host networking.
- Gunicorn must bind to `127.0.0.1:8000`, not `0.0.0.0`, to avoid public exposure.
- PostgreSQL can remain bound to host loopback.

Later, replace host networking with a normal Docker bridge network if the database is
also containerized or if PostgreSQL is deliberately configured for bridge access.

### 6.5 Prepare the static directory

The container user must be able to write collected static files:

```bash
cd "$HOME/leginabroad"
mkdir -p static
sudo chown -R 10001:10001 static
```

Do not change ownership of the entire repository to the container user.

---

## 7. Phase 3: local and server-side container validation

### 7.1 Build the image

```bash
docker compose build --pull web
```

### 7.2 Run Django checks in an ephemeral container

```bash
docker compose run --rm web python manage.py check --deploy
docker compose run --rm web python manage.py test
```

### 7.3 Run migrations explicitly

Do not run migrations automatically every time the application container restarts.
Run them as a deliberate deployment step:

```bash
docker compose run --rm web python manage.py migrate --noinput
```

For risky schema changes, back up the database immediately before this command and
use backward-compatible migrations.

### 7.4 Collect static files

```bash
docker compose run --rm web python manage.py collectstatic --noinput
```

Verify files are present on the host:

```bash
find static -maxdepth 2 -type f | head
```

### 7.5 Start the container without changing Nginx

If the current Gunicorn service already uses port 8000, temporarily use another port
for the container by overriding the Gunicorn command, or stop only the old Gunicorn
service during a scheduled test. Do not stop Nginx.

Example temporary command on port 8001:

```bash
docker compose run --rm --name leginabroad-test web \
  gunicorn legin_abroad_base.wsgi:application \
  --bind 127.0.0.1:8001 \
  --workers 2 \
  --access-logfile - \
  --error-logfile -
```

From a second SSH session:

```bash
curl -fsS http://127.0.0.1:8001/healthz
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8001/
curl -fsS http://127.0.0.1:8001/ads.txt
```

Stop the temporary container after validation.

---

## 8. Phase 4: put Docker behind the existing Nginx proxy

This is the first production cutover.

### 8.1 Pre-cutover checklist

- [ ] Database backup exists and `pg_restore --list` succeeds.
- [ ] Container tests pass.
- [ ] `manage.py check --deploy` passes or all warnings are understood.
- [ ] Static collection succeeds.
- [ ] Health endpoint returns HTTP 200.
- [ ] `.env.production` exists with mode `600`.
- [ ] Docker image does not contain `.git`, `.ssh`, dumps, or environment files.
- [ ] A second SSH session is open for rollback.

### 8.2 Perform the Gunicorn cutover

```bash
cd "$HOME/leginabroad"
docker compose build --pull web
docker compose run --rm web python manage.py migrate --noinput
docker compose run --rm web python manage.py collectstatic --noinput

sudo systemctl stop gunicorn.socket gunicorn.service
docker compose up -d web
```

Confirm Docker reports a healthy container:

```bash
docker compose ps
docker compose logs --tail=200 web
curl -fsS http://127.0.0.1:8000/healthz
```

Nginx should continue proxying to the same backend address. If it currently proxies
to a Unix socket, update only the upstream to `127.0.0.1:8000`, validate, then reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 8.3 Verify production

```bash
curl -fsS -o /dev/null -w 'home: %{http_code}\n' https://leginabroad.com/
curl -fsS -o /dev/null -w 'topics: %{http_code}\n' https://leginabroad.com/sections
curl -fsS https://leginabroad.com/ads.txt
```

Manually verify:

- Mobile and desktop navigation.
- Article detail pages and breadcrumbs.
- Search form and search results.
- Django admin login page.
- Static CSS and JavaScript.
- Existing S3 images.
- Google consent message.
- `/ads.txt` content type and exact publisher line.

### 8.4 Observe before removing old services

Keep the systemd Gunicorn unit files installed for at least several successful
deployments. They provide a fast rollback path.

Useful commands:

```bash
docker compose ps
docker compose logs --tail=500 web
docker stats --no-stream
sudo journalctl -u nginx --since '30 minutes ago' --no-pager
```

---

## 9. Docker rollback procedure

If the container fails but no incompatible database migration was applied:

```bash
cd "$HOME/leginabroad"
docker compose down
sudo systemctl start gunicorn.socket gunicorn.service
sudo nginx -t
sudo systemctl reload nginx
```

Verify:

```bash
sudo systemctl status gunicorn.service gunicorn.socket --no-pager
curl -fsS -o /dev/null -w '%{http_code}\n' https://leginabroad.com/
```

If an incompatible database migration was applied, application rollback alone may not
be sufficient. Prefer backward-compatible migrations. Restore the database only as a
last resort because it discards data created after the backup.

---

## 10. Phase 5: prepare the Caddy migration

Do this only after Docker has run reliably behind Nginx.

### 10.1 Resolve `www` DNS first or omit it initially

At the time this runbook was created, `www.leginabroad.com` did not resolve. Choose
one approach:

1. Initially configure only `leginabroad.com`; or
2. Add a DNS `CNAME` from `www` to `leginabroad.com` (or an equivalent `A`/`AAAA`
   record), wait for propagation, and configure a redirect.

Verify DNS before asking Caddy to obtain a certificate:

```bash
getent hosts leginabroad.com
getent hosts www.leginabroad.com
```

### 10.2 Install Caddy from the official repository

Use the current instructions for the server distribution:

<https://caddyserver.com/docs/install>

After installation:

```bash
caddy version
sudo systemctl status caddy --no-pager
```

It is normal for Caddy to be inactive or unable to bind while Nginx owns ports 80 and
443. Do not stop Nginx merely to check Caddyfile syntax.

### 10.3 Create `/etc/caddy/Caddyfile`

Start with the bare domain only:

```caddyfile
{
    email YOUR-ACME-CONTACT-EMAIL
}

leginabroad.com {
    encode zstd gzip

    handle_path /static/* {
        root * /home/YOUR_SERVER_USER/leginabroad/static
        file_server
    }

    reverse_proxy 127.0.0.1:8000

    log {
        output file /var/log/caddy/leginabroad-access.log {
            roll_size 10MiB
            roll_keep 10
            roll_keep_for 720h
        }
        format json
    }
}
```

Replace both placeholders. Do not add `www` until its DNS record resolves.

The Caddy system user must be able to traverse the parent directories and read the
static directory. Avoid making secret files world-readable. A cleaner long-term
location for static files is `/srv/leginabroad/static`:

```bash
sudo mkdir -p /srv/leginabroad
sudo chown root:caddy /srv/leginabroad
sudo chmod 750 /srv/leginabroad
```

If using `/srv/leginabroad/static`, change the Compose bind mount and Caddy root to
that path.

### 10.4 Optional `www` redirect after DNS works

```caddyfile
www.leginabroad.com {
    redir https://leginabroad.com{uri} permanent
}
```

### 10.5 Validate without stopping Nginx

```bash
sudo caddy fmt --overwrite /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo caddy adapt --config /etc/caddy/Caddyfile --pretty > /tmp/leginabroad-caddy.json
```

Review the adapted configuration and remove the temporary file afterward.

Do not repeatedly test public certificate issuance against production ACME endpoints.
Caddy documents ACME staging for repeated certificate tests.

---

## 11. Phase 6: replace Nginx with Caddy

Perform this during a low-traffic maintenance window with two SSH sessions open.

### 11.1 Final pre-cutover checks

- [ ] Django container is healthy on `127.0.0.1:8000`.
- [ ] `caddy validate` succeeds.
- [ ] DNS for every hostname in the Caddyfile resolves to the VPS.
- [ ] Ports 80 and 443 are open.
- [ ] Caddy data directory is persistent and writable.
- [ ] Nginx configuration backup exists.
- [ ] The rollback commands are ready in the second SSH session.

### 11.2 Cut over ports 80 and 443

```bash
sudo systemctl stop nginx
sudo systemctl start caddy
sudo systemctl status caddy --no-pager
```

Watch logs immediately:

```bash
sudo journalctl -u caddy -f
```

From a second session or your local machine:

```bash
curl -I https://leginabroad.com/
curl -fsS https://leginabroad.com/ads.txt
```

### 11.3 Verify certificates and redirects

```bash
curl -I http://leginabroad.com/
curl -I https://leginabroad.com/
```

Expected behavior:

- HTTP redirects to HTTPS.
- HTTPS returns a valid public certificate.
- The application returns HTTP 200.
- Static CSS loads successfully.

If `www` was added:

```bash
curl -I https://www.leginabroad.com/
```

It should redirect to the bare domain while preserving the path and query string.

### 11.4 Verify application behavior

Repeat every URL and manual check from section 8.3. Also verify:

- No mixed-content errors in the browser console.
- Django sees requests as HTTPS.
- CSRF-protected admin forms submit successfully.
- Real client IP and forwarded headers are correct.
- Google CMP still appears when tested.
- AdSense script and `/ads.txt` remain accessible.

### 11.5 Keep Certbot temporarily

Do not delete certificates or Certbot configuration during cutover. After Caddy has
renewed its own certificates successfully and the site has remained stable, disable
the old Certbot timer if one exists:

```bash
sudo systemctl list-timers | grep -i certbot || true
```

Only then consider:

```bash
sudo systemctl disable --now certbot.timer
```

Do not remove historical certificates until rollback is no longer required.

---

## 12. Caddy rollback procedure

If Caddy fails during cutover:

```bash
sudo systemctl stop caddy
sudo nginx -t
sudo systemctl start nginx
sudo systemctl status nginx --no-pager
```

Verify the public site immediately:

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' https://leginabroad.com/
curl -fsS https://leginabroad.com/ads.txt
```

Caddy configuration changes should use graceful reloads after the initial migration:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Do not stop and restart Caddy for routine configuration changes.

---

## 13. Phase 7: update GitHub Actions

The current workflow deploys on every push to `master`, runs `git pull`, executes
`restart.sh`, and restarts systemd Gunicorn/Nginx. Replace that only after Docker and
Caddy are already working manually.

### Recommended first version: build on the VPS

Keep the existing SSH connection but change the remote deployment commands to:

```bash
set -Eeuo pipefail
cd "$HOME/leginabroad"

git pull --ff-only
docker compose build --pull web
docker compose run --rm web python manage.py check --deploy
docker compose run --rm web python manage.py migrate --noinput
docker compose run --rm web python manage.py collectstatic --noinput
docker compose up -d web

for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/healthz > /dev/null; then
    break
  fi
  if [ "$attempt" -eq 30 ]; then
    docker compose logs --tail=200 web
    exit 1
  fi
  sleep 2
done

sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
docker image prune -f
```

Important improvements to the GitHub Actions workflow:

1. Add a test job before deployment.
2. Make the deploy job depend on successful tests.
3. Use GitHub environment protection for production if available.
4. Prevent two deployments from running concurrently.
5. Keep `git pull --ff-only`; do not force-reset production.
6. Never echo production environment variables.
7. Print container status and bounded logs when the health check fails.

### Later improvement: build once and publish an image

After the simple deployment is stable:

1. Build the image in GitHub Actions.
2. Tag it with the Git commit SHA.
3. Push it to GitHub Container Registry.
4. Pull that immutable image on the VPS.
5. Keep the previous image tag for rollback.

This avoids building different images on different servers and makes rollback more
predictable.

---

## 14. Static files strategy

Choose one strategy and document it.

### Strategy A: Caddy serves collected static files (recommended initially)

- `collectstatic` writes into a host bind-mounted directory.
- Caddy serves `/static/*` directly.
- Django handles application requests.

Advantages:

- Efficient static delivery.
- No static requests enter Gunicorn.
- Similar to the existing Nginx design.

Requirements:

- Correct ownership for UID/GID `10001` to write files.
- Caddy must have read/traverse permissions.
- The directory must persist across container replacement.

### Strategy B: WhiteNoise serves static files

- Run `collectstatic` inside the image or during deployment.
- Proxy every request through Caddy.
- Place WhiteNoise immediately after SecurityMiddleware.

Advantages:

- Fewer Caddy filesystem permissions.
- Application image can contain all static assets.

Trade-off:

- Static requests enter the application container.
- Building static files into the image requires settings that can run safely during
  the build without production secrets.

Do not use both strategies accidentally. If Caddy serves static files, verify that its
filesystem path matches Django's `STATIC_ROOT` output.

---

## 15. Security checklist

- [ ] `.env.production` is excluded by Git and Docker.
- [ ] `.django_env.json`, `.ssh`, and database dumps are excluded from Docker context.
- [ ] Docker container runs as a non-root user.
- [ ] Gunicorn listens only on `127.0.0.1` with host networking.
- [ ] PostgreSQL remains inaccessible from the public Internet.
- [ ] `DEBUG` is false.
- [ ] `ALLOWED_HOSTS` contains only intended domains.
- [ ] Django proxy SSL settings are correct for Caddy.
- [ ] `manage.py check --deploy` is reviewed on every production release.
- [ ] Docker logs are size-rotated.
- [ ] Base images and locked dependencies are updated regularly.
- [ ] Database backups are automated and restore-tested.
- [ ] Caddy `/data` storage is backed up if Caddy is later containerized.
- [ ] `/ads.txt` returns `text/plain` and the correct publisher identifier.
- [ ] Privacy/CMP behavior is tested after proxy changes.

---

## 16. Monitoring and routine operations

### Application status

```bash
docker compose ps
docker compose logs --tail=200 web
docker stats --no-stream
```

### Caddy status

```bash
sudo systemctl status caddy --no-pager
sudo journalctl -u caddy --since '1 hour ago' --no-pager
sudo caddy validate --config /etc/caddy/Caddyfile
```

### Public smoke test

```bash
curl -fsS -o /dev/null -w 'home %{http_code} %{time_total}s\n' https://leginabroad.com/
curl -fsS -o /dev/null -w 'topics %{http_code} %{time_total}s\n' https://leginabroad.com/sections
curl -fsS https://leginabroad.com/ads.txt
```

### Database backup verification

At least periodically:

1. Create a fresh backup.
2. Copy it away from the VPS.
3. Restore it into a disposable PostgreSQL database.
4. Run a minimal Django query against the restored database.
5. Record the date and result.

An untested backup is not a proven recovery mechanism.

---

## 17. Final completion criteria

The migration is complete only when all items are true:

- [ ] Django runs from the Docker image, not the old virtual environment.
- [ ] Container restarts automatically after a VPS reboot.
- [ ] PostgreSQL data survives container rebuilds because it remains on the host.
- [ ] Caddy owns ports 80 and 443.
- [ ] Caddy obtains and renews valid TLS certificates.
- [ ] Nginx is stopped but its configuration backup is retained.
- [ ] GitHub Actions tests before deploying.
- [ ] Deployment waits for a healthy container.
- [ ] Rollback has been tested at least once.
- [ ] Home, topics, articles, search, admin, static files, and S3 media work.
- [ ] `/ads.txt` remains correct.
- [ ] Google CMP works in the EEA test flow.
- [ ] Logs are visible through Docker and `journalctl`.
- [ ] Database backups and restore procedures are documented and tested.

---

## 18. Recommended execution order summary

1. Back up Nginx, Gunicorn configuration, and PostgreSQL.
2. Refactor Django from branch/JSON secrets to environment variables.
3. Refactor logs to stdout and add `/healthz`.
4. Deploy those application changes through the current stack.
5. Add Dockerfile, `.dockerignore`, Compose, and environment template.
6. Validate Docker on port 8001 without touching production traffic.
7. Move production Gunicorn into Docker while keeping Nginx.
8. Observe several successful deployments.
9. Fix `www` DNS or deliberately omit `www`.
10. Install and validate Caddy.
11. Replace Nginx with Caddy during a controlled maintenance window.
12. Update GitHub Actions only after the manual procedure is proven.
13. Test rollback, backups, AdSense, CMP, and all critical URLs.

---

## 19. Official references

- Docker production Compose guidance:
  <https://docs.docker.com/compose/how-tos/production/>
- Docker build best practices:
  <https://docs.docker.com/build/building/best-practices/>
- Docker multi-stage builds:
  <https://docs.docker.com/build/building/multi-stage/>
- Caddy automatic HTTPS:
  <https://caddyserver.com/docs/automatic-https>
- Caddy reverse proxy quick start:
  <https://caddyserver.com/docs/quick-starts/reverse-proxy>
- Caddy production service guidance:
  <https://caddyserver.com/docs/running>
- Caddy configuration reloads:
  <https://caddyserver.com/docs/getting-started#reloading-config>
- Django deployment checklist:
  <https://docs.djangoproject.com/en/stable/howto/deployment/checklist/>
