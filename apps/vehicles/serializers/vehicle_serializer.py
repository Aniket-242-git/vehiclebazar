"""Vehicle serializers (list card, detail, write)."""
from __future__ import annotations

from datetime import date

from rest_framework import serializers

from apps.vehicles.models import FuelType, Transmission, Vehicle, VehicleStatus
from .vehicle_image_serializer import VehicleImageSerializer


class VehicleListSerializer(serializers.ModelSerializer):
    """Compact payload for listing cards / search results."""

    category = serializers.SlugRelatedField(slug_field="name", read_only=True)
    category_slug = serializers.SlugRelatedField(source="category", slug_field="slug", read_only=True)
    brand = serializers.SlugRelatedField(slug_field="name", read_only=True)
    fuel_display = serializers.CharField(source="get_fuel_type_display", read_only=True)
    transmission_display = serializers.CharField(source="get_transmission_display", read_only=True)
    effective_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id", "title", "slug", "category", "category_slug", "brand",
            "model_name", "manufacturing_year", "price", "offer_price",
            "effective_price", "has_discount", "fuel_type", "fuel_display",
            "transmission", "transmission_display", "km_driven", "location",
            "status", "is_featured", "thumbnail_url", "short_description",
            "created_at",
        ]

    def get_thumbnail_url(self, obj: Vehicle) -> str:
        request = self.context.get("request")
        img = obj.primary_image
        url = ""
        if img and img.image:
            url = img.image.url
        elif obj.cover_image:
            url = obj.cover_image.url
        return request.build_absolute_uri(url) if (request and url) else url

    def get_short_description(self, obj: Vehicle) -> str:
        text = (obj.description or "").strip()
        return (text[:140] + "…") if len(text) > 140 else text


class VehicleDetailSerializer(VehicleListSerializer):
    images = VehicleImageSerializer(many=True, read_only=True)
    features = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    ownership_display = serializers.CharField(source="get_ownership_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    age_years = serializers.IntegerField(read_only=True)

    class Meta(VehicleListSerializer.Meta):
        fields = VehicleListSerializer.Meta.fields + [
            "registration_year", "engine_cc", "color", "ownership",
            "ownership_display", "description", "features", "images",
            "status_display", "discount_amount", "age_years",
            "is_active", "updated_at",
        ]


class VehicleWriteSerializer(serializers.ModelSerializer):
    """Create/update payload used by admin APIs. Full validation server-side."""

    class Meta:
        model = Vehicle
        fields = [
            "category", "brand", "model_name", "title", "slug",
            "manufacturing_year", "registration_year", "price", "offer_price",
            "fuel_type", "transmission", "km_driven", "engine_cc", "color",
            "ownership", "location", "description", "status", "is_featured",
            "is_active", "cover_image", "features",
        ]

    def validate(self, attrs: dict) -> dict:
        mfg = attrs.get("manufacturing_year") or getattr(self.instance, "manufacturing_year", None)
        reg = attrs.get("registration_year", getattr(self.instance, "registration_year", None))
        price = attrs.get("price", getattr(self.instance, "price", None))
        offer = attrs.get("offer_price", getattr(self.instance, "offer_price", None))

        current_year = date.today().year
        if mfg and mfg > current_year:
            raise serializers.ValidationError(
                {"manufacturing_year": f"Manufacturing year cannot be in the future (> {current_year})."}
            )
        if reg:
            if reg > current_year:
                raise serializers.ValidationError({"registration_year": "Registration year cannot be in the future."})
            if mfg and reg < mfg:
                raise serializers.ValidationError(
                    {"registration_year": "Registration year cannot be before manufacturing year."}
                )
        if price is not None and offer is not None and offer >= price:
            raise serializers.ValidationError(
                {"offer_price": "Offer price must be lower than the regular price."}
            )
        return attrs

    def validate_fuel_type(self, value: str) -> str:
        if value not in FuelType.values:
            raise serializers.ValidationError(f"Invalid fuel type. Choose from: {', '.join(FuelType.values)}.")
        return value

    def validate_transmission(self, value: str) -> str:
        if value not in Transmission.values:
            raise serializers.ValidationError("Invalid transmission type.")
        return value

    def validate_status(self, value: str) -> str:
        if value not in VehicleStatus.values:
            raise serializers.ValidationError("Invalid vehicle status.")
        return value
