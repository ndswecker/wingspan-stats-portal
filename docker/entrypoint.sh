#!/bin/sh

set -e

python manage.py migrate --noinput
python manage.py register_achievements
python manage.py collectstatic --noinput

exec "$@"