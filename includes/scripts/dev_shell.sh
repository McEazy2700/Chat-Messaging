echo "Collecting staticfiles"
python manage.py collectstatic --no-input --clear

echo "Migrating Database"
python manage.py migrate --no-input

echo "Staring Dev Server"
python manage.py runserver 0.0.0.0:${BACKEND_PORT}
