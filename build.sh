#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate

# Create superuser for Free tier (using environment variables)
# Create or update superuser for Free tier
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  echo "Setting up superuser..."
  python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); username='$DJANGO_SUPERUSER_USERNAME'; email='$DJANGO_SUPERUSER_EMAIL'; password='$DJANGO_SUPERUSER_PASSWORD'; user, created = User.objects.get_or_create(username=username, defaults={'email': email}); user.set_password(password); user.is_staff=True; user.is_superuser=True; user.save(); print('Superuser setup complete.')"
fi
