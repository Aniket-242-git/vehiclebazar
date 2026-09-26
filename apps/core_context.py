"""Site-wide template context helpers."""
from django.conf import settings


def site_settings(request):
    """Brand name etc. available in every template."""
    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "VehicleBazaar"),
        "SITE_TAGLINE": getattr(settings, "SITE_TAGLINE", "Quality second-hand vehicles, verified."),
    }
