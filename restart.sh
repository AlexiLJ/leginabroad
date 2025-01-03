#!/bin/bash

# Initialize the variable for the -t flag
run_tests=false
# shellcheck disable=SC2034
run_collectstatic=false
venv_path="venv"

activate_venv() {
  if [ -d "$1" ]; then
    echo "$(pwd)/$1/bin/activate"
    source "$(pwd)/$1/bin/activate"
    echo "Virtual environment activated: $1"
    echo "The Python interpreter being used is: $(which python)"

  else
    echo "Error: Virtual environment not found at $1"
    exit 1
  fi
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
  # activate venv
  activate_venv "$venv_path"
  echo "Running tests..."
  python manage.py test || { echo "Tests failed! Aborting."; deactivate; exit 1; }
  deactivate
