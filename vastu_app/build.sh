#!/usr/bin/env bash
pip install -r requirements.txt
python vastu_app/manage.py collectstatic --no-input
python vastu_app/manage.py migrate --run-syncdb