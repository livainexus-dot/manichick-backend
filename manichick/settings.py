import os
from pathlib import Path
from datetime import timedelta

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# En production, cette clé doit être secrète et dans une variable d'environnement
SECRET_KEY = 'manichick-secret-key-changer-en-production'

# ── Applications installées ──────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'suivi_poules', 
    # Dans INSTALLED_APPS, ajoute :
    'lots_poulets',

    # Bibliothèques tierces (third-party libraries)
    'rest_framework',        # Django REST Framework
    'rest_framework_simplejwt', # authentification JWT
    'corsheaders',           # autorise les appels depuis l'app mobile

    # Nos applications Manichick
    'capteurs',
    'actionneurs',
    'alertes',
    'utilisateurs',
    'finances',
]

MIDDLEWARE = [
    # corsheaders DOIT être en premier dans la liste
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'manichick.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'manichick.wsgi.application'

# ── Authentification JWT ─────────────────────────────────
REST_FRAMEWORK = {
    # Par défaut, toutes les routes nécessitent un token JWT valide
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# Durée de validité des tokens JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),  # token valide 12h
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),   # refresh valide 7 jours
    'ROTATE_REFRESH_TOKENS': True, # génère un nouveau refresh à chaque usage
}

# ── CORS — autorise l'app mobile à appeler l'API ────────
# En développement on autorise tout
CORS_ALLOW_ALL_ORIGINS = True

# Configuration détaillée de CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-csrftoken',
]

# ── Internationalisation ─────────────────────────────────
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Douala'  # fuseau horaire du Cameroun
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



AUTH_USER_MODEL = 'utilisateurs.Utilisateur'

# ── Railway / développement local ────────────────────────
# Railway injecte automatiquement DATABASE_URL.
# On l'utilise directement sans condition.
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URL_TEST')
RAILWAY_PUBLIC_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN')

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.railway.app',
]

if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)

extra_allowed_hosts = os.environ.get('ALLOWED_HOSTS')
if extra_allowed_hosts:
    ALLOWED_HOSTS += [
        host.strip()
        for host in extra_allowed_hosts.split(',')
        if host.strip()
    ]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'https://*.railway.app',
]

if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RAILWAY_PUBLIC_DOMAIN}')

if DATABASE_URL:
    # Mode production Railway — utilise DATABASE_URL
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'manichick-secret-2026')
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
        )
    }
    # WhiteNoise pour les fichiers statiques
    if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
        MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

else:
    # Mode développement local Kali Linux
    DEBUG = True
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'manichick_db',
            'USER': 'manichick_user',
            'PASSWORD': 'manichick2024',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
