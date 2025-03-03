#!/usr/bin/env bash

# Exit early if something goes wrong
set -e
export API_BASE_URL=http://api:8000
export DJANGO_SECRET_KEY="example"
export CASE_WORKER_ENVIRONMENT_KEY="example"
export DATABASE_URL=psql://postgres:postgres@localhost:5432/trade_remedies
export DJANGO_SETTINGS_MODULE="config.settings.staging"

# Add commands below to run inside the container after all the other buildpacks have been applied
cd trade_remedies_public
python manage.py compilescss
python manage.py collectstatic --noinput --ignore=*.scss
