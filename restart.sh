#!/bin/bash

# Initialize the variable for the -t flag
run_tests=false
# shellcheck disable=SC2034
run_collectstatic=false
venv_path="venv"

activate_venv() {
    source "$(pwd)/$1/bin/activate"
    echo "Virtual environment activated: $1"
    echo "The Python interpreter being used is: $(which python)"
    echo "The Python version: $(python --version)"
}

# Parse the arguments
while getopts "tcd" opt; do
  case $opt in
    t)
      run_tests=true
      ;;
    d)
      venv_path=$OPTARG
      ;;
    c)
      run_collectstatic=true
      ;;
    *)
      echo "Usage: $0 [-t] [-c] [-d <venv_path>]"
      exit 1
      ;;
  esac
done

# If the -t flag is passed, run tests
if [ "$run_tests" = true ]; then
  activate_venv "$venv_path"
  echo "Running tests..."
  # if error occur with rights, go to the postgres user:
  # sudo su postgres > psql > ALTER USER $POSTGRESQL_USER CREATEDB;
  python3 manage.py test || { echo "Tests failed! Aborting."; deactivate; }
fi

if [ "$run_collectstatic" = true ]; then
  activate_venv "$venv_path"
  echo "Running python3 manage.py collectstatic"
  python3 manage.py collectstatic || { echo "Collectstatic failed. Aborting."; deactivate; }
fi

echo "Reloading services."
sudo systemctl restart gunicorn
sudo systemctl daemon-reload  # reload the systemd manager configuration
sudo systemctl restart gunicorn.socket gunicorn.service
sudo nginx -t && sudo systemctl restart nginx
echo "current python run: $(which python3)"
echo "current python run: $(python3 --version)"