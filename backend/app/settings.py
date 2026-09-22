import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret')
DEBUG = os.getenv('DJANGO_DEBUG', 'true') == 'true'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'rest_framework',
    'app.apps.users',
    'app.apps.properties',
    'app.apps.booking',
    'app.apps.contract',
    'app.apps.repair',
]

MIDDLEWARE = ['django.middleware.common.CommonMiddleware', 'app.middleware.request_log.RequestLogMiddleware']
ROOT_URLCONF = 'app.urls'
DATABASES = {'default': dj_database_url.config(default=os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3'))}
# SQLite 本地开发：写锁冲突时等待而不是立即报 database is locked（PostgreSQL 依靠行锁串行化）
if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    DATABASES['default']['OPTIONS'] = {'timeout': 20}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

USE_TZ = True
TIME_ZONE = 'Asia/Shanghai'
LANGUAGE_CODE = 'zh-hans'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
REST_FRAMEWORK = {'EXCEPTION_HANDLER': 'app.utils.exception_handler.standard_exception_handler'}
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
