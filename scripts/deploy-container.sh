#!/usr/bin/env bash
set -Eeuo pipefail

run_migrations=false
skip_build=false

usage() {
  cat <<'EOF'
Usage: bash scripts/deploy-container.sh [--migrate] [--skip-build]

Build and start the Django/Gunicorn container on 127.0.0.1:8000 without
changing Nginx or stopping the existing systemd Gunicorn service.

Options:
  --migrate      Run Django migrations before starting the new container.
  --skip-build   Reuse the image already present on the server.
  -h, --help     Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --migrate)
      run_migrations=true
      ;;
    --skip-build)
      skip_build=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

env_file="${DOCKER_ENV_FILE:-.env.docker}"
if [[ ! -f "$env_file" ]]; then
  echo "Missing $env_file. Copy .env.docker.example and add server values." >&2
  exit 1
fi

if [[ "$(stat -c '%a' "$env_file")" != "600" ]]; then
  echo "Refusing to use $env_file until its permissions are 600." >&2
  echo "Run: chmod 600 $env_file" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or is not on PATH." >&2
  exit 127
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker Engine is not available to the current user." >&2
  exit 1
fi

compose=(
  docker compose
  --env-file "$env_file"
  -f compose.yaml
  -f compose.production.yaml
)

mkdir -p static

if ! $skip_build; then
  echo "==> Building the locked application image"
  "${compose[@]}" build --pull
fi

echo "==> Checking Django configuration"
"${compose[@]}" run --rm --no-deps web python manage.py check --deploy

echo "==> Verifying that the container user can write collected static files"
if ! "${compose[@]}" run --rm --no-deps web test -w /app/static; then
  echo "The host static directory is not writable by container UID/GID 10001." >&2
  echo "One-time fix: sudo chown -R 10001:10001 '$project_root/static'" >&2
  exit 1
fi

if $run_migrations; then
  echo "==> Applying database migrations"
  "${compose[@]}" run --rm --no-deps web python manage.py migrate --noinput
else
  echo "==> Skipping migrations; pass --migrate when the release includes them"
fi

echo "==> Collecting static files"
"${compose[@]}" run --rm --no-deps web python manage.py collectstatic --noinput

echo "==> Starting the container without changing Nginx"
"${compose[@]}" up -d --remove-orphans

container_id="$("${compose[@]}" ps -q web)"
if [[ -z "$container_id" ]]; then
  echo "Compose did not return a web container ID." >&2
  "${compose[@]}" ps >&2
  exit 1
fi

echo "==> Waiting for Docker health status"
for _ in $(seq 1 30); do
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' "$container_id")"
  case "$health" in
    healthy)
      echo "Container is healthy on http://127.0.0.1:8000/healthz/"
      echo "Nginx and the old Gunicorn service have not been changed."
      exit 0
      ;;
    unhealthy)
      echo "Container became unhealthy." >&2
      "${compose[@]}" logs --tail=100 web >&2
      exit 1
      ;;
  esac
  sleep 2
done

echo "Timed out waiting for the container health check." >&2
"${compose[@]}" logs --tail=100 web >&2
exit 1
