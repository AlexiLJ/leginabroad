#!/usr/bin/env bash
set -Eeuo pipefail

# Flags
run_tests=false
run_collectstatic=false
python_version=""
env_path=""

usage() {
  cat <<EOF
Usage: $0 [-t] [-c] [-p <python_version>] [-e <env_path>]
  -t                    Run Django tests
  -c                    Run "collectstatic"
  -p <python_version>   Use a specific Python (e.g. 3.12, 3.13)
  -e <env_path>         Use a specific virtualenv directory (default: .venv)
                        (uv will honor VIRTUAL_ENV if set)
  -h                    Show this help
Examples:
  $0 -t
  $0 -c -p 3.13
  $0 -t -c -e venv -p 3.12
EOF
}

while getopts ":tcp:e:h" opt; do
  case "$opt" in
    t) run_tests=true ;;
    c) run_collectstatic=true ;;
    p) python_version="$OPTARG" ;;
    e) env_path="$OPTARG" ;;
    h) usage; exit 0 ;;
    \?) echo "Unknown option: -$OPTARG" >&2; usage; exit 1 ;;
    :)  echo "Option -$OPTARG requires an argument." >&2; usage; exit 1 ;;
  esac
done

# Ensure uv is available
#if ! command -v uv >/dev/null 2>&1; then
#  echo "Error: 'uv' is not installed or not on PATH."
#  echo "See: https://docs.astral.sh/uv/"
#  exit 1
#fi

# Make uv use a specific env directory if requested
if [[ -n "$env_path" ]]; then
  # uv respects VIRTUAL_ENV when set
  export VIRTUAL_ENV="$(realpath "$env_path")"
fi

prepare_env() {
  echo "==> Syncing environment with uv..."
  if [[ -n "$python_version" ]]; then
    echo "    Using Python $python_version"
    uv sync --python "$python_version"
  else
    uv sync
  fi
  echo "==> Interpreter in use:"
  uv run python -c 'import sys,platform; print(sys.executable); print(platform.python_version())'
}

# Run tasks
if $run_tests || $run_collectstatic; then
  prepare_env
fi

if $run_tests; then
  echo "==> Running tests..."
  # If your DB user needs CREATEDB for Django's test DB, grant it separately.
  if ! uv run python manage.py test; then
    echo "Tests failed! Aborting."
    exit 1
  fi
fi

if $run_collectstatic; then
  echo "==> Running collectstatic..."
  if ! uv run python manage.py collectstatic --noinput; then
    echo "collectstatic failed! Aborting."
    exit 1
  fi
fi

echo "==> Reloading services..."
# Reload systemd and restart gunicorn units
sudo systemctl daemon-reload
sudo systemctl restart gunicorn.socket gunicorn.service

# Test and (re)load nginx
if sudo nginx -t; then
  sudo systemctl reload nginx
else
  echo "nginx config test failed; NOT reloading nginx."
  exit 1
fi

echo "Done."
