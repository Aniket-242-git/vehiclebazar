"""VehicleImage serializer."""
from rest_framework import serializers

from apps.vehicles.models import VehicleImage


class VehicleImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = VehicleImage
        fields = ["id", "image", "url", "alt_text", "order", "is_primary", "created_at"]
        read_only_fields = ["created_at"]

    def get_url(self, obj: VehicleImage) -> str:
        request = self.context.get("request")
        if not obj.image:
            return ""
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url
