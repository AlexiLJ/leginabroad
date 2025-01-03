# Bash Script for Restarting Django Project

This script automates common tasks for managing Django project, such as activating a virtual environment, running tests, collecting static files, and restarting services.

## Features

- Activate a virtual environment. If directory name is not passed with _-d parameter_, default is "venv"
- Run Django tests using `python manage.py test` when passed _-t flag_.
- Collect static files using `python manage.py collectstatic` when passed _-c flag_.
- Restart Gunicorn and Nginx services by default.

## Requirements

- A virtual environment for the Django project.
- Gunicorn and Nginx installed and configured for your project.
- PostgreSQL user with appropriate permissions (if needed).

## Usage

Run the script with the following options:

```bash
./script.sh [-t] [-c] [-d <venv_path>]
