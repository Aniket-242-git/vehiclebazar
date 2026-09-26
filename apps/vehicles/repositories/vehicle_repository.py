"""Repository layer: all Vehicle queryset construction lives here.

Keeping query building in one place makes views/services thin and the queries
easy to test and optimise (select_related / prefetch_related / only).
"""
from __future__ import annotations

import django.db.models as m
from django.db.models import QuerySet

from apps.vehicles.models import Vehicle, VehicleStatus


class VehicleRepository:
    """Data-access object for Vehicle listings (SRP: DB access only)."""

    model = Vehicle

    # Columns needed by listing cards – avoids SELECT * on wide rows.
    LIST_FIELDS = (
        "id", "title", "slug", "price", "offer_price", "location",
        "fuel_type", "transmission", "km_driven", "manufacturing_year",
        "status", "is_featured", "is_active", "created_at", "description",
        "category_id", "brand_id",
    )

    def base_queryset(self) -> QuerySet[Vehicle]:
        return (
            self.model.objects
            .select_related("category", "brand")
            .prefetch_related("images", "features")
        )

    def public_queryset(self) -> QuerySet[Vehicle]:
        """Only listings a visitor may see (active; sold items hidden by default)."""
        return self.base_queryset().filter(is_active=True).exclude(
            status=VehicleStatus.INACTIVE
        )

    def featured(self, limit: int = 8) -> QuerySet[Vehicle]:
        return (
            self.public_queryset()
            .filter(status=VehicleStatus.AVAILABLE, is_featured=True)
            .order_by("-created_at")[:limit]
        )

    def latest(self, limit: int = 8) -> QuerySet[Vehicle]:
        return (
            self.public_queryset()
            .filter(status=VehicleStatus.AVAILABLE)
            .order_by("-created_at")[:limit]
        )

    def by_slug(self, slug: str) -> QuerySet[Vehicle]:
        return self.base_queryset().filter(slug=slug)

    def admin_queryset(self) -> QuerySet[Vehicle]:
        return self.base_queryset()

    # ------------------------------------------------------------------
    # Search + filtering helpers (all database-level, combinable)
    # ------------------------------------------------------------------
    def search(self, qs: QuerySet[Vehicle], term: str) -> QuerySet[Vehicle]:
        term = (term or "").strip()
        if not term:
            return qs
        return qs.filter(
            m.Q(title__icontains=term)
            | m.Q(model_name__icontains=term)
            | m.Q(brand__name__icontains=term)
            | m.Q(category__name__icontains=term)
            | m.Q(location__icontains=term)
        )

    def apply_filters(
        self,
        qs: QuerySet[Vehicle],
        *,
        category: str | None = None,
        brand: str | None = None,
        min_price=None,
        max_price=None,
        year_from: int | None = None,
        fuel_type: str | None = None,
        transmission: str | None = None,
        location: str | None = None,
        status: str | None = None,
    ) -> QuerySet[Vehicle]:
        if category:
            qs = qs.filter(category__slug=category)
        if brand:
            qs = qs.filter(brand__slug=brand)
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)
        if year_from is not None:
            qs = qs.filter(manufacturing_year__gte=year_from)
        if fuel_type:
            qs = qs.filter(fuel_type=fuel_type)
        if transmission:
            qs = qs.filter(transmission=transmission)
        if location:
            qs = qs.filter(location__icontains=location)
        if status:
            qs = qs.filter(status=status)
        return qs

    SORT_FIELDS = {
        "latest": "-created_at",
        "oldest": "created_at",
        "price_asc": "price",
        "price_desc": "-price",
        "year_desc": "-manufacturing_year",
        "year_asc": "manufacturing_year",
    }

    def apply_sort(self, qs: QuerySet[Vehicle], sort_key: str) -> QuerySet[Vehicle]:
        """Database-level ordering; defaults to newest first."""
        return qs.order_by(self.SORT_FIELDS.get(sort_key, "-created_at"))
