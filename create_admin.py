import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "the_system.settings")
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@test.com", "admin123")
    print("Superuser created: admin / admin123")
else:
    print("Superuser already exists")
