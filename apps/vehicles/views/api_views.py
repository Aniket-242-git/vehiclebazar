"""DRF API views for vehicles, categories, brands and features.

Read endpoints are public (active listings only); write endpoints require an
authenticated staff user (see ``IsStaffAdmin`` permission).  All queryset
construction goes through the repository/service layer so views stay thin.
"""
from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.vehicles.models import Brand, Category, Feature, Vehicle
from apps.vehicles.serializers import (
    BrandSerializer,
    CategorySerializer,
    FeatureSerializer,
    VehicleDetailSerializer,
    VehicleListSerializer,
    VehicleWriteSerializer,
)
from apps.vehicles.services.pagination import VehiclePageNumberPagination
from apps.vehicles.services.permissions import IsStaffAdmin
from apps.vehicles.services.vehicle_service import VehicleService


class VehicleViewSet(viewsets.ModelViewSet):
    """CRUD for vehicles.

    GET    /api/vehicles/            paginated, searchable, filterable list
    GET    /api/vehicles/{id}/       full detail (gallery, features, specs)
    POST   /api/vehicles/            staff only
    PUT    /api/vehicles/{id}/       staff only
    PATCH  /api/vehicles/{id}/       staff only (e.g. mark as sold)
    DELETE /api/vehicles/{id}/       staff only
    """

    lookup_field = "id"
    pagination_class = VehiclePageNumberPagination

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated() & IsStaffAdmin()]

    def get_serializer_class(self):
        if self.action == "list":
            return VehicleListSerializer
        if self.action == "retrieve":
            return VehicleDetailSerializer
        return VehicleWriteSerializer

    def get_queryset(self):
        # Admin writes operate on the full table; public reads on active only.
        if self.request.user.is_staff:
            return VehicleService.repository.base_queryset()
        params = VehicleService.parse_params(self.request.query_params)
        return VehicleService.build_queryset(params)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated & IsStaffAdmin])
    def mark_sold(self, request, pk=None):
        """Convenience endpoint: PATCH-like action to flip status to 'sold'."""
        vehicle = self.get_object()
        vehicle.status = "sold"
        vehicle.save(update_fields=["status", "updated_at"])
        return Response(VehicleDetailSerializer(vehicle, context=self.get_serializer_context()).data)


class CategoryViewSet(viewsets.ModelViewSet):
    """GET /api/categories/ is public; writes are staff-only."""

    serializer_class = CategorySerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [IsAuthenticated() & IsStaffAdmin()]

    def get_queryset(self):
        qs = Category.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        return qs.order_by("name")


class BrandViewSet(viewsets.ModelViewSet):
    """GET /api/brands/ is public; writes are staff-only."""

    serializer_class = BrandSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [IsAuthenticated() & IsStaffAdmin()]

    def get_queryset(self):
        qs = Brand.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        return qs.order_by("name")


class FeatureViewSet(viewsets.ModelViewSet):
    """Reusable feature catalogue (AC, ABS, Airbags ...). Staff-writable."""

    serializer_class = FeatureSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [IsAuthenticated() & IsStaffAdmin()]

    def get_queryset(self):
        return Feature.objects.order_by("name")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.vehicles.exists():
            return Response(
                {"detail": "Feature is used by existing vehicles; unlink it first."},
                status=status.HTTP_409_CONFLICT,
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
