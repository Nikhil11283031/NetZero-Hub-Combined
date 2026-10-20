"""Django settings for the Solar Panel Installation microservice (ORG-001).

This service owns its own database (solar requests, events and payments) and shares nothing with the other
NetZero Hub services except their public APIs. Sign-in is handled by the group's Django backend, which holds
the user accounts: solar checks each request's token against its /api/v1/auth/me/ endpoint (see solar/auth.py),
the same way the EPA services do.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-solar-secret-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,solar-service")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:3000,http://localhost:8003")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "solar",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# The solar service's own database. In Docker this is the separate "solar-db" MySQL container;
# without SOLAR_MYSQL_HOST it falls back to a local SQLite file (solar.sqlite3) for development.
if env("SOLAR_MYSQL_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "HOST": env("SOLAR_MYSQL_HOST"),
            "PORT": env("SOLAR_MYSQL_PORT", "3306"),
            "NAME": env("SOLAR_MYSQL_DATABASE", "solar"),
            "USER": env("SOLAR_MYSQL_USER", "solar"),
            "PASSWORD": env("SOLAR_MYSQL_PASSWORD", ""),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "solar.sqlite3"}}

LANGUAGE_CODE = "en-au"
TIME_ZONE = env("TIME_ZONE", "Australia/Sydney")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/solar-static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Where the group accounts live (the Django backend). Solar asks it who a token belongs to, like the EPA
# services do. No caching by default, so signing out takes effect straight away.
NZ_AUTH_URL = env("NZ_AUTH_URL", "http://localhost:8000/api/v1/auth/me/")
AUTH_CACHE_SECONDS = int(env("AUTH_CACHE_SECONDS", "0"))

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["solar.auth.RemoteTokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "solar.errors.exception_handler",
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Solar Panel Installation API (ORG-001)",
    "DESCRIPTION": (
        "NetZero Hub microservice for solar installation requests: free site assessment booking, quote, "
        "payments (deposit, full, balance, refunds) and the installer's status updates."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {"SolarRequestStatusEnum": "solar.models.SolarRequest.Status"},
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
