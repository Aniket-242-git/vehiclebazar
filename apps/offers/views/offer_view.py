"""Offer API views: public active-offer endpoint + staff CRUD."""
from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from apps.offers.models import Offer
from apps.offers.serializers import OfferSerializer
from apps.offers.services import OfferService


class OfferViewSet(viewsets.ModelViewSet):
    """Staff-only CRUD at /api/admin/offers/ (+ public GET /api/offers/active/)."""

    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "pk"

    def get_permissions(self):
        if self.action == "active":
            return []  # public read
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="active", permission_classes=[],
            authentication_classes=[])
    def active(self, request):
        """The single offer that should be shown as a modal right now (or null)."""
        offer = OfferService.get_modal_offer()
        data = OfferSerializer(offer, context={"request": request}).data
        return Response(data)

    @action(detail=True, methods=["post"], url_path="toggle-active")
    def toggle_active(self, request, pk=None):
        offer = self.get_object()
        offer.is_active = not offer.is_active
        offer.save(update_fields=["is_active", "updated_at"])
        return Response(OfferSerializer(offer).data, status=status.HTTP_200_OK)
