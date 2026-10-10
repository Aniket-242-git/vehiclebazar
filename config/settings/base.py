"""
Base (shared) Django settings for the Second-Hand Vehicle Marketplace project.

Settings are split per-environment:
    config.settings.base         - shared configuration (this file)
    config.settings.development  - local development (DEBUG=True, SQLite ok)
    config.settings.production   - live hosting / cPanel (DEBUG=False, MySQL/Postgres)

All secrets come from environment variables (see .env.example). Nothing secret is
hard-coded here.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env if present (harmless when the file does not exist).
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean from the environment safely."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    """Read a comma-separated list from the environment."""
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# ------------------------------------------------------------------
# Security – NEVER hard-code SECRET_KEY. Provide it via environment.
# ------------------------------------------------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")

DEBUG = env_bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000",
)

# ------------------------------------------------------------------
# Application definition
# ------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party (pure-python, safe on cPanel shared hosting)
    "rest_framework",
    "django_filters",
    # Local apps
    "apps.accounts",
    "apps.vehicles",
    "apps.contacts",
    "apps.offers",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Site-wide context: brand name + currently active offer modal
                "apps.offers.context_processors.active_offer",
                "apps.core_context.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ------------------------------------------------------------------
# Database – configured in development.py / production.py.
# Default fallback keeps `manage.py` usable before an env module is chosen.
# ------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": os.getenv(
            "DB_ENGINE", "django.db.backends.sqlite3"
        ),
        "NAME": os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
    }
}

# ------------------------------------------------------------------
# Password validation
# ------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------
# Static & media files
# On cPanel run `python manage.py collectstatic` and point the domain's
# static/media URLs at STATIC_ROOT / MEDIA_ROOT via the control panel.
# ------------------------------------------------------------------
STATIC_URL = os.getenv("STATIC_URL", "/static/")
STATIC_ROOT = BASE_DIR / os.getenv("STATIC_ROOT_REL", "staticfiles")
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------
# Authentication redirects
# ------------------------------------------------------------------
LOGIN_URL = "admin_login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"

# ------------------------------------------------------------------
# Django REST Framework
# Public read APIs are unauthenticated; write APIs require staff session auth.
# ------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.vehicles.services.pagination.VehiclePageNumberPagination",
    "PAGE_SIZE": 12,
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
}

# ------------------------------------------------------------------
# Pagination limits (configurable business rules)
# ------------------------------------------------------------------
PAGINATION_DEFAULT_PAGE_SIZE = int(os.getenv("PAGINATION_DEFAULT_PAGE_SIZE", "12"))
PAGINATION_MAX_PAGE_SIZE = int(os.getenv("PAGINATION_MAX_PAGE_SIZE", "48"))

# ------------------------------------------------------------------
# Offers – business rule for which single offer the modal displays.
#   "priority"     : highest priority active offer wins (recommended default)
#   "display_order": first active offer ordered by display_order then newest
# ------------------------------------------------------------------
OFFER_DISPLAY_STRATEGY = os.getenv("OFFER_DISPLAY_STRATEGY", "priority")

# ------------------------------------------------------------------
# File upload validation (secure uploads)
# ------------------------------------------------------------------
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
# Magic-number signatures we accept for uploaded images.
ALLOWED_IMAGE_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}
# Homepage banner slides may carry bigger files (animated GIFs / short videos).
MAX_BANNER_UPLOAD_SIZE_MB = int(os.getenv("MAX_BANNER_UPLOAD_SIZE_MB", "25"))

# ------------------------------------------------------------------
# Email service architecture
# The contact view depends on an *interface*, and the concrete backend is
# selected by EMAIL_BACKEND_SERVICE. Swap console -> smtp/sendgrid/SES later
# without touching views. See apps/contacts/services/email_service.py
# ------------------------------------------------------------------
EMAIL_BACKEND_SERVICE = os.getenv("EMAIL_BACKEND_SERVICE", "console")
CONSOLE_EMAIL_RECIPIENTS = env_list("CONSOLE_EMAIL_RECIPIENTS", "admin@example.com")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@vehiclemarket.local")
EMAIL_SUBJECT_PREFIX = "[VehicleMarket] "
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ------------------------------------------------------------------
# Logging (use logging, not print(), for application logs)
# ------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}
