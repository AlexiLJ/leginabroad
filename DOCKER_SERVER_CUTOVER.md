# Docker milestone 2: run the container behind the existing Nginx

This milestone starts Django and Gunicorn in Docker on `127.0.0.1:8000`, verifies
the container, and then changes only the Nginx application upstream. PostgreSQL,
TLS, static-file routing, and the current systemd Gunicorn service remain
available during the initial observation period.

Do not combine this cutover with the Caddy migration or the GitHub Actions
rewrite.

## 1. Back up the working server

Before changing the VPS:

```bash
sudo nginx -T > "$HOME/nginx-before-docker.txt"
sudo cp -a /etc/nginx "$HOME/nginx-before-docker"
sudo systemctl cat gunicorn.socket gunicorn.service > "$HOME/gunicorn-before-docker.txt"
pg_dump --format=custom --file="$HOME/leginabroad-before-docker.dump" DATABASE_NAME
pg_restore --list "$HOME/leginabroad-before-docker.dump" >/dev/null
```

Copy the database dump and Nginx backup away from the VPS before continuing.

## 2. Prepare runtime configuration

From the repository root on the VPS:

```bash
cp .env.docker.example .env.docker
chmod 600 .env.docker
```

Fill in the real values. On the VPS, use:

```dotenv
DJANGO_DEBUG=false
DJANGO_SECURE_SSL_REDIRECT=true
DJANGO_CSRF_COOKIE_SECURE=true
DJANGO_SESSION_COOKIE_SECURE=true
DJANGO_ALLOWED_HOSTS=leginabroad.com,www.leginabroad.com,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://leginabroad.com,https://www.leginabroad.com
HOST_NAME=/var/run/postgresql
```

PostgreSQL remains bound to host loopback. The production Compose overlay mounts
`/var/run/postgresql` into the web container, and an absolute Django database
host selects that Unix socket instead of TCP.

Find the active client-authentication file:

```bash
sudo -u postgres psql -Atqc "SHOW hba_file;"
sudo -u postgres psql -Atqc "SHOW unix_socket_directories;"
```

Back up the reported `pg_hba.conf`, then add this rule before a broader
`local all all peer` rule:

```text
local   DATABASE_NAME   DATABASE_USER   scram-sha-256
```

Use the real database and role names from `.env.docker`. Reload PostgreSQL and
test the socket interactively without putting the password in shell history:

```bash
sudo systemctl reload postgresql
psql --host=/var/run/postgresql --username=DATABASE_USER \
  --dbname=DATABASE_NAME --password --command='SELECT 1;'
```

Do not change `listen_addresses` and do not publish port 5432.

## 3. Prepare the static directory

The production Compose overlay bind-mounts the existing repository `static`
directory so Nginx can continue serving it from the same location.

```bash
mkdir -p static
sudo chown -R 10001:10001 static
sudo chmod -R u=rwX,go=rX static
```

Confirm the Nginx worker can traverse every parent directory leading to the
static directory. Keep the existing Nginx `/static/` location unchanged.

## 4. Build and start without cutting over traffic

```bash
bash scripts/deploy-container.sh
```

Use `--migrate` only when the release contains reviewed migrations:

```bash
bash scripts/deploy-container.sh --migrate
```

The script performs these actions:

1. Refuses environment files with permissions other than `600`.
2. Builds the locked image.
3. Runs `manage.py check --deploy`.
4. Verifies static-directory permissions.
5. Optionally applies migrations.
6. Collects static files.
7. Starts the service on `127.0.0.1:8000`.
8. Waits for Docker to report a healthy container.

It does not modify Nginx or stop the old Gunicorn service.

## 5. Test the container directly

```bash
curl --fail --show-error http://127.0.0.1:8000/healthz/
curl --fail --show-error \
  --header 'Host: leginabroad.com' \
  --header 'X-Forwarded-Proto: https' \
  http://127.0.0.1:8000/
docker compose --env-file .env.docker \
  -f compose.yaml -f compose.production.yaml ps
docker compose --env-file .env.docker \
  -f compose.yaml -f compose.production.yaml logs --tail=100 web
```

The homepage request should return HTML without a redirect loop. Check an
article, search, admin login, CSS, and an S3-hosted image before changing Nginx.

## 6. Cut Nginx over to Docker

Save a copy of the active site file immediately before editing it:

```bash
sudo cp /etc/nginx/sites-available/leginabroad \
  /etc/nginx/sites-available/leginabroad.pre-docker
```

In the HTTPS server block, replace only the current application proxy location
or Unix-socket `proxy_pass` with the block from:

```text
deploy/nginx/leginabroad-container-location.conf
```

Keep the existing server names, certificate directives, HTTP-to-HTTPS redirect,
and static-file location. Then validate and reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 7. Verify public traffic

```bash
curl --fail --show-error --head https://leginabroad.com/
curl --fail --show-error https://leginabroad.com/healthz/
curl --fail --show-error https://leginabroad.com/ads.txt
```

In a browser, test desktop and mobile navigation, several articles, pagination,
search, the admin, static styling, and uploaded images. Watch both logs:

```bash
sudo journalctl -u nginx -f
docker compose --env-file .env.docker \
  -f compose.yaml -f compose.production.yaml logs -f web
```

Keep the old systemd Gunicorn service available for at least one observation
period. Do not disable it during the first cutover.

## 8. Roll back to systemd Gunicorn

Restore Nginx before stopping the container:

```bash
sudo cp /etc/nginx/sites-available/leginabroad.pre-docker \
  /etc/nginx/sites-available/leginabroad
sudo systemctl restart gunicorn.socket gunicorn.service
sudo nginx -t
sudo systemctl reload nginx
```

Verify the public site, then stop Docker:

```bash
docker compose --env-file .env.docker \
  -f compose.yaml -f compose.production.yaml down
```

Database migrations are not automatically reversed. If a release includes a
schema change, prepare and test its database rollback separately before the
cutover.

## Completion criteria

- Docker reports the `web` service as healthy.
- Nginx proxies application traffic to `127.0.0.1:8000`.
- Static assets still come from the existing host path.
- Search, articles, admin, S3 images, `ads.txt`, and mobile layouts work.
- Logs contain no repeating application or proxy errors.
- The systemd Gunicorn rollback remains tested and available.

Only after this milestone is stable should the GitHub Actions deployment be
changed to call the container deploy script.
