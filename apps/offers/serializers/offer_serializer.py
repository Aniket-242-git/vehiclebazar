"""Offer serializer with date validation (server-side, mandatory)."""
from __future__ import annotations

from rest_framework import serializers

from apps.offers.models import Offer


class OfferSerializer(serializers.ModelSerializer):
    is_live = serializers.BooleanField(read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id", "title", "slug", "description", "banner",
            "button_text", "button_url", "start_date", "end_date",
            "is_active", "priority", "display_order", "is_live",
            "created_at", "updated_at",
        ]
        read_only_fields = ["slug", "is_live", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        start = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end = attrs.get("end_date") or getattr(self.instance, "end_date", None)
        if start and end and end <= start:
            raise serializers.ValidationError({"end_date": "End date must be after the start date."})
        return attrs
