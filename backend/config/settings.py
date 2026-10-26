from pathlib import Path
from datetime import timedelta
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(BOOKLEAF_DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / '.env.example')
DEV_SECRET_KEY = 'bookleaf-development-only-secret-key-do-not-use-in-production'
SECRET_KEY = env('SECRET_KEY', default=DEV_SECRET_KEY)
DEBUG = env('BOOKLEAF_DEBUG')
if not DEBUG and SECRET_KEY == DEV_SECRET_KEY:
    raise RuntimeError('SECRET_KEY must be set when DEBUG=False')
if not DEBUG and not env('DATABASE_URL', default=''):
    raise RuntimeError('DATABASE_URL is required when BOOKLEAF_DEBUG=False')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost','127.0.0.1'])
database_url = env('DATABASE_URL', default='').strip()
DATABASES = {'default': env.db('DATABASE_URL') if database_url else {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
}}
DATABASES['default']['CONN_MAX_AGE'] = 60
DATABASES['default']['CONN_HEALTH_CHECKS'] = True
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','corsheaders','rest_framework','rest_framework_simplejwt.token_blacklist','django_filters','drf_spectacular','accounts','books','tickets','ai_services','core']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','corsheaders.middleware.CorsMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF='config.urls'; TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='config.wsgi.application'; ASGI_APPLICATION='config.asgi.application'
AUTH_USER_MODEL='accounts.User'; LANGUAGE_CODE='en-us'; TIME_ZONE='Asia/Kolkata'; USE_I18N=True; USE_TZ=True
STATIC_URL='static/'; STATIC_ROOT=BASE_DIR/'staticfiles'; DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
STORAGES={'staticfiles':{'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')
SESSION_COOKIE_SECURE=not DEBUG
CSRF_COOKIE_SECURE=not DEBUG
SECURE_SSL_REDIRECT=not DEBUG
SECURE_HSTS_SECONDS=31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS=not DEBUG
CORS_ALLOWED_ORIGINS=env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:5173'])
REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES':['rest_framework_simplejwt.authentication.JWTAuthentication'],'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticated'],'DEFAULT_SCHEMA_CLASS':'drf_spectacular.openapi.AutoSchema','DEFAULT_PAGINATION_CLASS':'core.pagination.StandardPagination','PAGE_SIZE':15,'DEFAULT_THROTTLE_CLASSES':['rest_framework.throttling.AnonRateThrottle','rest_framework.throttling.UserRateThrottle'],'DEFAULT_THROTTLE_RATES':{'anon':'30/min','user':'120/min','ai':'10/hour'},'EXCEPTION_HANDLER':'core.exceptions.api_exception_handler'}
SIMPLE_JWT={'ACCESS_TOKEN_LIFETIME':timedelta(minutes=20),'REFRESH_TOKEN_LIFETIME':timedelta(days=1),'ROTATE_REFRESH_TOKENS':True,'BLACKLIST_AFTER_ROTATION':True}
SPECTACULAR_SETTINGS={'TITLE':'BookLeaf API','VERSION':'1.0.0'}
GEMINI_API_KEY=env('GEMINI_API_KEY',default=''); GEMINI_MODEL=env('GEMINI_MODEL',default='gemini-3.5-flash-lite')
GEMINI_TIMEOUT_MS=env.int('GEMINI_TIMEOUT_MS',default=60000)
