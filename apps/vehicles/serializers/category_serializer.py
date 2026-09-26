"""Category + Brand + Feature serializers."""
from rest_framework import serializers

from apps.vehicles.models import Brand, Category, Feature


class CategorySerializer(serializers.ModelSerializer):
    vehicle_count = serializers.IntegerField(read_only=True)  # annotated by view

    class Meta:
        model = Category
        fields = [
            "id", "name", "slug", "description", "image",
            "is_active", "vehicle_count", "created_at", "updated_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "is_active", "created_at", "updated_at"]
        read_only_fields = ["slug", "created_at", "updated_at"]


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ["id", "name", "slug", "icon", "is_active"]
        read_only_fields = ["slug"]
