#!/usr/bin/env bash
set -o errexit
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py create_admin_if_needed
