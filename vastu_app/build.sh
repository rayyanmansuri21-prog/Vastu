#!/usr/bin/env bash
pip install -r requirements.txt
python vastu_app/manage.py collectstatic --no-input
python vastu_app/manage.py migrate --run-syncdb

python vastu_app/manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'gohelhetvi47@gmail.com', 'Hetvi@1807')
    print('Superuser created!')
else:
    print('Superuser already exists.')
"