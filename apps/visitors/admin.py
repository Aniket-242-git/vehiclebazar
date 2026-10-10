"""Django admin configuration for VisitorLog."""
from django.contrib import admin
from django.utils.html import format_html

from apps.visitors.models import VisitorLog


@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = (
        "visited_at",
        "location_status_badge",
        "location_display",
        "device_display",
        "ip_address",
        "page_url",
        "google_maps_link",
    )
    list_filter = (
        "location_enabled",
        "location_status",
        "device_type",
        "browser",
        "os",
        "visited_at",
    )
    search_fields = (
        "ip_address",
        "city",
        "state_region",
        "country",
        "page_url",
        "user_agent",
        "postal_code",
    )
    readonly_fields = (
        "visited_at",
        "session_key",
        "ip_address",
        "user_agent",
        "device_type",
        "os",
        "browser",
        "browser_version",
        "screen_resolution",
        "language",
        "page_url",
        "referrer",
        "location_enabled",
        "location_status",
        "latitude",
        "longitude",
        "accuracy",
        "city",
        "state_region",
        "country",
        "postal_code",
        "address",
        "user",
    )
    date_hierarchy = "visited_at"
    ordering = ("-visited_at",)

    def has_add_permission(self, request):
        return False  # Logs are automatically created via visitor requests

    @admin.display(description="Location Status")
    def location_status_badge(self, obj):
        if obj.location_enabled:
            return format_html('<span style="color:#198754;font-weight:bold;">📍 Enabled</span>')
        return format_html('<span style="color:#6c757d;">❌ Not Enabled</span>')

    @admin.display(description="Location")
    def location_display(self, obj):
        return obj.display_location

    @admin.display(description="Device")
    def device_display(self, obj):
        return f"{obj.get_device_type_display()} · {obj.browser} ({obj.os})"

    @admin.display(description="Maps")
    def google_maps_link(self, obj):
        url = obj.google_maps_url
        if url:
            return format_html('<a href="{}" target="_blank">🗺️ View Map</a>', url)
        return "-"
