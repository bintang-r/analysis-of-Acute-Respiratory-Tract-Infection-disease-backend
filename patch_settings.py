import os
from pathlib import Path
import re

base_dir = Path(r"C:\laragon\www\main-analysis\analisis-penyakit-ispa-backend")

# Patch apps.py
apps = ["authentication", "symptoms", "diseases", "rules", "consultations", "experts"]
for app in apps:
    apps_py = base_dir / "apps" / app / "apps.py"
    if apps_py.exists():
        content = apps_py.read_text()
        content = content.replace(f"name = '{app}'", f"name = 'apps.{app}'")
        apps_py.write_text(content)

# Patch settings.py
settings_py = base_dir / "backend" / "settings.py"
content = settings_py.read_text()

# Append apps and settings
installed_apps_addition = """
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'apps.authentication',
    'apps.symptoms',
    'apps.diseases',
    'apps.rules',
    'apps.consultations',
    'apps.experts',
"""
content = content.replace("'django.contrib.staticfiles',", "'django.contrib.staticfiles'," + installed_apps_addition)

# Add middleware
middleware_addition = """
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
"""
content = content.replace("'django.middleware.security.SecurityMiddleware',", middleware_addition)

# Modify Database
db_config = """DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ispa_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}"""
db_start = content.find("DATABASES = {")
db_end = content.find("}", content.find("}", db_start) + 1) + 1
content = content[:db_start] + db_config + content[db_end:]

# Add CORS, DRF, JWT settings
extra_settings = """

AUTH_USER_MODEL = 'authentication.User'

CORS_ALLOW_ALL_ORIGINS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}
"""
content += extra_settings
settings_py.write_text(content)
print("Settings patched successfully.")
