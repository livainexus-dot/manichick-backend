#!/bin/bash
set -e
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python create_admin.py
