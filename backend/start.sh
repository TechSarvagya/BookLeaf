#!/usr/bin/env sh
set -eu
python backend/manage.py migrate --noinput
python backend/manage.py seed_bookleaf_data --file 'FULLSTACK-SAMPLEDATA (1) (1) (1).json' --allow-production-demo
exec gunicorn --chdir backend config.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 2 --timeout 120
