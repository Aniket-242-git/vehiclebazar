"""Production settings – shared hosting / cPanel.

Everything sensitive is read from environment variables set in the control
panel (or a .env file outside the web root). Supports MySQL (cPanel default)
and PostgreSQL via DB_ENGINE.
"""
from .base import *  # noqa: F401,F403

DEBUG = False

if not SECRET_KEY:  # noqa: F405
    raise RuntimeError(
        "DJANGO_SECRET_KEY environment variable is required in production."
    )

# ------------------------------------------------------------------
# Database (MySQL or PostgreSQL, chosen with DB_ENGINE)
# ------------------------------------------------------------------
DATABASES["default"] = {  # noqa: F405
    "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.mysql"),  # noqa: F405
    "NAME": os.environ["DB_NAME"],
    "USER": os.environ["DB_USER"],
    "PASSWORD": os.environ["DB_PASSWORD"],
    "HOST": os.getenv("DB_HOST", "localhost"),
    "PORT": os.getenv("DB_PORT", ""),
    "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
}

if DATABASES["default"]["ENGINE"].endswith("mysql"):  # noqa: F405
    DATABASES["default"]["OPTIONS"] = {  # noqa: F405
        "charset": "utf8mb4",
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
    }

# ------------------------------------------------------------------
# HTTPS / security hardening
# ------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # JS needs it for API POSTs (same-origin)

# ------------------------------------------------------------------
# Email – real backend can be enabled later without touching views.
# Default keeps the console-style service; switch EMAIL_BACKEND_SERVICE
# and configure SMTP credentials when ready.
# ------------------------------------------------------------------
if os.getenv("EMAIL_BACKEND_SERVICE", "console") == "smtp":  # noqa: F405
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["EMAIL_HOST"]
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)  # noqa: F405
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# ------------------------------------------------------------------
# Caching – per-process local memory cache (no Redis dependency, which
# cannot run on typical cPanel shared hosting).
# ------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "vehicle-marketplace",
    }
}

# Log to file on shared hosts where stdout is not visible.
LOGGING["handlers"]["file"] = {  # noqa: F405
    "class": "logging.handlers.RotatingFileHandler",
    "filename": BASE_DIR / "logs" / "django.log",  # noqa: F405
    "maxBytes": 2_000_000,
    "backupCount": 5,
    "formatter": "verbose",  # noqa: F405
}
LOGGING["loggers"]["apps"]["handlers"].append("file")  # noqa: F405
