"""Search service – dedicated entry point for vehicle search.

Wraps the repository so callers (views/APIs) never build Q objects inline.
Kept separate from VehicleService to respect SRP and make search testable in
isolation.
"""
from __future__ import annotations

from django.db.models import QuerySet

from apps.vehicles.models import Vehicle
from apps.vehicles.repositories import VehicleRepository


class VehicleSearchService:
    repository = VehicleRepository()

    @classmethod
    def search(cls, term: str, *, include_all_statuses: bool = False) -> QuerySet[Vehicle]:
        qs = (
            cls.repository.admin_queryset()
            if include_all_statuses
            else cls.repository.public_queryset()
        )
        qs = cls.repository.search(qs, term)
        return cls.repository.apply_sort(qs, "latest")

    @classmethod
    def suggestions(cls, term: str, limit: int = 5) -> list[str]:
        """Distinct titles for an autocomplete dropdown (DB-level DISTINCT)."""
        term = (term or "").strip()
        if not term:
            return []
        return list(
            cls.repository.public_queryset()
            .filter(title__icontains=term)
            .values_list("title", flat=True)
            .distinct()[:limit]
        )
