#!/bin/bash

# Initialize the variable for the -t flag
run_tests=false
venv_path="venv"

# Parse the arguments
while getopts "td:" opt; do
  case $opt in
    t)
      run_tests=true
      ;;
    d)
      venv_path=$OPTARG
      ;;
    *)
      echo "Usage: $0 [-t] [-d <venv_path>]"
      exit 1
      ;;
  esac
done

# If the -t flag is passed, run tests
if [ "$run_tests" = true ]; then
  # activate venv
  if [ -d "$venv_path" ]; then
    # shellcheck disable=SC1090
    source "$(pwd)/$venv_path/bin/activate"
    echo "Virtual environment activated: $venv_path"
  else
    echo "Error: Virtual environment not found at $venv_path"
    exit 1
  fi
  echo "Running tests..."
  python3 manage.py test || { echo "Tests failed! Aborting."; deactivate; exit 1; }
fi

echo "Reloading services."
sudo systemctl restart gunicorn
sudo systemctl daemon-reload  # reload the systemd manager configuration
sudo systemctl restart gunicorn.socket gunicorn.service
sudo nginx -t && sudo systemctl restart nginx
