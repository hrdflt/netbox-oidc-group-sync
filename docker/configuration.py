# NetBox configuration used by the Docker test environment only.
# Not suitable for any real deployment.
import os

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'netbox'),
        'USER': os.environ.get('DB_USER', 'netbox'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'netbox'),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': int(os.environ.get('DB_PORT', 5432)),
    }
}

REDIS = {
    'tasks': {
        'HOST': os.environ.get('REDIS_HOST', 'redis'),
        'PORT': int(os.environ.get('REDIS_PORT', 6379)),
        'DATABASE': 0,
        'SSL': False,
    },
    'caching': {
        'HOST': os.environ.get('REDIS_HOST', 'redis'),
        'PORT': int(os.environ.get('REDIS_PORT', 6379)),
        'DATABASE': 1,
        'SSL': False,
    },
}

SECRET_KEY = 'docker-test-secret-key-not-for-production-0123456789abcdef'
API_TOKEN_PEPPERS = {1: 'docker-test-pepper-not-for-production-0123456789abcdef'}

PLUGINS = ['netbox_oidc_group_sync']

# Allows `manage.py makemigrations --dry-run` for checking migration drift
DEVELOPER = True
