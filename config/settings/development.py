"""Development settings – local machine only. Never use in production."""
from .base import *  # noqa: F401,F403

DEBUG = True

# A development key is fine here; production reads DJANGO_SECRET_KEY from env.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me-in-production")  # noqa: F405

ALLOWED_HOSTS = ["*"]

# SQLite is the zero-config default for local development.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Print emails to the console during development.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# More permissive logging while developing.
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
