#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r backend/requirements.txt
python backend/manage.py collectstatic --no-input
python backend/manage.py migrate

# Load initial data only if database is fresh/empty (to avoid overwriting user data)
python backend/manage.py shell -c "from django.contrib.auth import get_user_model; import sys; sys.exit(0 if get_user_model().objects.count() == 0 else 1)" && python backend/manage.py loaddata backend/initial_data.json || echo "Database already initialized. Preserving existing data."
