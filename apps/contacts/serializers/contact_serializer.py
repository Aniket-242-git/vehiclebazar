"""Contact form serializer.

Used two ways:
1. DRF ModelSerializer for the JSON API (POST /api/contact/).
2. As a plain validation form for server-rendered pages via
   ``ContactRequestFormSerializer`` alias + ``as_form()`` helper in views.

Validation is fully server-side: name, email format, phone pattern, message.
"""
from __future__ import annotations

from rest_framework import serializers

from apps.contacts.models import PHONE_RE, ContactRequest
from apps.vehicles.models import Vehicle


class ContactRequestSerializer(serializers.ModelSerializer):
    vehicle_title = serializers.CharField(source="vehicle.title", read_only=True)
    vehicle_slug = serializers.CharField(source="vehicle.slug", read_only=True)

    class Meta:
        model = ContactRequest
        fields = [
            "id", "name", "email", "phone", "message",
            "vehicle", "vehicle_title", "vehicle_slug",
            "status", "admin_notes", "created_at",
        ]
        read_only_fields = ["id", "status", "admin_notes", "created_at"]

    def validate_phone(self, value: str) -> str:
        value = (value or "").strip()
        if not PHONE_RE.match(value):
            raise serializers.ValidationError(
                "Enter a valid phone number (7–18 digits; optional + and spaces)."
            )
        return value

    def validate_name(self, value: str) -> str:
        value = (value or "").strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value

    def validate_message(self, value: str) -> str:
        return (value or "").strip()

    def validate_vehicle(self, value: Vehicle | None) -> Vehicle | None:
        if value is not None and not value.is_active:
            raise serializers.ValidationError("This vehicle listing is no longer available.")
        return value


# Alias used by server-rendered contact views/forms.
ContactRequestFormSerializer = ContactRequestSerializer
