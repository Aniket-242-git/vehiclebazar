"""Models for visitor tracking and location analytics."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class DeviceType(models.TextChoices):
    DESKTOP = "desktop", "Desktop"
    MOBILE = "mobile", "Mobile"
    TABLET = "tablet", "Tablet"
    BOT = "bot", "Bot"
    UNKNOWN = "unknown", "Unknown"


class LocationStatus(models.TextChoices):
    GRANTED = "granted", "Enabled / Granted"
    DENIED = "denied", "Denied / Blocked"
    PROMPT_IGNORED = "prompt_ignored", "Prompt Ignored"
    UNSUPPORTED = "unsupported", "Not Supported"
    NOT_PROMPTED = "not_prompted", "Not Prompted"


class VisitorLog(models.Model):
    """Stores visit logs including device, timestamp, IP, and location (if enabled)."""

    visited_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Exact date and time of visit.",
    )
    session_key = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="Session identifier to correlate pageviews.",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Visitor IP address.",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Raw browser User-Agent string.",
    )

    # Device & Browser details
    device_type = models.CharField(
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.DESKTOP,
        db_index=True,
    )
    os = models.CharField(
        max_length=80,
        blank=True,
        help_text="Operating System (e.g. Windows 11, iOS 17, Android 14).",
    )
    browser = models.CharField(
        max_length=80,
        blank=True,
        help_text="Browser name (e.g. Chrome, Safari, Firefox).",
    )
    browser_version = models.CharField(
        max_length=40,
        blank=True,
    )
    screen_resolution = models.CharField(
        max_length=30,
        blank=True,
        help_text="Device display resolution (e.g. 1920x1080).",
    )
    language = models.CharField(
        max_length=30,
        blank=True,
        help_text="Browser language (e.g. en-US).",
    )

    # Navigation details
    page_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Page URL visited.",
    )
    referrer = models.CharField(
        max_length=500,
        blank=True,
        help_text="Referrer URL.",
    )

    # Location details
    location_enabled = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True if visitor granted geolocation permission.",
    )
    location_status = models.CharField(
        max_length=30,
        choices=LocationStatus.choices,
        default=LocationStatus.NOT_PROMPTED,
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="GPS accuracy in meters.",
    )
    city = models.CharField(
        max_length=120,
        blank=True,
    )
    state_region = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="State / Region",
    )
    country = models.CharField(
        max_length=120,
        blank=True,
    )
    postal_code = models.CharField(
        max_length=30,
        blank=True,
    )
    address = models.TextField(
        blank=True,
        help_text="Formatted address from reverse geocoding.",
    )

    # Optional authenticated user link
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="visit_logs",
    )

    class Meta:
        ordering = ["-visited_at"]
        verbose_name = "Visitor Log"
        verbose_name_plural = "Visitor Logs"
        indexes = [
            models.Index(fields=["-visited_at", "location_enabled"]),
            models.Index(fields=["device_type", "-visited_at"]),
        ]

    def __str__(self) -> str:
        loc = self.display_location if self.location_enabled else "No location"
        return f"[{self.visited_at:%Y-%m-%d %H:%M}] {self.device_type} - {loc} ({self.ip_address})"

    @property
    def has_location(self) -> bool:
        return bool(self.location_enabled and self.latitude is not None and self.longitude is not None)

    @property
    def google_maps_url(self) -> str | None:
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None

    @property
    def display_location(self) -> str:
        if not self.location_enabled:
            return "Location Not Enabled"
        parts = [p for p in [self.city, self.state_region, self.country] if p]
        if parts:
            return ", ".join(parts)
        if self.latitude is not None and self.longitude is not None:
            return f"{self.latitude:.4f}, {self.longitude:.4f}"
        return "Location Enabled (Coordinates Pending)"

    @property
    def device_icon(self) -> str:
        mapping = {
            DeviceType.MOBILE: "bi-phone",
            DeviceType.TABLET: "bi-tablet",
            DeviceType.DESKTOP: "bi-laptop",
            DeviceType.BOT: "bi-robot",
        }
        return mapping.get(self.device_type, "bi-display")
